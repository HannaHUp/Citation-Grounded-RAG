---
phase: 04-vincent-style-workflow-shell
plan: 02
subsystem: backend-analysis
tags: [fastapi, pydantic, llm-prompt, perspective, tdd]

requires:
  - phase: 04-vincent-style-workflow-shell
    provides: extractor-owned page spans and verified source_page metadata from 04-01
provides:
  - Validated /analyze perspective contract for plaintiff, defendant, and neutral
  - Perspective prompt framing prepended to document analysis prompts
  - Regression coverage that offsets remain excluded and the engine has no profile_id branches
affects: [04-03, complaint-workflow, frontend-perspective-selector]

tech-stack:
  added: []
  patterns:
    - "Perspective is request-level prompt context, not a profile-specific engine branch."
    - "FastAPI/Pydantic rejects unsupported perspective values before run_llm executes."

key-files:
  created:
    - .planning/phases/04-vincent-style-workflow-shell/04-02-SUMMARY.md
  modified:
    - backend/main.py
    - backend/services/llm_finding.py
    - tests/test_engine.py
    - tests/test_upload.py
    - .planning/STATE.md

key-decisions:
  - "Perspective remains outside FINDINGS_SCHEMA and is not model-generated."
  - "Perspective framing is prepended to the user message and uses generic document text wording."
  - "ENGINE-04 remains protected by static no-profile-branch coverage."

patterns-established:
  - "Additive /analyze fields are validated on AnalyzeRequest and passed through to run_llm."
  - "run_llm accepts optional prompt context without changing stub finding verification."

duration: ~25 min
completed: 2026-06-27
---

# Phase 04 Plan 02: Perspective Prompt Framing Summary

**Plaintiff, defendant, and neutral perspectives now flow through `/analyze` into the LLM prompt as framing context while the analysis engine stays profile-agnostic.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-06-27T20:56:40Z
- **Completed:** 2026-06-27T21:00:37Z for GREEN commit; documentation completed afterward
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `AnalyzeRequest.perspective` as an optional `Literal["plaintiff", "defendant", "neutral"]`.
- Passed the validated perspective into `run_llm`.
- Added `_perspective_context()` and prepended concise plaintiff, defendant, and neutral framing before the document text prompt.
- Changed the generic prompt wording from contract text to document text.
- Added tests proving perspective reaches the prompt, offsets remain excluded, invalid values are rejected, and no `profile_id` branch was introduced.

## TDD Evidence

### RED

Command:

```powershell
uv run pytest tests\test_engine.py tests\test_upload.py
```

Result: expected failure, 6 failed and 4 passed. Failures were for missing perspective behavior only:

- Prompt still said `contract text` instead of `document text`.
- `run_llm()` rejected the new `perspective=` keyword.
- `/analyze` ignored valid perspective values instead of passing them to `run_llm`.
- Unsupported perspective values were accepted instead of rejected by FastAPI/Pydantic.

Committed as `d6ecb1a`.

### GREEN

Targeted command:

```powershell
uv run pytest tests\test_engine.py tests\test_upload.py
```

Result: 10 passed.

Full command:

```powershell
uv run pytest
```

Result: 41 passed.

Static branch check:

```powershell
rg "if\s+(profile\.)?profile_id\s*==" backend/services/llm_finding.py
```

Result: no matches.

Committed as `915298f`.

## Task Commits

1. **Task 1: RED tests for perspective API and prompt wiring** - `d6ecb1a` (test)
2. **Task 2: GREEN implementation for prompt perspective** - `915298f` (feat)

**Plan metadata:** pending final docs commit.

## Files Created/Modified

- `tests/test_engine.py` - Added document-text prompt coverage plus plaintiff, defendant, and neutral prompt-context tests that also assert offsets stay out of the LLM payload.
- `tests/test_upload.py` - Added `/analyze` perspective pass-through and invalid-value validation tests.
- `backend/main.py` - Added validated optional perspective to `AnalyzeRequest` and passed it into `run_llm`.
- `backend/services/llm_finding.py` - Added optional perspective support and `_perspective_context()` without adding profile-specific branches or schema fields.
- `.planning/STATE.md` - Updated current position for 04-03 readiness.

## Decisions Made

- Perspective is prompt context only. It is not stored on findings, not added to `FINDINGS_SCHEMA`, and not inferred from `profile_id`.
- `None` perspective keeps the existing generic document-analysis behavior except for the wording change to document text.
- Invalid perspectives are rejected at the request model boundary.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The worktree already had unrelated dirty edits in `backend/main.py`, `backend/services/llm_finding.py`, `.planning/STATE.md`, and other files. Implementation staging was selective so the 04-02 feature commit excluded the pre-existing backend hunks.
- PowerShell clock commands hit a sandbox runner error, so summary timing uses git commit timestamps.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Phase 04 Plan 03. The frontend workflow shell can now send `plaintiff`, `defendant`, or `neutral` to `/analyze`, and the backend will validate and carry that framing into the LLM prompt.

## Self-Check: PASSED

Files confirmed on disk:

- `.planning/phases/04-vincent-style-workflow-shell/04-02-SUMMARY.md`
- `tests/test_engine.py`
- `tests/test_upload.py`
- `backend/main.py`
- `backend/services/llm_finding.py`
- `.planning/STATE.md`

Commits confirmed in git log:

- `d6ecb1a` - `test(04-02): add failing tests for perspective framing`
- `915298f` - `feat(04-02): add perspective prompt framing`

Verification confirmed:

- RED targeted suite failed before implementation for missing perspective behavior.
- Targeted GREEN suite passed: 10 tests.
- Full suite passed: 41 tests.
- Static no-profile-branch search returned no matches.

---
*Phase: 04-vincent-style-workflow-shell*
*Completed: 2026-06-27*
