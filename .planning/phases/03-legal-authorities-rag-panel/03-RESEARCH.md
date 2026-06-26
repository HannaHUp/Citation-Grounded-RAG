# Phase 03: Legal Authorities RAG Panel - Research

**Researched:** 2026-06-26
**Domain:** Legal corpus ingestion, local retrieval, grounded authority summaries, and React panel UI
**Confidence:** MEDIUM

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Use a small real US legal corpus suitable for an MVP demo, not a broad proprietary corpus.
- Include CourtListener-sourced cases and enough statutes/regulations/secondary source material to populate the required tabs.
- Ingestion must support checkpoint/resume so interrupted runs can continue without starting over.
- Prefer simple, inspectable local storage for the corpus and embeddings over production database complexity.
- Authority lookup is triggered from an existing finding or its associated legal question/context.
- Retrieval returns top-k local vector matches grouped into Cases, Statutes & Regulations, and Secondary sources.
- Relevance percentage must be derived from cosine similarity or the retrieval score normalization, never from LLM text.
- The UI should expose relevance per authority entry so users can compare why entries ranked highly.
- Each authority summary must use the same product rule as Surface A: generated text is useful, but quoted support is what can be verified.
- The verify guard for authority summaries points at the retrieved corpus chunk and performs deterministic exact quote matching.
- Verified and unverified authority summaries both remain visible.
- Verbatim quote blocks are first-class UI content, not footnotes hidden behind hover-only affordances.
- Add the Legal Authorities panel as an adjacent Surface B experience to the existing two-pane output, without redesigning the full app shell.
- Use tabs for Cases, Statutes & Regulations, and Secondary sources.
- Each authority entry should show title/name, source type, relevance %, AI summary, verification badge, verbatim quote block, and real source URL.
- Empty and loading states should be practical: explain when no authority results exist, when ingestion has not run, or when retrieval is still loading.

### Claude's Discretion
- Planner may choose the specific local vector/index implementation that best fits the current stack, provided offsets/quotes remain inspectable and tests can prove retrieval and verification behavior.
- Planner may split the phase into backend and frontend waves, with ingestion/retrieval before panel wiring.
- Planner may define a minimal seed corpus for demos if the source and resume behavior are real.

### Deferred Ideas (OUT OF SCOPE)
- Vincent-style workflow shell, landing picker, task picker, party selector, and polished final two-pane workflow are Phase 4.
- Page-number citations for uploaded documents are Phase 4.
- Multi-jurisdiction or large-scale corpus coverage remains out of scope.
- Auth, user accounts, and persistent user document storage remain deferred until there is a second user.
- Fuzzy quote matching remains deferred until exact-match failure rates justify it.

</user_constraints>

## Summary

The codebase already has a hardcoded `backend/services/authorities.py`, an `/authorities` endpoint, `tests/test_authorities.py`, and a React `LegalAuthoritiesPanel`. Phase 3 should replace the token-overlap stub with a real, inspectable local corpus and cosine-scored retrieval while preserving the existing endpoint shape where possible.

For this MVP, the lowest-risk local vector store is persisted JSONL chunks plus a scikit-learn TF-IDF matrix and `cosine_similarity`. This satisfies cosine-derived relevance, avoids heavyweight model downloads during execution, keeps vectors inspectable, and is easy to test deterministically. Sentence Transformers is a better semantic-search path later, but it adds PyTorch/model download cost and more setup risk than this phase needs.

**Primary recommendation:** implement a file-backed legal corpus under `backend/data/authorities/`, ingest CourtListener cases plus small seeded statutes/secondary records, index with `TfidfVectorizer`, rank by `cosine_similarity`, then run authority summaries through the existing deterministic quote verifier pattern.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scikit-learn | pin in `backend/requirements.txt` | `TfidfVectorizer` + `cosine_similarity` for local vectors | Official docs define TF-IDF feature matrices and cosine similarity; deterministic and testable for a small MVP corpus |
| requests or urllib | standard/simple dependency | CourtListener ingestion HTTP calls | CourtListener REST root exposes `/api/rest/v4/search/`, `/opinions/`, and related resources |
| FastAPI | existing | `/authorities` and ingestion/status endpoints | Already used by backend |
| React | existing | tabbed panel and authority cards | Already used by frontend |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| joblib | transitive with scikit-learn | persist vectorizer/matrix | Use if pickling the vectorizer is simpler than rebuilding |
| pathlib/json | stdlib | checkpoint and corpus files | Use for inspectable corpus metadata |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| scikit-learn TF-IDF | Sentence Transformers | Better semantic search, but adds heavier dependencies and model download/runtime uncertainty |
| file-backed JSONL | SQLite | More query flexibility, but persistence/database complexity is explicitly discouraged for this MVP |
| CourtListener-only corpus | CourtListener + seeded statutes/secondary URLs | CourtListener covers cases; statutes and secondary sources need seeded records to satisfy all tabs |

## Architecture Patterns

### Recommended Project Structure

```text
backend/
  data/authorities/
    corpus.jsonl
    ingest_state.json
    tfidf.joblib
  scripts/
    ingest_authorities.py
  services/
    authorities.py
    authority_ingest.py
    authority_summary.py
tests/
  test_authority_ingest.py
  test_authorities.py
frontend/src/components/
  LegalAuthoritiesPanel.tsx
```

### Pattern 1: Checkpointed Ingestion

**What:** write each normalized authority chunk to JSONL and record cursor/page/source progress in `ingest_state.json`.
**When to use:** CourtListener API calls may be interrupted or rate-limited.
**Implementation shape:** idempotent `ingest_authorities(max_records=...)` skips authority IDs already in corpus, writes temp files then atomically replaces state.

### Pattern 2: Exact Quote Verification for Authority Chunks

**What:** authority summary output includes a quote, and verification is `source_text.find(quote) != -1`.
**When to use:** every AI-generated authority summary.
**Implementation shape:** reuse the Surface A verifier concept, but point it at `AuthorityChunk.source_text` rather than uploaded document text.

### Pattern 3: Score Normalization at Retrieval Boundary

**What:** store raw cosine score and expose relevance as an integer percent derived from that score.
**When to use:** API response construction only.
**Implementation shape:** `relevance = round(max(0.0, min(1.0, cosine_score)) * 100)`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TF-IDF feature extraction | custom token weighting | `sklearn.feature_extraction.text.TfidfVectorizer` | Official implementation handles vocabulary, IDF, normalization, sparse matrices |
| Cosine scoring | ad hoc overlap scoring | `sklearn.metrics.pairwise.cosine_similarity` | Requirement explicitly needs cosine-derived relevance |
| Legal source retrieval API | scraping HTML pages | CourtListener REST v4 search/opinion data for cases | Official API exposes structured search results |
| Verification | LLM self-report | deterministic exact string matching | Project core value depends on non-AI verification |

## Common Pitfalls

### Pitfall 1: Treating BM25/API Search as the Final Relevance Score

**What goes wrong:** CourtListener search result score or token overlap is shown as final "relevance %".
**Why it happens:** easier than building local vectors.
**How to avoid:** CourtListener is ingestion/source discovery only; user-facing relevance comes from local cosine similarity.
**Warning signs:** code maps API `meta.score.bm25` directly into `relevance`.

### Pitfall 2: Losing Verbatim Source Text

**What goes wrong:** summaries cannot be verified because only cleaned snippets were stored.
**Why it happens:** ingestion normalizes whitespace or truncates text before persisting.
**How to avoid:** persist `source_text` exactly as the verifier will search it; quote blocks must come from that text.
**Warning signs:** tests do not assert `quote in source_text`.

### Pitfall 3: One Empty Tab Breaks the Demo

**What goes wrong:** cases work but statutes/secondary tabs are empty.
**Why it happens:** CourtListener is case-focused and the phase also requires statutes/regulations/secondary sources.
**How to avoid:** seed a few real statute/regulation and secondary records with real URLs in the corpus.

### Pitfall 4: Replanning the App Shell

**What goes wrong:** Phase 3 grows into the Phase 4 workflow shell.
**Why it happens:** legal authorities naturally belong in the final two-pane UX.
**How to avoid:** keep this phase to the existing two-pane app and authorities panel.

## Code Examples

### TF-IDF and Cosine Retrieval

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

texts = [chunk.source_text for chunk in chunks]
vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
matrix = vectorizer.fit_transform(texts)
query_vec = vectorizer.transform([query])
scores = cosine_similarity(query_vec, matrix)[0]
```

### Checkpoint State Shape

```json
{
  "courtlistener": {
    "next_url": "https://www.courtlistener.com/api/rest/v4/search/?...",
    "completed": false,
    "records_written": 25
  },
  "seeded_sources": ["15-usc-18", "ftc-merger-guidelines"]
}
```

## Sources

### Primary (HIGH confidence)
- CourtListener REST API root: https://www.courtlistener.com/api/rest/v4/ shows `search`, `clusters`, `opinions`, and other resources.
- CourtListener search endpoint: https://www.courtlistener.com/api/rest/v4/search/ returns paginated search results with `count`, `next`, `results`, case metadata, nested opinions, snippets, and source URLs.
- scikit-learn `TfidfVectorizer`: https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html documents conversion of raw documents into TF-IDF feature matrices.
- scikit-learn `cosine_similarity`: https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html defines cosine similarity as normalized dot product.
- Sentence Transformers semantic search docs: https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html documents embedding corpus entries and using cosine semantic search; useful later if TF-IDF is not enough.

### Local Code Evidence (HIGH confidence)
- `backend/services/authorities.py` currently uses hardcoded corpus and token overlap relevance.
- `tests/test_authorities.py` already expects grounded quotes, tab-ready source types, and `/authorities`.
- `frontend/src/components/LegalAuthoritiesPanel.tsx` already implements tabs and authority cards.

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - official docs verified, but exact dependency install/runtime not tested in this planning turn.
- Architecture: HIGH - matches existing backend/frontend structure.
- Pitfalls: MEDIUM - based on project constraints and API shape.

**Research date:** 2026-06-26
**Valid until:** 2026-07-26 for scikit-learn patterns; re-check CourtListener API behavior before relying on live ingestion.
