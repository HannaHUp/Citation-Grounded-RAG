<!-- GSD:project-start source:PROJECT.md -->
## Project

**Citation-Grounded-RAG**

A Vincent-AI-style legal-analysis MVP for the law industry. Upload a contract or
litigation complaint; an LLM extracts findings (risks, claims, obligations) and
grounds every finding to an exact, verifiable source span — with a deterministic
verify guard that flags any finding whose quote can't be matched back to the
source. The target audience is technical reviewers evaluating legal-AI
competence: it showcases grounded analysis where every generated claim links to
a real source.

**Core Value:** Grounding + verify guard IS the product: every generated claim links to a
verifiable real source, and an explicit faithfulness guard *measures and shows*
whether each claim is actually supported. This is the entire moat over plain
ChatGPT. If this works, everything else is presentation.

### Constraints

- **Tech stack**: Backend Python + FastAPI. Front-end React/Vite (light). LLM = Claude API with structured tool-output for forced-schema findings.
- **Tech stack**: No retrieval until Slice 3 — corpus doesn't exist before then. As built, Slice 3 uses TF-IDF cosine over a JSONL corpus (no vector DB; see "Slice 3 RAG: Retrieval (as built)").
- **Dependencies**: Legal corpus sourced from CourtListener's free API (a few hundred US authorities, not a billion docs).
- **Scope**: MVP demo, not production — no auth/accounts/DB until a second user exists.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12+ | Backend runtime | 3.12 is current stable; FastAPI requires 3.10+; 3.13 available but 3.12 has wider ecosystem support |
| FastAPI | 0.138.1 | API framework | Standard Python async API framework; auto-generates OpenAPI docs; Pydantic v2 built-in for request/response schema validation |
| Uvicorn | 0.49.0 | ASGI server | FastAPI's standard dev/prod server; `--reload` for dev |
| anthropic SDK | 0.112.0 | Claude API client | Official SDK; handles tool-use loop, `tool_choice`, and `strict` mode schema validation |
| pdfplumber | 0.11.10 | PDF extraction with char offsets | See detailed comparison below — winner for offset fidelity |
| python-docx | 1.2.0 | DOCX extraction | Only option for DOCX with paragraph-level offsets; maintained |
| React | 18.x | Frontend | Stated constraint; 18 is stable, 19 RC has breaking changes not worth chasing for MVP |
| Vite | 5.x | Frontend build tool | Fastest dev cycle for React; standard pairing |
### Supporting Libraries (Slice 1–2)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | v2 (bundled with FastAPI) | Request/response models, finding schema | Always; v2 is ~10x faster than v1, FastAPI 0.100+ uses v2 |
| python-multipart | 0.0.x | File upload parsing in FastAPI | Required for `UploadFile` endpoints; add at scaffold time |
| pytest | latest | Backend tests | For the verify-guard unit test; nothing else needs a test framework |
### Supporting Libraries (Slice 3 — RAG) — AS BUILT
> **The implemented RAG stack diverged from the original recommendation below.** We
> ship **JSONL + TF-IDF cosine**, not chromadb + sentence-transformers embeddings.
> See "Slice 3 RAG: Retrieval (as built)" for the what and the why.

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scikit-learn | 1.8.0 | TF-IDF vectorizer + cosine similarity | Retrieval scoring over the local corpus; a hand-rolled stdlib TF-IDF cosine is used as a fallback if scikit-learn is absent |
| (stdlib) `json` / `.jsonl` | — | Corpus + checkpoint storage | One `AuthorityRecord` per line in `corpus.jsonl`; `ingest_state.json` for checkpoint/resume. No vector DB. |
| (stdlib) `urllib.request` | — | HTTP for CourtListener ingestion | Injectable `fetch_json` so tests can stub the API; httpx was not needed at this scale |

> **Original recommendation (NOT built — kept for context):** `sentence-transformers`
> 5.6.0 (`all-MiniLM-L6-v2` embeddings) + `chromadb` 1.5.9 in-process vector store.
## PDF/DOCX Extraction: Char-Offset Comparison
### Comparison: offset preservation
| Library | Char offsets | How | Quality | Weight |
|---------|-------------|-----|---------|--------|
| **pdfplumber** | YES — per-character | `.chars` gives every char with `x0/y0/doctop`; reconstruct running offset by iterating chars in order | Excellent for text-layer PDFs; handles multi-column poorly | Light (`pdfminer.six` + `pypdfium2`) |
| **PyMuPDF (fitz)** | YES — per-character | `extractRAWDICT()` gives char bboxes; `extractWORDS()` for word-level | Faster than pdfplumber; better multi-column; strong OCR integration path | ~12 MB wheel (ships with MuPDF binary) |
| **python-docx** | PARTIAL — paragraph/run level | No char-level offsets; you get runs (`Run.text`) and must accumulate byte offsets yourself | Fine for DOCX; paragraphs map cleanly to offset accumulation | Light |
| **unstructured** | NO — loses offsets | Returns `Element` objects with no char-level position tracking; designed for chunking not offset grounding | Handles many formats but offset fidelity is explicitly not its goal | Heavy (200+ MB with deps) |
### Winner: pdfplumber for PDF, python-docx for DOCX, skip unstructured entirely
# PDF: pdfplumber
# DOCX: python-docx
# start_offset = position before paragraph was appended
## Claude API: Forced Structured Output
| Model | API ID | Input $/MTok | Output $/MTok | Notes |
|-------|--------|-------------|--------------|-------|
| Haiku 4.5 | `claude-haiku-4-5-20251001` | $1 | $5 | Default for MVP |
| Sonnet 4.6 | `claude-sonnet-4-6` | $3 | $15 | Upgrade if ⚠ rate too high |
| Opus 4.8 | `claude-opus-4-8` | $5 | $25 | Overkill for structured extraction |
## Frontend: Click-to-Highlight Char Span
- `react-pdf` / `pdf.js` viewer — renders PDF as canvas; highlights on canvas are a separate coordinate system. Use text extraction on the backend, render as `<pre>` or a styled div on the frontend. The source text is already extracted; there's no need to re-render the PDF.
- Any rich-text editor (Slate, TipTap) — overkill, read-only display only.
## Slice 3 RAG: Retrieval (as built)
**Implemented as JSONL + TF-IDF cosine, not chromadb + embeddings.**

- **Storage:** `backend/data/authorities/corpus.jsonl` — one `AuthorityRecord` per
  line (`authority_id, title, source_type, summary_seed, quote_seed, url,
  source_text, metadata`). Checkpoint/resume state in `ingest_state.json`. No
  vector DB, no separate process.
- **Retrieval:** `services/authorities.py` scores the query against each record's
  `title + summary_seed + quote_seed + source_text` with
  `TfidfVectorizer(ngram_range=(1,2), stop_words="english")` + `cosine_similarity`
  (scikit-learn), falling back to a hand-rolled stdlib TF-IDF cosine if sklearn
  isn't importable.
- **Relevance %** = `round(clamp(cosine, 0, 1) * 100)` — derived from the cosine
  score, never from LLM text (RAG-04).
- **Authority verification:** `quote_seed in source_text` — the same deterministic
  exact-match guard as the document pipeline, pointed at the corpus record.

### Why TF-IDF cosine instead of chromadb + sentence-transformers embeddings
The original stack table (above) recommended an embedding model + vector store.
We deliberately did **not** build that, for reasons specific to this MVP:

1. **The corpus is tiny and the decision said "prefer simple, inspectable local
   storage over production database complexity"** (Phase 3 CONTEXT decision). With
   ~a dozen authorities, brute-force TF-IDF cosine over a JSONL file is sub-
   millisecond — a vector index solves a scale problem we don't have.
2. **Grounding, not semantic recall, is the product.** The moat is the
   deterministic `quote in source_text` verify guard. Relevance ranking only needs
   to be *good enough* to populate the Cases/Stat./Secondary tabs sensibly; lexical
   TF-IDF over legal text (statute numbers, party names, terms of art) is a strong
   baseline, and exact-match verification — not embedding nearness — is what we
   actually display and stand behind.
3. **Zero heavyweight dependencies.** sentence-transformers pulls in PyTorch (~2 GB)
   and a model download; chromadb adds its own stack. scikit-learn (or the stdlib
   fallback) keeps install light and the whole corpus human-readable in one file.
4. **Inspectability for a demo to technical reviewers.** A reviewer can open
   `corpus.jsonl`, read every record, and trace exactly why an authority ranked
   where it did. An opaque embedding index would hide that.

**Upgrade trigger:** swap in sentence-transformers + chromadb when the corpus grows
past a few hundred records *and* lexical ranking visibly mismatches intent (e.g.
paraphrased queries that share no terms with the source). Neither condition holds
at MVP scale.
## Alternatives Considered
| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| pdfplumber | PyMuPDF | Heavier binary dep; overkill for MVP-scale PDFs; offset API is more complex |
| pdfplumber | pdfminer.six (direct) | pdfplumber is a clean wrapper around pdfminer.six — same engine, better API |
| pdfplumber | pypdf | pypdf does not expose per-character positions, only page-level text |
| pdfplumber | unstructured | Loses offsets; 200 MB+ dep tree; designed for ML pipelines not grounding |
| TF-IDF cosine over JSONL (as built) | chromadb / sentence-transformers embeddings | Embeddings + vector index solve a scale problem the ~dozen-record corpus doesn't have; PyTorch/chroma deps are heavyweight; JSONL stays human-inspectable. Grounding is enforced by exact-match verify, not embedding nearness. See "Why TF-IDF cosine" above. |
| TF-IDF cosine over JSONL (as built) | Pinecone / Weaviate / Qdrant / FAISS / hnswlib | Hosted infra or a separate index process; all overkill for a corpus that fits in one file and is brute-forced sub-millisecond |
| React + Vite | Next.js | SSR/SSG adds complexity for a demo SPA with no SEO requirement |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `unstructured` | Explicitly drops char offsets; designed for ML chunking pipelines, not grounding | pdfplumber + python-docx |
| `pypdf` | No per-character position data; `extract_text()` returns flat string with no offset map | pdfplumber |
| PDF.js / react-pdf in frontend | Canvas rendering = coordinates in a different space from extracted text offsets; highlights don't align | Extract text backend, render as `<pre>` |
| pgvector / Qdrant / Pinecone / chromadb at Slice 3 | Heavyweight infra (or a 2 GB PyTorch dep for embeddings) for a corpus that fits in one JSONL file; adds a deploy dependency before the value is proven | TF-IDF cosine over JSONL (scikit-learn, stdlib fallback) |
| LangChain / LlamaIndex | Abstracts away exactly the offset-tracking logic that is the core product differentiator; their "splitters" discard offsets | Roll the 30-line chunker manually to keep offset control |
| Celery / Redis task queue | No async workloads that require a queue at MVP scale; one analysis per upload | Async FastAPI endpoint with `asyncio` |
## Installation
# Backend
# Slice 3 RAG additions
# Frontend
## Sources
- PyPI pdfplumber 0.11.10 — https://pypi.org/pypi/pdfplumber/json
- PyPI PyMuPDF 1.27.2.3 — https://pypi.org/pypi/pymupdf/json
- PyPI anthropic 0.112.0 — https://pypi.org/pypi/anthropic/json
- PyPI FastAPI 0.138.1 — https://pypi.org/pypi/fastapi/json
- PyPI python-docx 1.2.0 — https://pypi.org/pypi/python-docx/json
- PyPI scikit-learn 1.8.0 — https://pypi.org/pypi/scikit-learn/json (as-built RAG scorer)
- PyPI sentence-transformers 5.6.0 — https://pypi.org/pypi/sentence-transformers/json (recommended-but-not-built; embedding upgrade path)
- PyPI chromadb 1.5.9 — https://pypi.org/pypi/chromadb/json (recommended-but-not-built; vector-store upgrade path)
- Anthropic models overview (verified 2026-06-26) — https://platform.claude.com/docs/en/about-claude/models/overview
- Anthropic tool use / forcing tool use (verified 2026-06-26) — https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools
- pdfplumber GitHub — char-level `.chars` with `doctop` confirmed
- PyMuPDF docs — `extractRAWDICT()` char-level positions confirmed
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
