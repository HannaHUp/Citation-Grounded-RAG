---
phase: 04-vincent-style-workflow-shell
plan: 05
type: redesign-plan
status: ready-for-implementation
autonomous: false
created: 2026-06-27
requirements:
  - Vincent-style complaint workflow
  - Demo-document fixture mode
  - Future LLM provider compatibility
---

# Phase 4 Plan 05: Vincent-Style Complaint Workflow Redesign

## Objective

Replace the current wizard-like Phase 4 frontend with a Vincent-style complaint workflow split across three distinct UI pages:

1. **Document Entry Page**: user enters Analyze a Complaint and uploads a complaint or selects the bundled demo complaint `musk-v-altman-openai-complaint-sf.pdf`.
2. **Workflow Setup Page**: the app shows the detected complaint context, task buttons, and extracted represented-party selector.
3. **Grounded Chat Workspace Page**: the app renders the initial LLM-style legal analysis and supports follow-up chat, with inline citations tied to the uploaded complaint and a right-side Legal Authorities / similar matters panel.

In fixture mode, rich hardcoded results are shown only for the bundled Musk v. Altman demo complaint. Later, switching to real LLM/API mode should not require frontend or endpoint contract changes.

The current Phase 4 implementation has useful backend foundations (`source_page`, page spans, perspective plumbing, authority retrieval), but the UX shape is wrong. The target is not a generic workflow wizard. It is a document-analysis workspace where LLM output is citation-grounded and externally verifiable.

The implementation must not place document entry, task selection, party selection, report output, source preview, legal authorities, and follow-up chat into one long page. Each product mode needs its own page-level route/state. Source preview is not a permanently visible panel under the assistant/chat transcript; it is a citation-driven verification view opened only when the user clicks a citation.

## Product Workflow

### Page 1: Document Entry

The first complaint screen should offer:

- Upload your own complaint.
- Use demo complaint: `musk-v-altman-openai-complaint-sf.pdf`.

The demo option exists so hardcoded fixture output is honest and document-specific.

After either action succeeds, navigate to Page 2.

### Page 2: Workflow Setup

This page answers: "What should I analyze, and for whom?"

It should show:

- Compact detected document bar.
- Detected summary.
- "Here are some things I can help you do" task grid.
- "What party do you represent?" party selector.
- Run/start analysis button.

It should not show the final report, source preview, legal authorities panel, or chat transcript. Those belong on Page 3.

### Document Loading Rules

If the user selects the demo complaint:

- Backend loads the bundled PDF.
- Backend returns a demo `doc_id`, extracted text, detected workflow metadata, extracted parties, and available tasks.
- Rich fixture analysis is available.

If the user uploads a different file while fixture mode is active:

- Backend extracts and stores the document normally.
- Backend returns detected type/profile if available.
- UI should clearly explain that rich Vincent-style complaint analysis for arbitrary documents requires LLM mode.
- The app must not show Musk v. Altman hardcoded legal output for unrelated files.

If LLM mode is active later:

- Same UI and endpoint contracts should support arbitrary uploaded complaints.
- Party extraction, task selection metadata, structured analysis, citations, and authorities should come from provider-backed services.

### Task Grid

After the complaint is loaded, show the Vincent-style task grid:

- Claims
- Defenses
- Timeline
- Client Questions
- Dramatis Personae
- Matters Like This
- Parties
- Relief
- Key Allegations
- Contract Formation
- Fiduciary Duties

Tasks can be enabled, disabled, or fixture-backed, but the UI must distinguish real runnable behavior from unavailable future behavior.

For the demo complaint, fixture mode should support at least:

- Claims
- Parties
- Key Allegations
- Contract Formation
- Fiduciary Duties
- Matters Like This

### Represented Party Selection

Replace generic Plaintiff/Defendant/Neutral as the main selector with:

**What party do you represent?**

For the Musk v. Altman demo complaint, fixture parties should include:

- Elon Musk
- Samuel Altman
- Gregory Brockman
- OpenAI, Inc.
- OpenAI, L.L.C.
- OpenAI, L.P.
- OpenAI GP, L.L.C.
- OpenAI Global, LLC
- OpenAI Holdings, LLC
- OpenAI OpCo, LLC
- OAI Corporation, LLC
- Microsoft
- DOES 1 through 100

The data model should still allow party role/type metadata, for example person, company, plaintiff, defendant, affiliate, unknown.

Later LLM mode should populate this list from the uploaded complaint through the same backend contract.

After the user selects tasks and represented parties, clicking run/start analysis should navigate to Page 3.

### Page 3: Grounded Chat Workspace

This page answers: "What did the assistant find, and what can I ask next?"

The workspace should contain:

- Compact header: workflow name, document name, selected tasks, represented parties, back-to-setup action.
- Main chat transcript:
  - first assistant turn is the initial structured legal analysis/report
  - later turns are user follow-up questions and assistant answers
- Persistent follow-up input at the bottom.
- Right-side contextual panel:
  - Legal Authorities
  - similar cases/matters
- Citation verification entry point when a citation is selected

Do not render the source preview under the chat transcript by default. Page 3 should primarily show assistant/user messages and the right Legal Authorities panel. The source document/PDF preview should be opened by clicking an inline citation, using one of these patterns:

- a separate **Source Verification Page** with a back button to the chat workspace
- a full-height right drawer replacing the authorities panel while verification is active
- a modal/overlay focused on the cited page/span

The Vincent demo behavior is closer to a source/PDF verification view triggered by clicking a citation, not a second always-visible document pane below the answer.

The task grid and party selector should not remain expanded on this page. They may be summarized in the header or a collapsible context drawer.

### Initial Analysis

Input:

- `doc_id`
- selected task IDs
- represented party IDs

Output:

- A first assistant chat turn containing a structured legal report with sections, paragraphs, tables, and inline citations.
- Citations must resolve to source page, quote, and source span when available.
- The report should be rendered like a legal memo/work product, not as generic finding cards.

Example left-pane output:

- `(1) All Claims`
- numbered claim list with citations
- `(2) Claims Table`
- rows for claim, related citations, governing law, related facts, related parties/witnesses, source
- sections for contract formation, fiduciary duties, allegations, or other selected tasks

### Follow-Up Chat

Follow-up chat is part of the target product, not a later redesign.

Fixture mode should support a small set of hardcoded follow-up examples for the demo complaint, such as:

- "What are the strongest claims?"
- "What defenses could Altman raise?"
- "What cases are most like this?"
- "Where does the complaint allege breach of fiduciary duty?"

If the user asks an unsupported question in fixture mode, the app should return a clear grounded limitation message rather than pretending to answer from the demo data.

LLM mode should later use the same chat contracts for arbitrary follow-up questions.

### Citation Trust-But-Verify

Inline citations are the core interaction.

For each citation such as `p. 31`:

- Hover shows a compact tooltip:
  - document name
  - page number
  - quote/snippet
- Click opens a source/PDF verification view at the cited page/span.
- Exact-span highlighting should use existing `abs_start` / `abs_end` where available.

The citation model must support multiple citations per report item. Do not limit citations to one `source_page` badge per finding card.

### Right Ground-Truth Panel

The right panel should behave like Vincent's Legal Authorities / source-ground-truth panel:

- Close button
- Title: Legal Authorities
- Tabs:
  - All
  - Cases
  - Stat. & Reg.
  - Admin. Decisions
  - Secondary
- Search within results
- Result count
- Sort dropdown, e.g. Most Relevant
- Modify List button placeholder
- Authority cards with:
  - title
  - source type
  - jurisdiction/court
  - relevance score
  - treatment badge when available, e.g. Distinguished
  - grounded summary
  - verbatim quote block
  - source link

For `Matters Like This`, fixture mode should show similar cases and, where possible, matter/docket-style records. MVP can use the existing authority card shape with a `similar_case` source type or metadata extension.

## Provider Architecture

The implementation should create provider interfaces so fixture mode and future API mode share contracts.

Recommended providers:

- `DocumentWorkflowProvider`
  - Input: `doc_id`
  - Output: detected workflow metadata, available tasks, extracted parties, fixture availability
- `PartyExtractor`
  - Input: document text/chunks
  - Output: parties/entities
- `AnalysisRunner`
  - Input: document, selected tasks, represented parties
  - Output: structured legal report
- `CitationResolver`
  - Input: `doc_id`, citation ID
  - Output: source document name, page, quote, offsets
- `AuthorityRetriever`
  - Input: `doc_id`, report item/task/finding context
  - Output: legal authorities and similar matters

Provider mode should be controlled by configuration:

```env
AI_PROVIDER=fixture
```

Future:

```env
AI_PROVIDER=llm
ANTHROPIC_API_KEY=...
```

Fixture mode behavior:

- Demo complaint selected or matching known filename/hash: return rich Musk v. Altman fixture data.
- Other uploaded document: return extraction/detection metadata, but do not return Musk v. Altman report content.

LLM mode behavior:

- Use the same endpoints and models.
- Populate parties, tasks, report, citations, and authorities from real providers.

## Backend Contracts

Add or adapt backend models.

### ComplaintWorkflowResponse

Fields:

- `doc_id`
- `document_name`
- `workflow_id`
- `detected_doc_type`
- `detected_summary`
- `fixture_available`
- `tasks: WorkflowTask[]`
- `parties: ExtractedParty[]`

### ExtractedParty

Fields:

- `id`
- `name`
- `role`
- `type`
- `selected_by_default`

### WorkflowTask

Fields:

- `id`
- `title`
- `description`
- `category`
- `enabled`
- `fixture_supported`

### AnalysisReport

Fields:

- `id`
- `title`
- `subtitle`
- `sections`
- `tables`
- `primary_task_ids`
- `represented_party_ids`

### ChatThread

Fields:

- `thread_id`
- `doc_id`
- `selected_task_ids`
- `represented_party_ids`
- `messages`

### ChatMessage

Fields:

- `id`
- `role`: `user` or `assistant`
- `content`
- `report`
- `citations`
- `created_at`

### ReportSection

Fields:

- `id`
- `heading`
- `blocks`

### ReportBlock

Possible types:

- `paragraph`
- `ordered_list`
- `bulleted_list`
- `callout`
- `table_ref`

Each text-bearing block should support inline citation references.

### ReportTable

Fields:

- `id`
- `title`
- `columns`
- `rows`

Cells should support citation references.

### ReportCitation

Fields:

- `id`
- `label`
- `source_doc_name`
- `page`
- `quote`
- `abs_start`
- `abs_end`

### Endpoint Candidates

Prefer additive endpoints so existing tests and APIs remain stable:

- `POST /demo/complaint/musk-altman`
  - Loads bundled demo complaint and returns upload/workflow metadata.
- `GET /workflow/{doc_id}`
  - Returns `ComplaintWorkflowResponse`.
- `POST /analysis/report`
  - Body: `doc_id`, `task_ids`, `represented_party_ids`.
  - Returns initial `AnalysisReport` or creates the first assistant message in a chat thread.
- `POST /chat/start`
  - Body: `doc_id`, `task_ids`, `represented_party_ids`.
  - Returns `ChatThread` with the initial assistant analysis message.
- `POST /chat/message`
  - Body: `thread_id`, `message`.
  - Returns assistant `ChatMessage` with grounded citations.
- `GET /citation/{doc_id}/{citation_id}`
  - Returns `ReportCitation`.
- Existing `/authorities` can be reused or adapted for right-panel results.

If implementation prefers fewer endpoints, it may combine demo load and workflow metadata, but the frontend should still consume stable typed contracts.

## Frontend Changes

Rework the current Phase 4 frontend around three page-level states/routes.

### Page-Level States

- `entry`
  - upload or demo document selection only
- `setup`
  - detected complaint context, tasks, represented parties, run/start action
- `workspace`
  - grounded chat transcript, source/legal-authorities side panel, follow-up input

Do not render all three pages at once.

### Components to Create or Replace

- `ComplaintEntry`
  - Upload own file
  - Use demo complaint button
- `ComplaintSetup`
  - Document header
  - Detected summary
  - Task grid
  - Represented party selector
  - Run analysis action
- `ComplaintChatWorkspace`
  - Chat transcript
  - Initial report assistant message
  - Follow-up input
  - Right contextual panel
- `ComplaintTaskGrid`
  - Vincent-style selectable cards
- `RepresentedPartySelector`
  - Extracted party chips/checkboxes
- `AnalysisReportView`
  - Renders legal memo/table output
- `InlineCitation`
  - Hover tooltip and click behavior
- `SourcePreviewPanel`
  - Shows document text/PDF-like preview at highlighted citation only inside a citation verification view/drawer/modal
- `GroundTruthPanel`
  - Legal Authorities / similar cases tabs, search, sort, cards
- `ChatMessageView`
  - Renders user/assistant turns
- `FollowUpComposer`
  - Follow-up question input

### Components to Keep or Reuse

- `UploadZone`
- `DocViewer`, if adapted for citation source preview
- `LegalAuthoritiesPanel`, if restyled/extended into `GroundTruthPanel`
- Existing API helpers, extended with new typed calls

### Components to Demote or Remove as Primary UX

- Current wizard-style `WorkflowPicker`
- Current generic `TaskPicker` shape
- `WorkflowOutput` as findings-left/authorities-right card layout
- Generic `FindingCard` as the primary report renderer

They can remain temporarily during migration, but the Vincent-style complaint flow should become the main Phase 4 path.

## Fixture Data

Add fixture data for the demo complaint.

Suggested path:

- `backend/fixtures/musk_v_altman_complaint.py`
- `frontend` should not hardcode legal content except presentation labels; it should receive fixture data from backend.

Fixture should include:

- document metadata
- parties
- task list
- structured report sections
- report tables
- citation map
- authority/similar-case results

The actual PDF should live in a stable repo path if licensing and size are acceptable, for example:

- `data/demo/musk-v-altman-openai-complaint-sf.pdf`

If the PDF cannot be committed, document the expected local path and make the demo button disabled with a clear setup message until present.

## Tests and Verification

Backend tests:

- Demo endpoint loads the bundled complaint and returns `fixture_available=true`.
- `/workflow/{doc_id}` returns demo parties and tasks for the demo complaint.
- Other uploaded file in fixture mode does not return Musk v. Altman report content.
- `/analysis/report` returns structured report with citations for the demo complaint.
- Every fixture citation resolves to a source page and quote.
- Existing page-span/source_page tests still pass.

Frontend build verification:

- `cd frontend; npm run build`

Frontend behavior checks:

- Demo complaint path shows task grid and party selector.
- Non-demo upload in fixture mode shows limited-mode message instead of fake Musk results.
- Selecting tasks and parties renders report output.
- Hovering citation shows source tooltip.
- Clicking citation highlights or opens source preview.
- Right panel shows authority tabs and cards.

Optional later tests:

- Add frontend component tests only if the project already has a test harness. Do not add new frontend test dependencies unless explicitly approved.

## Implementation Order

1. Add backend types and fixture provider interfaces.
2. Add demo complaint loading endpoint and fixture workflow response.
3. Add structured report endpoint for demo complaint.
4. Add/extend authority fixture results for similar cases and legal authorities.
5. Add frontend API types and calls.
6. Build Page 1 `ComplaintEntry` with upload-or-demo options.
7. Build Page 2 `ComplaintSetup` task grid and represented-party selector.
8. Build Page 3 `ComplaintChatWorkspace` with initial assistant report turn.
9. Build `AnalysisReportView` with inline citations for assistant report messages.
10. Implement fixture-backed follow-up chat contracts and UI.
11. Implement citation hover and click-to-source verification view. Do not render `SourcePreviewPanel` permanently under the chat transcript.
12. Implement/restyle right `GroundTruthPanel`.
13. Keep current backend grounding tests passing.
14. Run backend targeted tests and frontend build.
15. Update planning docs only after human review confirms the new workflow matches the target.

## Acceptance Criteria

- The app supports an **Analyze a Complaint** demo path using `musk-v-altman-openai-complaint-sf.pdf`.
- The app has three distinct UI pages: document entry, workflow setup, and grounded chat workspace.
- The setup page does not show the report/chat/authorities workspace.
- The workspace page does not keep the full task grid and represented-party selector expanded above the answer.
- The demo path shows Vincent-style task buttons and extracted party chips.
- Fixture mode never applies Musk v. Altman hardcoded report content to an unrelated uploaded document.
- The initial assistant response is a structured legal report with inline citations, not a list of generic finding cards.
- The user can ask at least fixture-backed follow-up questions in the chat workspace.
- Hovering a citation shows source quote/page metadata.
- Clicking a citation opens a source verification view/drawer/modal and highlights the cited span where offsets are available.
- The source preview is not permanently visible under the assistant answer/chat transcript.
- The right panel shows legal authorities/similar cases with tabs, search/sort UI, quote blocks, and grounded summaries.
- Provider contracts allow future LLM mode with no frontend contract rewrite.
- Existing extractor/verifier/page citation tests continue to pass.

## Non-Goals

- Do not implement real CourtListener-scale docket ingestion in this plan.
- Do not claim 975 million dockets or 38 state courts.
- Do not show hardcoded Musk v. Altman analysis for arbitrary uploaded files.
- Do not add authentication, persistence, billing, or multi-user storage.
- Do not remove useful backend grounding infrastructure from earlier phases.
