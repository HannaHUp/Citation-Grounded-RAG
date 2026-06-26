# Phase 3: Legal Authorities RAG Panel - Context

**Gathered:** 2026-06-26
**Status:** Ready for planning
**Mode:** Auto-discussed from roadmap/project requirements

<domain>

## Phase Boundary

Phase 3 delivers Surface B: a Legal Authorities panel that can be triggered from an existing finding and returns relevant legal authorities from a small real local corpus. The phase includes corpus ingestion, local vector retrieval, grounded authority summaries, deterministic verification against authority chunks, visible cosine-derived relevance, real source links, and a tabbed panel for Cases, Statutes & Regulations, and Secondary sources.

This phase does not include the Phase 4 workflow shell, party-selection flow, landing/task picker, page-number citations for uploaded documents, auth, persistence, multi-jurisdiction coverage, judge analytics, or a production-scale corpus.

</domain>

<decisions>

## Implementation Decisions

### Corpus and Ingestion
- Use a small real US legal corpus suitable for an MVP demo, not a broad proprietary corpus.
- Include CourtListener-sourced cases and enough statutes/regulations/secondary source material to populate the required tabs.
- Ingestion must support checkpoint/resume so interrupted runs can continue without starting over.
- Prefer simple, inspectable local storage for the corpus and embeddings over production database complexity.

### Retrieval and Relevance
- Authority lookup is triggered from an existing finding or its associated legal question/context.
- Retrieval returns top-k local vector matches grouped into Cases, Statutes & Regulations, and Secondary sources.
- Relevance percentage must be derived from cosine similarity or the retrieval score normalization, never from LLM text.
- The UI should expose relevance per authority entry so users can compare why entries ranked highly.

### Grounded Authority Summaries
- Each authority summary must use the same product rule as Surface A: generated text is useful, but quoted support is what can be verified.
- The verify guard for authority summaries points at the retrieved corpus chunk and performs deterministic exact quote matching.
- Verified and unverified authority summaries both remain visible, using the same ✓/⚠ language and behavior established in earlier phases.
- Verbatim quote blocks are first-class UI content, not footnotes hidden behind hover-only affordances.

### Panel Experience
- Add the Legal Authorities panel as an adjacent Surface B experience to the existing two-pane output, without redesigning the full app shell.
- Use tabs for Cases, Statutes & Regulations, and Secondary sources.
- Each authority entry should show title/name, source type, relevance %, AI summary, verification badge, verbatim quote block, and real source URL.
- Empty and loading states should be practical: explain when no authority results exist, when ingestion has not run, or when retrieval is still loading.

### Claude's Discretion
- Planner may choose the specific local vector/index implementation that best fits the current stack, provided offsets/quotes remain inspectable and tests can prove retrieval and verification behavior.
- Planner may split the phase into backend and frontend waves, with ingestion/retrieval before panel wiring.
- Planner may define a minimal seed corpus for demos if the source and resume behavior are real.

</decisions>

<specifics>

## Specific Ideas

- Keep the core message consistent with the project: the generated legal summary can be wrong, but the quoted support and verification badge must be inspectable.
- Treat Phase 3 as the point where vector storage becomes justified because a corpus now exists.
- CourtListener API rate limits and source formats are a known concern from STATE.md and should be checked early before committing to ingestion details.
- Preserve the one-engine-many-profiles lesson from Phase 2: add authority behavior without destabilizing the existing document findings pipeline.

</specifics>

<deferred>

## Deferred Ideas

- Vincent-style workflow shell, landing picker, task picker, party selector, and polished final two-pane workflow are Phase 4.
- Page-number citations for uploaded documents are Phase 4.
- Multi-jurisdiction or large-scale corpus coverage remains out of scope.
- Auth, user accounts, and persistent user document storage remain deferred until there is a second user.
- Fuzzy quote matching remains deferred until exact-match failure rates justify it.

</deferred>

---

*Phase: 03-legal-authorities-rag-panel*
*Context gathered: 2026-06-26*
