---
phase: 02-second-profile-auto-detect
plan: 01
subsystem: backend
tags: [profile-as-data, classify, forced-tool-call, tdd]
dependency_graph:
  requires: [01-grounding-spine]
  provides: [complaint_claims profile, classify_doc_type, extended /upload response]
  affects: [backend/profiles, backend/services/llm_finding.py, backend/main.py]
tech_stack:
  added: []
  patterns: [forced tool-call pattern mirrored for classify, profile-as-data registry pattern]
key_files:
  created:
    - backend/profiles/complaint_claims.py
    - tests/test_classify.py
  modified:
    - backend/profiles/__init__.py
    - backend/services/llm_finding.py
    - backend/main.py
decisions:
  - "classify_doc_type appended to llm_finding.py (not a new module) — YAGNI, one function, reuses _get_client"
  - "GROUNDING_STUB guard is first line of classify_doc_type — offline demo works without API key"
  - "max_tokens=64 for classify call (enum response only) vs 4096 for findings"
metrics:
  duration: ~15min
  completed: 2026-06-26
  tasks_completed: 2
  files_changed: 5
---

# Phase 2 Plan 1: Second Profile + Auto-Detect (Backend) Summary

**One-liner:** Complaint profile added as pure data (one new file + one registry line); classify_doc_type forced tool-call wired into /upload; PROF-01 proved — zero engine/verifier/schema edits.

## What Was Built

### Task 1: Complaint profile + registry (TDD RED → GREEN)

`backend/profiles/complaint_claims.py` — a direct clone of `contract_risk.py` with claims framing substitutions:
- `COMPLAINT_CLAIMS` AnalysisProfile with `profile_id="complaint_claims"`
- `output_schema=FINDINGS_SCHEMA` — the same object, no copy (D-04 proof)
- `system_prompt` carries the verbatim-quote / no-normalization discipline sentence from `contract_risk.py` (D-06, load-bearing for the verifier's `str.find()`)
- Severity reinterpreted: `high` = core legal claim/theory of liability; `medium` = significant factual allegation; `low` = procedural/jurisdictional

`backend/profiles/__init__.py` — exactly two lines added:
- `from backend.profiles.complaint_claims import COMPLAINT_CLAIMS`
- `COMPLAINT_CLAIMS.profile_id: COMPLAINT_CLAIMS,` in PROFILES dict

### Task 2: classify_doc_type + /upload extension (same TDD cycle)

`backend/services/llm_finding.py` — `classify_doc_type(prefix: str) -> str` appended after `run_llm`:
- GROUNDING_STUB guard is the first statement (returns keyword heuristic, no API call)
- `_get_client()` called inside the function body (never at module level — Pitfall 6)
- `max_tokens=64` — enum-only response, much cheaper than 4096 for findings
- `_CLASSIFY_SCHEMA` + `_DOC_TYPE_TO_PROFILE` module-level constants
- Forced tool-call pattern mirrors `run_llm` exactly

`backend/main.py` — `/upload` extended:
- `classify_doc_type` added to imports
- `classify_doc_type(full_text[:3000])` called after `doc_store[doc_id] = ...`
- Returns `detected_doc_type` + `profile_id` alongside existing `doc_id` + `full_text`
- `/analyze` handler untouched (D-03)

## PROF-01 Proof

`git diff --stat backend/services/verifier.py backend/models.py` shows zero changes. `run_llm` body is unchanged — zero `if profile_id ==` branches added (confirmed by `test_engine_has_no_profile_branch` static check, still passing).

## TDD Gate Compliance

1. RED commit `eae6b69`: `test(02-01): add failing tests for complaint profile + classify_doc_type` — all 4 tests failed with ImportError.
2. GREEN commit `87f3604`: `feat(02-01): add complaint profile, classify_doc_type, and extend /upload` — all 17 tests pass.

## Deviations from Plan

None — plan executed exactly as written. Tasks 1 and 2 share the same TDD cycle (test_classify.py covers both) which is why both implementations were committed together in the GREEN commit.

## Test Results

- `tests/test_classify.py`: 4/4 pass (stub complaint, stub contract, live complaint, profile registry)
- `tests/test_engine.py`: 2/2 pass (no offsets in payload, no profile_id branches — PROF-01 static proof)
- Full suite: 17/17 pass

## Known Stubs

None in the delivered backend code. The GROUNDING_STUB path is intentional offline scaffolding documented in D-10, not a data stub — findings come from `stub_findings.py` which already has Musk v. Altman canned findings (`_PDF` rows).

## Self-Check: PASSED

Files exist:
- backend/profiles/complaint_claims.py: FOUND
- tests/test_classify.py: FOUND
- backend/profiles/__init__.py: modified (COMPLAINT_CLAIMS.profile_id present)
- backend/services/llm_finding.py: modified (classify_doc_type present)
- backend/main.py: modified (detected_doc_type + classify_doc_type call present)

Commits exist:
- eae6b69: test(02-01) RED gate — FOUND
- 87f3604: feat(02-01) GREEN gate — FOUND
