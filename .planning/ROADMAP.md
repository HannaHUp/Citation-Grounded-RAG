# Roadmap: Citation-Grounded-RAG

## Overview

Three vertical slices, each shipping a demoable end-to-end result. Phase 1 proves the
grounding spine (offset preservation + verify guard) against one uploaded document —
zero corpus, zero external APIs, full demo in ~4-6 days. Phase 2 proves one-engine-many-
profiles cheaply before adding retrieval complexity. Phase 3 adds the Legal Authorities
RAG panel (Surface B), reusing the same grounding pattern with a real corpus. Phase 4
wraps the proven engine in the Vincent-style multi-step UX (workflow picker → task
picker + who-you-represent → two-pane grounded output), and adds page-number citations.
It comes last on purpose: the workflow shell frames features that Phases 2 and 3 build,
so building it earlier would be scaffolding around empty rooms.

## Phases

- [x] **Phase 1: Grounding Spine** - Upload → findings → click-to-highlight with ✓/⚠ badges (Surface A, end-to-end) (completed 2026-06-26)
- [x] **Phase 2: Second Profile + Auto-Detect** - Complaint profile + doc-type classify proves one-engine-many-profiles (completed 2026-06-26)
- [ ] **Phase 3: Legal Authorities RAG Panel** - Surface B: real corpus retrieval, grounded summaries, tabbed panel
- [ ] **Phase 4: Vincent-Style Workflow Shell** - Landing/workflow picker → task picker + who-you-represent → polished two-pane output + page citations

## Phase Details

### Phase 1: Grounding Spine
**Goal**: A user can upload a contract PDF or DOCX, see structured findings with verified/unverified badges, and click any finding to scroll to and highlight its exact source span in the document
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: INGEST-01, INGEST-02, INGEST-03, ENGINE-01, ENGINE-02, ENGINE-03, ENGINE-04, VERIFY-01, VERIFY-02, VERIFY-03, UIA-01, UIA-02, UIA-03
**Success Criteria** (what must be TRUE):
  1. User uploads a PDF or DOCX and the system returns structured findings within a reasonable wait
  2. Each finding card shows a finding statement, severity tag, verbatim quote, and a ✓ or ⚠ badge
  3. Clicking a finding scrolls the document pane to and highlights the exact source span
  4. At least one finding is shown with a ⚠ badge (unverified) with explanatory text, not hidden
  5. The round-trip assertion `full_text[start:end] == chunk.text` holds for all chunks (verifiable via backend test)
**Plans**: 3 plans
Plans:
**Wave 1**
- [x] 01-01-PLAN.md — Backend spine: scaffold + data model + offset-preserving extraction + chunker + /upload (D-03 round-trip GATE)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-02-PLAN.md — Engine + verify guard: contract-risk profile + forced tool-call + deterministic verifier + /analyze

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 01-03-PLAN.md — Frontend two-pane UI: upload → findings (✓/⚠ badges) → click-to-highlight + end-to-end demo
**UI hint**: yes

### Phase 2: Second Profile + Auto-Detect
**Goal**: A user uploading a litigation complaint sees complaint-specific claim analysis run on the identical pipeline with no engine changes; a user uploading a contract sees the contract profile; the detected doc type is displayed with a manual override
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: PROF-01, PROF-02, PROF-03
**Success Criteria** (what must be TRUE):
  1. Uploading a litigation complaint auto-detects "complaint" and runs the claims analysis profile
  2. Uploading a contract auto-detects "contract" and runs the risk analysis profile
  3. The detected doc type label is visible and a manual override affordance is present
**Plans**: 2 plans
Plans:
**Wave 1**
- [x] 02-01-PLAN.md — Backend slice: complaint profile (new file + 1 registry line) + classify_doc_type forced tool-call + /upload returns detected type (PROF-01, PROF-02)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 02-02-PLAN.md — Frontend slice: detected-type label + 2-button override + analyze() passes selected profile_id + profile-aware legend (PROF-02, PROF-03)
**UI hint**: yes

### Phase 3: Legal Authorities RAG Panel
**Goal**: A user can trigger an authority lookup for a finding and see a tabbed panel of relevant US statutes and cases, each with an AI summary run through the verify guard, a cosine-derived relevance %, a verbatim quote block, and a link to the real source
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: RAG-01, RAG-02, RAG-03, RAG-04, RAG-05
**Success Criteria** (what must be TRUE):
  1. System ingests a small real corpus via CourtListener API with checkpoint/resume (ingest can be interrupted and resumed)
  2. Authority lookup returns top-k relevant authorities from the local vector store
  3. Each authority entry shows an AI summary with ✓/⚠ badge (same verify guard as Phase 1, pointed at corpus chunk)
  4. Relevance % is derived from cosine similarity score, not LLM output, and is visible per authority
  5. Tabbed panel separates Cases, Statutes & Regulations, and Secondary sources with real source URLs
**Plans**: TBD
**UI hint**: yes

### Phase 4: Vincent-Style Workflow Shell
**Goal**: A user lands on a "What would you like to do?" workflow picker, selects a workflow, uploads a document, picks an analysis task and who they represent, and sees a polished two-pane output (document-grounded findings with page citations on the left, Legal Authorities on the right) — matching the validated Vincent-style flow
**Mode:** mvp
**Depends on**: Phase 2, Phase 3
**Requirements**: FLOW-01, FLOW-02, FLOW-03, FLOW-04, FLOW-05
**Success Criteria** (what must be TRUE):
  1. The landing screen shows a Workflows grid; selecting "Analyze a Complaint"/"Analyze a Contract" starts that workflow and leads to upload
  2. After upload, a task-picker screen lists the relevant analysis profiles as selectable boxes wired to the real Phase-2 profiles
  3. Selecting Plaintiff/Defendant/Neutral changes the framing of the generated findings (the choice reaches the LLM prompt)
  4. Each finding displays the correct source page number alongside the ✓/⚠ badge
  5. The output is the two-pane layout (findings left, Legal Authorities right) with the polished card/badge/severity design from `.planning/sketches/vincent-flow.html`
**Plans**: TBD
**UI hint**: yes
**Design reference**: `.planning/sketches/vincent-flow.html` (validated 2026-06-26)

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Grounding Spine | 3/3 | Complete    | 2026-06-26 |
| 2. Second Profile + Auto-Detect | 2/2 | Complete   | 2026-06-26 |
| 3. Legal Authorities RAG Panel | 0/TBD | Not started | - |
| 4. Vincent-Style Workflow Shell | 0/TBD | Not started | - |
