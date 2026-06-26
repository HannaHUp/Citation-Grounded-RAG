# Plan 03-01 Summary: Corpus Ingestion

**Status:** Complete
**Completed:** 2026-06-26

## What Changed

- Added `backend/services/authority_ingest.py` with file-backed authority records, seeded real-source authorities, checkpoint state, idempotent CourtListener ingestion, and corpus read/write helpers.
- Added `backend/scripts/ingest_authorities.py` as a CLI entry point for seeded + CourtListener ingestion.
- Added inspectable seed corpus files under `backend/data/authorities/`.
- Added `AuthorityRecord` to `backend/models.py`.
- Added ingestion tests in `tests/test_authority_ingest.py`.

## Verification

- `uv run pytest tests\test_authority_ingest.py` passed.
- Full backend suite later passed with 24 tests.

## Notes

- CourtListener ingestion is bounded and resumable through `ingest_state.json`.
- Seeded statute, case, and secondary records keep exact quote text inside `source_text`.
