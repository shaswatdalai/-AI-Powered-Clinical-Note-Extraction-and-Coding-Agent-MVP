"""
ICD-10 index: hybrid BM25 + vector search, fused with RRF.

Built once at startup from data/icd10cm_data.csv. Queried per diagnosis
at runtime. Returns top-3 candidates or NO_CONFIDENT_MATCH.

Design rules:
- The LLM never sees the code table. It sees only the top-3 candidates
  for one diagnosis.
- BM25 catches exact terms. Vector search catches paraphrases. RRF
  fuses the two ranked lists.
- Confidence is measured on the top candidate's cosine similarity, not
  on the raw RRF score (RRF scores are rank-based and tiny).

Run:
    python -m src.icd_index --build     # build the indexes once
"""

import json
import pickle
import sys
from pathlib import Path

import chromadb
import pandas as pd
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


ICD_CSV = Path("data/icd10cm_data.csv")
BM25_PATH = Path("bm25_index.pkl")
CHROMA_DIR = Path("chroma_db")
CHROMA_COLLECTION = "icd10"
EMBED_MODEL = "BAAI/bge-small-en"

RRF_K = 60
TOP_N = 3
MIN_COSINE_CONFIDENCE = 0.55   # tune on dev set


_bm25: BM25Okapi | None = None
_bm25_codes: list[str] = []
_bm25_descs: list[str] = []
_embedder: SentenceTransformer | None = None
_chroma_collection = None


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenizer for BM25."""
    return text.lower().split()


def build_index():
    """Build the BM25 and ChromaDB indexes from the ICD-10 CSV. Run once."""
    print(f"Reading {ICD_CSV}...")
    df = pd.read_csv(ICD_CSV)
    codes = df["code"].astype(str).tolist()
    descs = df["description"].astype(str).tolist()
    print(f"Loaded {len(codes)} ICD codes")

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
    """Load the BM25 and ChromaDB indexes into memory. Called once per process."""
    global _bm25, _bm25_codes, _bm25_descs, _embedder, _chroma_collection

    if not BM25_PATH.exists():
        raise FileNotFoundError(
            f"{BM25_PATH} not found. Run: python -m src.icd_index --build"
        )

    print("Loading BM25 index...")
    data = pickle.loads(BM25_PATH.read_bytes())
    _bm25 = data["bm25"]
    _bm25_codes = data["codes"]
    _bm25_descs = data["descs"]

    print("Loading ChromaDB...")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    _chroma_collection = client.get_collection(CHROMA_COLLECTION)

    print("Loading embedding model...")
    _embedder = SentenceTransformer(EMBED_MODEL)

    print(f"ICD index ready ({len(_bm25_codes)} codes).")


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


def icd_lookup(diagnosis_name: str) -> list[dict] | str:
    """
    Look up ICD-10 candidates for a diagnosis name.

    Returns a list of up to 3 {code, description, score} dicts, or the
    string "NO_CONFIDENT_MATCH" when the top candidate's cosine similarity
    falls below the threshold.
    """
    if not diagnosis_name or not diagnosis_name.strip():
        return "NO_CONFIDENT_MATCH"

    bm25_results = _bm25_search(diagnosis_name)
    vector_results = _vector_search(diagnosis_name)

    if not vector_results:
        return "NO_CONFIDENT_MATCH"

    # Confidence gate: top vector result's cosine similarity must clear threshold
    top_cosine = vector_results[0][1]
    if top_cosine < MIN_COSINE_CONFIDENCE:
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