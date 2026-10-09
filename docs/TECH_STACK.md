# Tech Stack Justification

Every choice below is accompanied by *why* and *what was rejected*.

---

## LLMs

| Role | Choice | Why | Rejected |
|---|---|---|---|
| Extractor | Qwen 3.8 27B | Free tier; fast; reliable JSON mode | GPT-4 (paid, not allowed); local Mistral (weaker extraction quality) |
| Verifier | Gemini 3.5 Flash Lite | **Different model family** from Qwen → errors are decorrelated; free tier; stable under free-tier load | Gemini 3.8 Flash: 503-prone on free tier; same model for both: shared blind spots |

**Independence rationale:** the SOW's central requirement is that verification is an *independent* check. Using two different model families (Alibaba's Qwen vs Google's Gemini) reduces the chance that both models make the same mistake on the same input. This is defended with evidence from the eval — the baseline single-model run vs the two-model pipeline.

**Model stability:** Gemini 3.8 Flash was the initial choice but returned HTTP 503 ("model experiencing high demand") on the majority of calls under free-tier load. Gemini 3.5 Flash Lite is a different version in the same family — same API, same JSON mode, lower traffic tier, markedly more stable. Independence from Qwen is preserved.

**Context window:**
- Qwen 3.8 27B: 128K token context window
- Gemini 3.5 Flash Lite: 1M token context window

Both windows are far larger than the per-note budget (~5K tokens for the extractor, ~6K for the verifier). The system never hits the window limit even on long notes. Long notes are handled by section-by-section extraction, not by truncation.

---

## Data layer

| Role | Choice | Why | Rejected |
|---|---|---|---|
| Vector store | ChromaDB | Local, persistent, simple API, metadata filtering | FAISS (no metadata filtering); Pinecone (paid, cloud dependency) |
| Keyword search | rank_bm25 | Tiny dependency; exact-term matching; pure Python | Elasticsearch (overkill for 74K rows); SQLite FTS5 (viable but requires preprocessing) |
| Embeddings | bge-small-en (CPU) | No quota use; offline; reproducible; ~130 MB model | Google text-embedding-004 (uses quota; network dependency) |
| Hybrid fusion | Reciprocal Rank Fusion (k=60) | Merges two ranked lists without needing comparable scores | Weighted sum of scores (requires calibration); top-N of each (loses information) |

---

## Backend

| Role | Choice | Why | Rejected |
|---|---|---|---|
| Web framework | FastAPI | Lightweight; async support; automatic OpenAPI docs; Pydantic native | Flask (sync-only by default); Django (too heavy for a single-user MVP) |
| Structured output | Pydantic v2 | Explicit schemas; testable; integrates with FastAPI; validates on parse | dataclasses (no runtime validation); manual dict checking (error-prone) |
| Orchestration | Plain Python functions | The SOW requires explaining every line. Frameworks hide the loop. | LangChain / LangGraph (opaque; harder to defend); CrewAI (same problem) |

---

## Guardrails

| Role | Choice | Why | Rejected |
|---|---|---|---|
| PII masking | Regex + spaCy (local) | SOW requires masking to run locally, never through an external API | Cloud DLP (violates SOW); Microsoft Presidio (heavier, similar capability, adds dependency) |
| Injection defence | Delimiter wrapping + system instruction | Simple, testable, no external dependency | LLM-based injection filter (circular — would need another model call before masking) |
| Offset preservation | Same-length masking (replace with same character count) | Keeps every downstream offset valid without a remapping layer | Variable-length masks + offset map (added complexity; drift risk) |

---

## Frontend

| Role | Choice | Why | Rejected |
|---|---|---|---|
| UI | HTML/CSS/JS served by FastAPI | Offset-based highlighting is straightforward with DOM ranges; no build step | React (build tooling overhead for a single-user MVP); Streamlit (less precise offset control; harder to render overlapping highlights) |

---

## Observability

| Role | Choice | Why | Rejected |
|---|---|---|---|
| Tracing | Structured JSON per note | Human-readable; viewable in the reviewer UI; cheap | OpenTelemetry (overkill); LangSmith (cloud dependency) |
| Evaluation | pytest + one-command harness | Deterministic; reproducible; standard Python tooling | Notebook-based eval (not reproducible) |

---

## Testing

| Role | Choice | Why | Rejected |
|---|---|---|---|
| Framework | pytest | Standard; fixtures; parameterisation | unittest (verbose) |
| Model mocking | Disk cache keyed by (model + prompt + schema version) | Reproducible; zero quota on re-run | Live-only testing (burns free tier quota; non-deterministic) |

---

## Free-tier constraints

Every choice above must run on free-tier services:

- **Groq free tier:** Qwen 3.8 27B, ~30 RPM, ~8K TPM, ~1000 RPD
- **Google AI Studio free tier:** Gemini 3.5 Flash Lite, rate-limited but stable
- **ChromaDB + bge-small-en + rank_bm25:** all local, no quota
- **Cache layer:** every model call cached to disk, so evaluation costs zero quota on re-run

If a free-tier model is deprecated or rate-limited, the fallback is listed in the ARCHITECTURE.md risk table. Model availability has already been observed to change (Gemini 3.8 Flash became unstable; Llama 3.3 70B was not available on this account).