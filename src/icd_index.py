"""
ICD-10 index: hybrid BM25 + vector search, fused with RRF.

Built once at startup from data/icd10cm_data.csv. Queried per diagnosis
at runtime. Returns top-3 candidates or NO_CONFIDENT_MATCH.

Design rules:
- The LLM never sees the code table. It sees only the top-3 candidates
  for one diagnosis.
- BM25 catches exact terms. Vector search catches paraphrases. RRF
  fuses the two ranked lists.
- Confidence is measured primarily by TOKEN OVERLAP between the query
  and the top candidate's description. Cosine similarity is kept as a
  secondary check with a permissive threshold.

Why token overlap and not cosine:
    Diagnostic on 2026-10-13 showed that bge-small-en produces embeddings
    in a narrow angular cone for short clinical phrases. Every query —
    common or rare — returns top_cosine between 0.85 and 0.89. Examples:
        "ligature mark"       -> Y652 (misadventures)      top_cos 0.861
        "hyoid bone fracture" -> S92211K (cuboid fracture) top_cos 0.878
        "hypertension"        -> I152 (secondary HTN)      top_cos 0.883
    A cosine gate at 0.55 never fires. The gate must use a signal that
    actually discriminates: whether the query's meaningful tokens appear
    in the candidate's description.

Run:
    python -m src.icd_index --build     # build the indexes once
"""

import json
import logging
import pickle
import re
import sys
import time
from pathlib import Path

import chromadb
import pandas as pd
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


ICD_CSV = Path("data/icd10cm_data.csv")
BM25_PATH = Path("bm25_index.pkl")
CHROMA_DIR = Path("chroma_db")
CHROMA_COLLECTION = "icd10"
EMBED_MODEL = "BAAI/bge-small-en"

RRF_K = 60
TOP_N = 3

# Primary gate: fraction of meaningful query tokens that must appear in
# the top candidate's cleaned description. 0.50 means at least half of
# the query's non-stopword tokens must match. Tune on dev set.
MIN_TOKEN_OVERLAP = 0.50

# Secondary gate: cosine similarity floor. Set low because bge-small-en
# cosines are uniformly high for clinical phrases. This only rejects
# truly unrelated queries, not semantically-narrow misses.
MIN_COSINE_FLOOR = 0.50

# Common English stopwords. Very short list — clinical text has few of
# these, and we want to keep "no", "not", "left", "right" etc. since
# they matter in ICD descriptions.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "in", "into", "is", "it", "its", "of", "on", "or",
    "that", "the", "their", "this", "to", "was", "were", "will",
    "with", "about", "other", "specific", "long", "description",
    "header", "code", "unspecified",
}


_bm25: BM25Okapi | None = None
_bm25_codes: list[str] = []
_bm25_descs: list[str] = []
_embedder: SentenceTransformer | None = None
_chroma_collection = None


def _clean_description(raw: str) -> str:
    """Strip the CSV's wrapper text from a description.

    Raw form:
        "Header: J308 - Other allergic rhinitis | Specific long
         description about this code: Allergic rhinitis, unspecified"
    Cleaned form:
        "Allergic rhinitis, unspecified"

    If the wrapper pattern is not found, the original string is
    returned stripped. This makes the function safe for description
    formats that change upstream.
    """
    if not isinstance(raw, str):
        return ""
    marker = "Specific long description about this code:"
    if marker in raw:
        return raw.split(marker, 1)[1].strip()
    # Some rows use a slightly different marker; try a generic split.
    if "description about this code:" in raw:
        return raw.split("description about this code:", 1)[1].strip()
    return raw.strip()


def _meaningful_tokens(text: str) -> set[str]:
    """Lowercase, split on non-alphanumeric, drop stopwords and 1-char tokens."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {t for t in tokens if len(t) > 1 and t not in STOPWORDS}


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenizer for BM25."""
    return text.lower().split()


def build_index():
    """Build the BM25 and ChromaDB indexes from the ICD-10 CSV. Run once."""
    print(f"Reading {ICD_CSV}...")
    df = pd.read_csv(ICD_CSV)
    codes = df["code"].astype(str).tolist()
    raw_descs = df["description"].astype(str).tolist()
    descs = [_clean_description(d) for d in raw_descs]
    print(f"Loaded {len(codes)} ICD codes (descriptions cleaned)")

    # --- BM25 ---
    print("Tokenizing for BM25...")
    tokenized = [_tokenize(d) for d in descs]
    bm25 = BM25Okapi(tokenized)

    print(f"Saving BM25 index to {BM25_PATH}...")
    BM25_PATH.write_bytes(pickle.dumps({
        "bm25": bm25,
        "codes": codes,
        "descs": descs,
    }))

    # --- ChromaDB ---
    print(f"Loading embedding model {EMBED_MODEL}...")
    embedder = SentenceTransformer(EMBED_MODEL)

    print("Encoding descriptions (this takes a few minutes)...")
    embeddings = embedder.encode(
        descs,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    print(f"Writing to ChromaDB at {CHROMA_DIR}...")
    CHROMA_DIR.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Delete collection if it exists (fresh rebuild)
    try:
        client.delete_collection(CHROMA_COLLECTION)
    except Exception:
        pass

    collection = client.create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    # ChromaDB has a max batch size (~5,461). Add in chunks of 5,000.
    CHUNK = 5000
    emb_list = embeddings.tolist()
    total = len(codes)
    for start in range(0, total, CHUNK):
        end = min(start + CHUNK, total)
        collection.add(
            ids=codes[start:end],
            documents=descs[start:end],
            embeddings=emb_list[start:end],
        )
        print(f"  Added {end}/{total}")

    print(f"Done. Collection has {collection.count()} entries.")


def load_index():
    """Load the BM25 and ChromaDB indexes into memory. Called once per process.

    If the on-disk BM25 index was built with the old (wrapper-included)
    descriptions, this function re-cleans the descriptions at load time
    so the token-overlap gate works. To take full advantage of the
    cleaned descriptions, rebuild with:
        python -m src.icd_index --build
    """
    global _bm25, _bm25_codes, _bm25_descs, _embedder, _chroma_collection

    t_total = time.perf_counter()
    logger.info("Starting ICD-10 index loading...")

    if not BM25_PATH.exists():
        err_msg = f"{BM25_PATH} not found. Run: python -m src.icd_index --build"
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)

    # 1. BM25 pickle loading
    t_bm25 = time.perf_counter()
    logger.info("[1/3] Loading BM25 index from '%s'...", BM25_PATH)
    try:
        data = pickle.loads(BM25_PATH.read_bytes())
        _bm25 = data["bm25"]
        _bm25_codes = data["codes"]
        raw_descs = data["descs"]
        # Re-clean in case the pickle was built before the wrapper strip.
        _bm25_descs = [_clean_description(d) if "description about this code:" in d
                       else d for d in raw_descs]
        bm25_elapsed = time.perf_counter() - t_bm25
        logger.info(
            "[1/3 DONE] BM25 index loaded successfully in %.3fs (%d codes).",
            bm25_elapsed,
            len(_bm25_codes),
        )
    except Exception:
        bm25_elapsed = time.perf_counter() - t_bm25
        logger.exception(
            "[1/3 FAILED] Failed to load BM25 index after %.3fs.",
            bm25_elapsed,
        )
        raise

    # 2. ChromaDB initialization and collection loading
    t_chroma = time.perf_counter()
    logger.info(
        "[2/3] Initializing ChromaDB persistent client at '%s' (collection: '%s')...",
        CHROMA_DIR,
        CHROMA_COLLECTION,
    )
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _chroma_collection = client.get_collection(CHROMA_COLLECTION)
        chroma_elapsed = time.perf_counter() - t_chroma
        logger.info(
            "[2/3 DONE] ChromaDB collection '%s' loaded successfully in %.3fs.",
            CHROMA_COLLECTION,
            chroma_elapsed,
        )
    except Exception:
        chroma_elapsed = time.perf_counter() - t_chroma
        logger.exception(
            "[2/3 FAILED] Failed to load ChromaDB collection '%s' after %.3fs.",
            CHROMA_COLLECTION,
            chroma_elapsed,
        )
        raise

    # 3. SentenceTransformer initialization
    t_embed = time.perf_counter()
    logger.info(
        "[3/3] Initializing SentenceTransformer model '%s'...",
        EMBED_MODEL,
    )
    try:
        _embedder = SentenceTransformer(EMBED_MODEL)
        embed_elapsed = time.perf_counter() - t_embed
        logger.info(
            "[3/3 DONE] SentenceTransformer model '%s' loaded in %.3fs.",
            EMBED_MODEL,
            embed_elapsed,
        )
    except Exception:
        embed_elapsed = time.perf_counter() - t_embed
        logger.exception(
            "[3/3 FAILED] Failed to initialize SentenceTransformer model '%s' after %.3fs.",
            EMBED_MODEL,
            embed_elapsed,
        )
        raise

    total_elapsed = time.perf_counter() - t_total
    logger.info(
        "ICD index ready (%d codes). Total load time: %.3fs.",
        len(_bm25_codes),
        total_elapsed,
    )


def _bm25_search(query: str, k: int = 20) -> list[tuple[int, float]]:
    """Return (index, score) pairs from BM25, sorted by score descending."""
    assert _bm25 is not None
    scores = _bm25.get_scores(_tokenize(query))
    top_idx = scores.argsort()[::-1][:k]
    return [(int(i), float(scores[i])) for i in top_idx]


def _vector_search(query: str, k: int = 20) -> list[tuple[int, float]]:
    """Return (index, cosine_similarity) pairs from ChromaDB, sorted by similarity."""
    assert _chroma_collection is not None
    assert _embedder is not None

    query_emb = _embedder.encode([query], normalize_embeddings=True).tolist()
    results = _chroma_collection.query(
        query_embeddings=query_emb,
        n_results=k,
        include=["distances"],
    )

    ids = results["ids"][0]
    distances = results["distances"][0]

    # Chroma cosine distance = 1 - cosine_similarity
    out: list[tuple[int, float]] = []
    for code, dist in zip(ids, distances):
        try:
            idx = _bm25_codes.index(code)
        except ValueError:
            continue
        similarity = 1.0 - dist
        out.append((idx, similarity))
    return out


def _rrf_fuse(
    bm25_results: list[tuple[int, float]],
    vector_results: list[tuple[int, float]],
) -> list[tuple[int, float]]:
    """Fuse two ranked lists via Reciprocal Rank Fusion. Returns (index, rrf_score)."""
    scores: dict[int, float] = {}

    for rank, (idx, _) in enumerate(bm25_results):
        scores[idx] = scores.get(idx, 0.0) + 1.0 / (RRF_K + rank + 1)

    for rank, (idx, _) in enumerate(vector_results):
        scores[idx] = scores.get(idx, 0.0) + 1.0 / (RRF_K + rank + 1)

    # Sort by fused score descending
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def _confidence_check(query: str, top_idx: int, top_cosine: float) -> tuple[bool, str]:
    """Decide whether the top candidate is a confident match.

    Returns (is_confident, reason_if_not).

    Two gates, both must pass:
      - Cosine floor: top_cosine >= MIN_COSINE_FLOOR (permissive; rejects
        only truly unrelated queries)
      - Token overlap: >= MIN_TOKEN_OVERLAP fraction of the query's
        meaningful tokens appear in the top candidate's cleaned
        description. This is the discriminating gate.
    """
    if top_cosine < MIN_COSINE_FLOOR:
        return False, f"cosine {top_cosine:.3f} < floor {MIN_COSINE_FLOOR}"

    q_tokens = _meaningful_tokens(query)
    if not q_tokens:
        return False, "query had no meaningful tokens"

    cand_desc = _bm25_descs[top_idx]
    c_tokens = _meaningful_tokens(cand_desc)
    if not c_tokens:
        return False, "top candidate had no meaningful tokens"

    overlap = len(q_tokens & c_tokens) / len(q_tokens)
    if overlap < MIN_TOKEN_OVERLAP:
        return False, (f"token overlap {overlap:.2f} < {MIN_TOKEN_OVERLAP} "
                       f"(query tokens {sorted(q_tokens)}; "
                       f"candidate tokens {sorted(c_tokens)[:8]}...)")
    return True, ""


def icd_lookup(diagnosis_name: str) -> list[dict] | str:
    """
    Look up ICD-10 candidates for a diagnosis name.

    Returns a list of up to 3 {code, description, score, top_cosine}
    dicts, or the string "NO_CONFIDENT_MATCH" when the top candidate
    is not a confident match. Confidence is determined by:
      - the top vector-search cosine must clear MIN_COSINE_FLOOR, and
      - at least MIN_TOKEN_OVERLAP of the query's meaningful tokens
        must appear in the top candidate's cleaned description.
    """
    if not diagnosis_name or not diagnosis_name.strip():
        return "NO_CONFIDENT_MATCH"

    bm25_results = _bm25_search(diagnosis_name)
    vector_results = _vector_search(diagnosis_name)

    if not vector_results:
        return "NO_CONFIDENT_MATCH"

    top_idx, top_cosine = vector_results[0]
    confident, reason = _confidence_check(diagnosis_name, top_idx, top_cosine)
    if not confident:
        return "NO_CONFIDENT_MATCH"

    fused = _rrf_fuse(bm25_results, vector_results)

    out: list[dict] = []
    for idx, score in fused[:TOP_N]:
        out.append({
            "code": _bm25_codes[idx],
            "description": _bm25_descs[idx],
            "score": round(score, 5),
        })

    # Also record the top cosine for downstream debugging
    if out:
        out[0]["top_cosine"] = round(top_cosine, 4)

    return out


def _cli():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m src.icd_index --build")
        print("  python -m src.icd_index 'type 2 diabetes'")
        sys.exit(1)

    if sys.argv[1] == "--build":
        build_index()
        return

    # Otherwise treat argv[1] as a query string
    load_index()
    query = " ".join(sys.argv[1:])
    print(f"\nQuery: {query!r}")
    result = icd_lookup(query)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _cli()