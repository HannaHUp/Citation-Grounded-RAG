---
phase: 02-second-profile-auto-detect
plan: 02
subsystem: frontend
tags: [profile-as-data, doc-type-control, override-ui, react-state]
dependency_graph:
  requires: [02-01]
  provides: [DocTypeControl, selectedProfileId state, profile-aware analyze call]
  affects: [frontend/src/types.ts, frontend/src/api.ts, frontend/src/App.tsx, frontend/src/components/FindingsPanel.tsx, frontend/src/styles.css]
tech_stack:
  added: []
  patterns: [profile-aware React state, conditional JSX on nullable state, CSS token reuse]
key_files:
  created: []
  modified:
    - frontend/src/types.ts
    - frontend/src/api.ts
    - frontend/src/App.tsx
    - frontend/src/components/FindingsPanel.tsx
    - frontend/src/styles.css
decisions:
  - "DocTypeControl renders inside FindingsPanel (not App.tsx inline) — props passed down, keeps App.tsx clean"
  - "doc-type-control strip given padding + border-bottom to visually separate from the sticky header row"
  - ".doc-type-control placed after .findings-header div, not inside it — avoids breaking the flex justify-content:space-between layout"
metrics:
  duration: ~10min
  completed: 2026-06-26
  tasks_completed: 2
  files_changed: 5
---

# Phase 2 Plan 2: Second Profile + Auto-Detect (Frontend) Summary

**One-liner:** UploadResponse type extended with detected_doc_type + profile_id; analyze() drops hardcoded "contract_risk"; DocTypeControl (detected label + 2-button override) and profile-aware legend hint wired into FindingsPanel; build green.

## What Was Built

### Task 1: Extend types + analyze() + App state wiring

`frontend/src/types.ts` — UploadResponse extended with:
- `detected_doc_type: "contract" | "complaint"`
- `profile_id: string`

`frontend/src/api.ts` — analyze() signature changed from `analyze(docId: string)` to `analyze(docId: string, profileId: string)`; body uses `profile_id: profileId` (hardcoded `"contract_risk"` removed — D-08).

`frontend/src/App.tsx` — two new state variables:
- `detectedDocType` (`"contract" | "complaint" | null`) — initializes null, set to `res.detected_doc_type` on successful upload, reset to null before the next upload attempt
- `selectedProfileId` (`string`) — initializes `"contract_risk"`, seeded from `res.profile_id` on upload; `handleAnalyze` passes it to `analyze(docId, selectedProfileId)`

### Task 2: DocTypeControl UI + profile-aware legend hint + CSS

`frontend/src/components/FindingsPanel.tsx` — extended with three new props (`detectedDocType`, `selectedProfileId`, `onSelectProfile`):
- DocTypeControl rendered immediately after `.findings-header` when `detectedDocType !== null`; anatomy: `.doc-type-control__label` (Detected: **Contract|Complaint**) + `.doc-type-control__buttons` (two `button.doc-type-btn` with `type="button"`, `aria-pressed`, `.doc-type-btn--active` on the currently selected profile)
- Legend hint: `{selectedProfileId === "complaint_claims" ? "strength of the legal claim" : "how serious the legal exposure is"}`

`frontend/src/App.tsx` — passes `detectedDocType`, `selectedProfileId`, `onSelectProfile={setSelectedProfileId}` to FindingsPanel.

`frontend/src/styles.css` — `.doc-type-control`, `.doc-type-control__label`, `.doc-type-control__label strong`, `.doc-type-control__buttons`, `.doc-type-btn`, `.doc-type-btn--active`, `.doc-type-btn:not(.doc-type-btn--active):hover` rules appended after `.badge-explainer`. All values use existing `:root` tokens; only hardcodes are `#ffffff` (active button text) and `#bcc6d6` (inactive hover border) — both per UI-SPEC.

## PROF-02/PROF-03 Proof

- PROF-03: `detectedDocType` label + 2-button override visible after upload, hidden pre-upload
- PROF-02: `selectedProfileId` is what `/analyze` sends; override is local React state with no backend round-trip (D-09)
- D-08: `grep 'contract_risk' frontend/src/api.ts` returns 0 lines — hardcode gone

## Checkpoint: human-verify (auto-approved under --auto)

The Task 3 human-verify checkpoint was auto-approved. Manual verification steps for the user:

1. Ensure `musk-v-altman-openai-complaint-sf.pdf` is present in the repo root (it is — confirmed by `git status` showing the file untracked).
2. Start the backend in stub mode: `GROUNDING_STUB=1 uvicorn backend.main:app --port 8010`
3. Start the frontend: `cd frontend && npm run dev`
4. Upload `musk-v-altman-openai-complaint-sf.pdf`. Expect the header area below "Findings" to show "Detected: **Complaint**" with the Complaint button active (blue fill).
5. Click "Analyze Document". Expect claim-shaped findings with ✓/⚠ badges; the severity legend hint should read "strength of the legal claim".
6. Click the "Contract" override button. It should turn blue; Complaint should become inactive. (Re-analyze would now run `contract_risk`.)
7. Upload the Microsoft–LinkedIn contract DOCX (Phase-1 fixture). Expect "Detected: **Contract**", risk findings on Analyze, legend hint "how serious the legal exposure is".
8. Confirm ✓ and at least one ⚠ badge appear and click-to-highlight scrolls the doc pane (Phase-1 grounding unchanged).

## Deviations from Plan

### Placement adjustment

**[Rule 2 - Layout]** The plan specified DocTypeControl "below the 'Findings' heading and above the 'Analyze Document' button" — i.e., inside `.findings-header`. The `.findings-header` uses `display: flex; justify-content: space-between` between the "Findings" span and the Analyze button; inserting a third flex child would break the two-item layout. The control was placed **after** the `.findings-header` div as a sibling, with its own `padding + border-bottom` to match the visual spec. The UI-SPEC diagram shows it on a second row below the header, which this placement achieves correctly.

## Known Stubs

None. The DocTypeControl renders real detected type from the `/upload` response. The GROUNDING_STUB path (backend, D-10) is intentional offline scaffolding documented in Plan 01.

## Threat Flags

No new network endpoints, auth paths, or file access patterns introduced. The client now sends a user-selected `profile_id` to `/analyze` (T-02-04 in plan threat register); the backend already rejects unknown profile IDs via `get_profile()` HTTP 400 — no mitigation gap.

## Self-Check: PASSED

Files modified:
- frontend/src/types.ts: FOUND (detected_doc_type present)
- frontend/src/api.ts: FOUND (profileId param present, "contract_risk" hardcode absent)
- frontend/src/App.tsx: FOUND (selectedProfileId + detectedDocType state + analyze(docId, selectedProfileId))
- frontend/src/components/FindingsPanel.tsx: FOUND (doc-type-control, doc-type-btn--active, aria-pressed, complaint_claims hint)
- frontend/src/styles.css: FOUND (.doc-type-btn, .doc-type-btn--active, var(--color-accent))

Commits:
- 844bb19: feat(02-02) Task 1 — FOUND
- 68bff6d: feat(02-02) Task 2 — FOUND
