# Requirements: Citation-Grounded-RAG

**Defined:** 2026-06-26
**Core Value:** Every generated claim links to a verifiable real source, with a deterministic guard that measures and shows whether each claim is actually supported.

## v1 Requirements

Requirements for the initial release. Each maps to a roadmap phase.

### Ingestion (Grounding Spine)

- [x] **INGEST-01**: User can upload a PDF or DOCX contract/complaint
- [x] **INGEST-02**: System extracts full document text preserving exact character offsets (round-trip assertion: `full_text[start:end] == verbatim`)
- [x] **INGEST-03**: System chunks text into `{text, start_offset, end_offset}` records, asserting `chunk.text == full_text[start:end]` at creation

### Analysis Engine

- [x] **ENGINE-01**: System runs one forced-structured-output LLM call producing findings `[{finding, severity, source_chunk_id, quote}]` with the quote forced verbatim
- [x] **ENGINE-02**: The LLM never receives or returns char offsets — only a quote string the verifier resolves
- [x] **ENGINE-03**: A contract-review analysis profile (risks, obligations, severity) drives the first findings run
- [x] **ENGINE-04**: An analysis profile is pure data (prompt + output schema); adding a profile requires no engine code changes

### Verify Guard

- [x] **VERIFY-01**: A deterministic verifier resolves each finding's quote via exact `source_text.find(quote)`; match → verified (✓), no match → unverified (⚠)
- [x] **VERIFY-02**: The verifier is the only component that produces `verified=True`, uses no LLM, and cannot be bypassed
- [x] **VERIFY-03**: Unverified findings are shown (never hidden) with a ⚠ badge and explanatory text

### Findings UI (Surface A)

- [x] **UIA-01**: Two-pane layout renders the document on the left and findings on the right
- [x] **UIA-02**: Each finding card shows the finding statement, severity tag, verbatim quote, and ✓/⚠ badge
- [x] **UIA-03**: Clicking a finding scrolls the document pane to and highlights the exact source span

### Profiles & Auto-Detect

- [x] **PROF-01**: A second analysis profile (litigation complaint → claims) runs on the identical pipeline with zero engine edits
- [x] **PROF-02**: On upload, a doc-type classify call detects contract vs complaint and shows the relevant profile cards
- [x] **PROF-03**: The detected doc type is displayed with a manual override affordance

### Legal Authorities RAG (Surface B)

- [ ] **RAG-01**: System ingests a small real corpus of US statutes/CFR + cases via CourtListener's free API, with checkpoint/resume
- [ ] **RAG-02**: For an authority-backed profile, system retrieves the top-k relevant authorities from a local vector store
- [ ] **RAG-03**: System generates a grounded AI summary per authority, run through the same verify guard pointed at the corpus chunk
- [ ] **RAG-04**: Authority relevance % is derived from the retrieval cosine score, not the LLM
- [ ] **RAG-05**: Legal Authorities panel shows each authority's AI summary, relevance %, verbatim quote block, and a link to the real source, tabbed by source type (Cases / Stat. & Reg. / Secondary)

### Vincent-Style Workflow Shell (Surface UX)

Reference design: `.planning/sketches/vincent-flow.html` (validated 2026-06-26).

- [ ] **FLOW-01**: A landing screen ("What would you like to do?") presents a Workflows grid (Analyze a Complaint, Analyze a Contract, …); selecting one starts that workflow
- [ ] **FLOW-02**: After upload, a task-picker screen ("Here are some things I can help you do") presents the relevant analysis profiles as selectable boxes (Claims, Defenses, Timeline, …) wired to the Phase-2 profiles
- [ ] **FLOW-03**: User selects who they represent (Plaintiff / Defendant / Neutral); the choice is injected into the analysis prompt so claims/defenses are framed from that party's perspective
- [ ] **FLOW-04**: Each finding displays the source **page number** (e.g. "p. 12"), derived from the extractor's per-char page map (not just the char-offset highlight)
- [ ] **FLOW-05**: The output screen is the two-pane Vincent layout — left = document-grounded findings, right = Legal Authorities panel — with the polished card/badge/severity visual design from the reference sketch

## v2 Requirements

Deferred to a future release. Tracked but not in the current roadmap.

### Verification Quality

- **VQ-01**: Fuzzy quote matching — normalize whitespace/quotes both sides, accept ≥~95% similarity, snap highlight to the real span (add only after the exact-match ⚠ rate is measured on real documents)

### Persistence

- **PERSIST-01**: User accounts and authentication (add when a second user exists)
- **PERSIST-02**: Persistent document/findings storage (currently in-memory)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Multi-jurisdiction / 110-country corpus | One corpus teaches the same skill; pure scope inflation |
| Judge analytics, 975M dockets | Billion-doc proprietary corpus is not the target; it's the architecture pattern that matters |
| Fine-tuning a model | The point is RAG + grounding, not model memory |
| Fancy hover cards / animations | Polish before the engine works; skip until the spine is proven |
| Vector DB before Slice 3 | No corpus exists before then — pure infra debt |
| LangChain / LlamaIndex | Their text splitters discard the char offsets that are the entire product |
| PDF.js / canvas-based viewer | Canvas coordinates don't align with extracted-text offsets |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01 | Phase 1 | Complete |
| INGEST-02 | Phase 1 | Complete |
| INGEST-03 | Phase 1 | Complete |
| ENGINE-01 | Phase 1 | Complete |
| ENGINE-02 | Phase 1 | Complete |
| ENGINE-03 | Phase 1 | Complete |
| ENGINE-04 | Phase 1 | Complete |
| VERIFY-01 | Phase 1 | Complete |
| VERIFY-02 | Phase 1 | Complete |
| VERIFY-03 | Phase 1 | Complete |
| UIA-01 | Phase 1 | Complete |
| UIA-02 | Phase 1 | Complete |
| UIA-03 | Phase 1 | Complete |
| PROF-01 | Phase 2 | Complete |
| PROF-02 | Phase 2 | Complete |
| PROF-03 | Phase 2 | Complete |
| RAG-01 | Phase 3 | Pending |
| RAG-02 | Phase 3 | Pending |
| RAG-03 | Phase 3 | Pending |
| RAG-04 | Phase 3 | Pending |
| RAG-05 | Phase 3 | Pending |
| FLOW-01 | Phase 4 | Pending |
| FLOW-02 | Phase 4 | Pending |
| FLOW-03 | Phase 4 | Pending |
| FLOW-04 | Phase 4 | Pending |
| FLOW-05 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-26*
*Last updated: 2026-06-26 after initial definition*
