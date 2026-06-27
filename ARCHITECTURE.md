# Architecture — Citation-Grounded-RAG

A legal-analysis MVP: upload a contract or litigation complaint, an LLM extracts
findings (risks, claims, obligations), and **every finding is grounded to an exact,
verifiable source span**. A deterministic verify guard flags any finding whose
quote can't be matched back to the source.

> **The moat in one sentence:** the LLM is never trusted to assert that a claim is
> supported. A finding is marked ✓ *verified* only if a deterministic, non-LLM
> string match locates its quote in the original document. Everything else is
> presentation around that guarantee.

---

## 1. System at a glance

```
┌─────────────┐   POST /upload    ┌──────────────────────────────────────────┐
│   React     │ ────────────────▶ │  FastAPI (backend/main.py, port 8010)      │
│  (Vite SPA) │   POST /analyze   │                                            │
│ port 5173   │ ────────────────▶ │  extraction → chunker → llm_finding →      │
│             │   POST /authorities│  verifier   (the grounding pipeline)       │
│             │ ────────────────▶ │  authorities (RAG: JSONL + TF-IDF cosine)  │
└─────────────┘                   └──────────────────────────────────────────┘
                                          │
                                   in-memory doc_store (dict)
                                   corpus.jsonl (legal authorities)
```

- **Backend:** Python + FastAPI, 3 POST endpoints. No DB — documents live in an
  in-memory dict; the authority corpus is a JSONL file on disk.
- **Frontend:** React/Vite single-page app, 4-step state machine, no router.
- **LLM:** Claude (`claude-haiku-4-5-20251001`) via the Anthropic SDK, using
  **forced tool-output** so findings always conform to a fixed schema.

There are **three workflows** worth understanding. Each is documented below as
**What it is → Why we have it → How it's implemented**.

---

## 2. Workflow A — The Grounding Pipeline (the core product)

### What it is
The path from an uploaded file to a list of findings, each carrying a verified/
unverified badge, an exact source span (character offsets), and a page number.

`POST /upload` → `POST /analyze` → findings rendered with ✓/⚠ badges and
click-to-highlight.

### Why we have it
This *is* the product. A plain LLM will happily summarize a contract and
hallucinate a clause that isn't there. Our differentiator is that **we can prove,
deterministically, whether each generated claim actually appears in the source** —
and we show the ones that don't (⚠) rather than hiding them. To do that, we must
preserve exact character offsets from extraction all the way to the UI highlight,
and we must verify quotes with code, not with the model.

### How it's implemented

The pipeline is five stages. **Offsets are computed once at extraction and never
recomputed** — this is the load-bearing rule that makes click-to-highlight exact.

**1. Extraction** (`services/extraction.py`)
- **PDF:** `extract_pdf_document()` uses `pdfplumber` and reads **per-character**
  data (`.chars`), not `page.extract_text()` (which normalizes whitespace and
  corrupts offsets). Chars are sorted by `(doctop, x0)` (document-Y, then X),
  concatenated into `full_text` while accumulating a running offset. The first
  offset seen on each page is recorded to build **`PageSpan`s** (contiguous,
  ascending `[start_offset, end_offset)` ranges per page).
- **DOCX:** `extract_docx_document()` uses `python-docx`, joins paragraphs with
  `\n`. ⚠ **Shortcut:** python-docx exposes no rendered pagination, so DOCX always
  produces a single `PageSpan(page 1)`. Every DOCX finding cites "p. 1".

**2. Chunking** (`services/chunker.py`)
- `chunk_text()` splits `full_text` into ≤2000-char windows, preferring to break
  on the last `\n`. Each `Chunk` carries `chunk_id` (`"{doc_id}:{idx}"`),
  `text`, `start_offset`, `end_offset`.
- **Hard invariant (the round-trip gate):** `chunk.text == full_text[start:end]`,
  enforced with an explicit `raise ValueError` (not `assert`, so it survives
  `python -O`). If offset bookkeeping ever drifts, ingestion fails loudly here.

**3. LLM finding extraction** (`services/llm_finding.py`)
- `run_llm(chunks, profile, full_text, perspective=None)`. The model receives
  **`chunk_id` + chunk text only — never offsets** (offsets are ours to compute,
  not the model's to guess).
- **Forced tool-output:** the call sets `tools=[extract_findings]` with the
  profile's `output_schema`, plus `tool_choice={"type":"tool", ...}`, so the
  model is *forced* to return data matching `FINDINGS_SCHEMA`
  (`{finding, severity, source_chunk_id, quote}` per item). The quote field's
  description forbids normalization — return exact bytes.
- **Perspective** (Plaintiff/Defendant/Neutral) is injected by *prepending* a
  framing string from `_perspective_context()` to the user message. This is the
  **only** place perspective is handled — no profile branching (see Workflow C).
- **Offline mode:** `GROUNDING_STUB=1` returns canned findings from
  `stub_findings.py` (for demos / tests without an API key). Crucially, **the
  verify guard still runs for real**, so ✓/⚠ badges are still earned, and the
  stub includes deliberate near-miss quotes to exercise the ⚠ path.

**4. Verify guard** (`services/verifier.py`) — the moat
- `verify(finding, full_text, chunks_by_id, page_spans)` does a **deterministic
  exact string match, no LLM involvement.** Algorithm:
  1. Empty quote → unverified (avoids the `"".find()==0` trap).
  2. Unknown `source_chunk_id` → unverified (catches fabricated chunk ids).
  3. **Search the cited chunk first** (`chunk.text.find(quote)`). If found,
     `abs_start = chunk.start_offset + local_index`. Searching the chunk first
     disambiguates quotes that repeat across the document — it resolves to the
     clause the model actually grounded in.
  4. **Fallback: search the whole `full_text`.** Reached only when the chunk_id
     was mis-attributed but the quote is still genuinely present.
  5. No match anywhere → `verified=False`, `abs_start/abs_end=None`.
- **`source_page`** is then derived by `page_for_offset(page_spans, abs_start)` —
  a linear scan for the span containing the offset. The page comes from the
  verifier *after* offsets are known; it is **not** in the LLM schema and the LLM
  never produces it.

**5. Response.** `/analyze` returns `{findings: [VerifiedFinding...]}`. The client
**cannot** send a `verified` field — the request model deliberately omits it, so
verified-ness can only ever be asserted server-side by the guard.

### Key data shapes
| Model | Fields |
|-------|--------|
| `Chunk` | `chunk_id, text, start_offset, end_offset` (`full_text[start:end]==text`) |
| `PageSpan` | `page_number, start_offset, end_offset` |
| `RawFinding` (LLM out) | `finding, severity, source_chunk_id, quote` |
| `VerifiedFinding` (API out) | `…raw fields… + verified: bool, abs_start, abs_end, source_page` (last three `None` when unverified) |

---

## 3. Workflow B — Legal Authorities (RAG panel)

### What it is
For a given finding, retrieve relevant US legal authorities (cases, statutes/
regulations, secondary sources) from a local corpus, each shown with a relevance
%, a verbatim quote, a summary, a verified badge, and a real source URL.

`POST /authorities` with a finding → tabbed panel on the right of the output screen.

### Why we have it
Grounding a finding to *the uploaded document* (Workflow A) proves the claim is in
the contract. Grounding it to *real external law* shows the analysis is anchored
in actual authority, not the model's training-data recollection of statutes. Same
philosophy as the verify guard, pointed at a corpus instead of the upload.

### How it's implemented

> ⚠ **Doc-vs-code divergence — flag this to the tech lead.** `CLAUDE.md`'s stack
> table specifies **chromadb + sentence-transformers embeddings**. The *implemented*
> code uses neither: the corpus is **JSONL** and retrieval is **TF-IDF cosine
> similarity** (sklearn `TfidfVectorizer`, with a hand-rolled TF-IDF fallback if
> sklearn isn't importable). Authority summaries are currently the **canned
> `summary_seed`**, not LLM-generated. The chromadb/embeddings upgrade is unbuilt.

**Ingestion** (`services/authority_ingest.py`, CLI `scripts/ingest_authorities.py`)
- **Storage:** `backend/data/authorities/corpus.jsonl` (one `AuthorityRecord` per
  line) + `ingest_state.json` for checkpoint/resume.
- **Seed records:** `seeded_authority_records()` provides 9 hardcoded authorities
  (Clayton Act §7, Brown Shoe, FTC/DOJ Merger Guidelines, Cal. Corp. Code, venue
  statutes, etc.) matching the antitrust + nonprofit-fiduciary demo.
- **CourtListener:** `ingest_courtlistener()` fetches `/api/rest/v4/search/`, dedups
  by `authority_id`, and supports resume from a saved `next_url`. ⚠ **Shortcut:**
  the loop ends with an unconditional `break` — only **one page** is fetched per
  run despite the pagination machinery being present.

**Retrieval** (`services/authorities.py`)
- `retrieve_authorities(document_text, profile_id, finding=, quote=)`:
  - **Query:** finding-lookup mode (`finding`/`quote` present) → `finding + quote`;
    document mode → `document_text + _PROFILE_TERMS[profile_id]` (hardcoded keyword
    bags per profile).
  - **Scoring:** `_cosine_scores()` over `title + summary_seed + quote_seed +
    source_text` for each record. Sort by `(-score, title)`.
  - Finding mode also filters `score >= 0.04` and `_prefer_source_type_coverage()`
    guarantees at least one Case / Statute / Secondary before filling to `limit`.
- **Relevance %** = `round(clamp(cosine, 0, 1) * 100)` — **derived from cosine, not
  the LLM.**
- **Authority "verified"** = `quote_seed in source_text` — the same deterministic
  exact-match guard, applied to the record's own source text.
- ⚠ `/authorities` accepts `source_chunk_id` but **ignores it**; its default
  `profile_id` is `contract_antitrust`, which is a retrieval keyword key, **not** a
  registered analysis profile.

---

## 4. Workflow C — Profile System (one engine, many document types)

### What it is
The same extraction/LLM/verify engine analyzes both contracts and complaints. The
only thing that changes is a **profile** — a pure-data object describing how to
prompt the model for that document type.

### Why we have it
A legal-AI tool must handle many document types. The cheap, maintainable way is one
engine driven by data, not a forest of `if doc_type == ...` branches. This was
proven in Phase 2: adding the complaint profile required **zero engine edits**.

### How it's implemented
- **`AnalysisProfile`** dataclass: `profile_id, display_name, system_prompt,
  tool_description, output_schema`.
- Each profile is one module-level instance (`profiles/contract_risk.py`,
  `profiles/complaint_claims.py`). Both reuse the shared `FINDINGS_SCHEMA`; they
  differ only in `system_prompt` and `tool_description`.
- **Registry** (`profiles/__init__.py`): `PROFILES = {id: profile}`. **Adding a
  document type = one import + one dict entry.** `get_profile(id)` raises 400 on
  unknown ids.
- The engine (`run_llm`) consumes `profile.system_prompt`, `.tool_description`,
  `.output_schema` generically — **there is no `if profile_id == ...` anywhere.**
- Document type is auto-detected on upload by `classify_doc_type()` (a separate
  forced tool-call with enum `["contract","complaint"]`, with a keyword-heuristic
  fallback). The user can override it in the UI.

---

## 5. Workflow D — Frontend 4-step flow

### What it is
A Vincent-style guided UX: pick a workflow → upload → pick task & perspective →
two-pane grounded output.

### Why we have it
The workflow shell *frames* the features the backend provides — it's built last on
purpose, because a picker around empty rooms is scaffolding. It turns the raw
endpoints into a coherent "what would you like to do?" product surface.

### How it's implemented
State machine in `App.tsx`: `step ∈ {workflow, upload, tasks, output}`, all local
`useState`, no router/global store. API client in `api.ts` (`BASE =
http://localhost:8010`).

| Step | Component | Sends | Result |
|------|-----------|-------|--------|
| `workflow` | `WorkflowPicker` | — | picks workflow (complaint/contract enabled; others disabled tiles), sets default profile |
| `upload` | `WorkflowUploadStep` → `UploadZone` | `POST /upload` | stores `docId, fullText, detectedDocType, profileId` |
| `tasks` | `TaskPicker` | `POST /analyze` (with `perspective` **only** for complaint) | findings; auto-selects first verified (else first) finding |
| `output` | `WorkflowOutput` | `POST /authorities` per active finding | two-pane render |

- **Output layout:** left = severity-sorted `FindingCard`s + a `DocViewer` source
  preview; right = `LegalAuthoritiesPanel` (tabs: Cases / Stat. & Reg. / Secondary)
  with explicit loading / error / empty / no-active-finding states.
- **`FindingCard`:** severity tag · `p. N` (only when `source_page` present) ·
  verified badge · statement · quote blockquote · unverified explainer when `!verified`.
- **Click-to-highlight** (`handleFindingClick`): for a verified finding with
  non-null offsets, `setHighlight({start: abs_start, end: abs_end})`. `DocViewer`
  renders `<pre>` with `text.slice(0,start) + <mark>…</mark> + text.slice(end)` and
  `scrollIntoView` on the mark. **The highlight coordinates are the backend's
  absolute offsets** — the same offset chain that started at extraction. Clicking
  also refreshes the right-pane authorities for that finding.

---

## 6. Module dependency map

```
main.py
 ├─ profiles.get_profile → {contract_risk, complaint_claims} → models.{AnalysisProfile, FINDINGS_SCHEMA}
 ├─ services.extraction.{extract_pdf_document, extract_docx_document} → models.{ExtractedDocument, PageSpan}   [pdfplumber, python-docx]
 ├─ services.chunker.chunk_text → models.Chunk
 ├─ services.llm_finding.{run_llm, classify_doc_type} → models.{AnalysisProfile, Chunk, RawFinding}   [anthropic, stub_findings]
 ├─ services.verifier.verify_all → verify → page_for_offset → models.{Chunk, PageSpan, RawFinding, VerifiedFinding}
 ├─ services.authorities.{retrieve_authorities, authority_response} → authority_ingest.{corpus, AuthorityRecord}   [sklearn optional]
 └─ store.doc_store  (in-memory dict[str, DocStore])

frontend: App.tsx → api.ts, workflows.ts, types.ts
          App → {WorkflowPicker, WorkflowUploadStep→UploadZone, TaskPicker, WorkflowOutput}
          WorkflowOutput → {FindingCard→(SeverityTag,VerifiedBadge), DocViewer, LegalAuthoritiesPanel→VerifiedBadge}
```

---

## 7. Known shortcuts & MVP scope (call these out proactively)

These are deliberate MVP simplifications. Each has a clear upgrade trigger.

1. **In-memory document store** (`store.py`) — lost on restart. Swap to FS/DB when
   a second user exists (auth is deferred for the same reason).
2. **RAG ≠ documented stack** — JSONL + TF-IDF cosine, **not** chromadb +
   sentence-transformers. Authority summaries are canned (`summary_seed`), not
   LLM-generated. Biggest gap between `CLAUDE.md` and reality.
3. **CourtListener ingest fetches one page only** (unconditional `break`); resume/
   limit scaffolding is present but inactive past page 1.
4. **DOCX page citations are always "p. 1"** (python-docx has no pagination).
5. **`contract_antitrust`** is a retrieval keyword bag, not a runnable analysis
   profile; it's the `/authorities` default.
6. **`/authorities` ignores `source_chunk_id`** even though it accepts it.
7. **DocViewer supports a single active highlight.**
8. **`GROUNDING_STUB=1`** bypasses the live LLM with canned findings — but the
   verify guard still runs, so badges remain real.

---

## 8. Trust boundaries & validation

- **Upload** validates: extension allowlist (`.pdf`/`.docx`), size ≤ 20 MB, and a
  **magic-byte check** (`%PDF` / `PK`) — not just the extension. CORS is locked to
  the Vite dev origin, methods restricted to POST.
- **Verified-ness is server-only.** The `/analyze` request model has no `verified`
  field by design; the client can never claim a finding is supported.
- **The round-trip invariant** (`chunk.text == full_text[start:end]`) fails loudly
  at chunk time, so a corrupted offset can never silently reach the UI.
