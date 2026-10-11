---
type: session
status: completed
date: 2026-09-30
tags: [sessions, analysis, intake]
---
# Review job foundation

## Task and scope
The user accepted the initial homepage direction and asked to continue P0/2, P0/3
and clarify P0/4. T009-T015 and T017/T019-T021 were already checked. T016 actual
demo replay, T018 full result/report/graph ownership and T022 outgoing masking
remain open. This session advances T023; it does not complete the legal engines.

## Changes
Added an owner-scoped `/analyses/{id}/run` handoff and `/status` read. A prepared
live document is atomically queued before a 202 response. One in-process worker
shares the admission slot with preparation and saves stage transitions in separate
transactions. Duplicate review starts and deletion during an active job return 409;
another session's ID returns 404. A failed stage preserves prior commits, marks
later stages interrupted and exposes only a generic reason. The runtime owns worker
shutdown. The normal app registers no legal runners, reports
`legal_analysis_enabled=false`, and responds 503 to run requests. Demo execution
still requires T016's stronger replay gate. The homepage Run review button remains
disabled. Prepared-document status now reads from the saved analysis row, and its
UI notice changes with that status.

## Verification
- Full API suite: 265 passed, two host-dependent skips, four warnings.
- Synthetic-runner integration verifies 202 after queueing, owner isolation,
  duplicate/busy/delete conflicts, shared slot duration, terminal stage persistence,
  prior-stage preservation and exception-text suppression.
- Frontend: 17 tests passed; TypeScript, backend/frontend lint and production build
  passed. OpenAPI export and TypeScript generation passed; `git diff --check` passed.
- Vite/Vitest config resolution failed under the restricted Windows sandbox, then
  both passed outside that restriction. Existing Three.js chunk-size warning remains.

Not run: browser end-to-end checks for the new route because no production stage
runner is registered or UI action enabled; provider calls, hosted migration/deploy,
Linux/physical-device checks. This is local development, not a release gate pass.

## Blockers and next step
T023 remains unchecked. Register and verify real stage engines incrementally with
bounded timeouts (T024), partial-result/restart semantics (T025) and truthful UI
polling (T026). Then complete T016 replay and T018 ownership across result surfaces.
T022 awaits outgoing semantic-provider adapters. Public intake remains disabled.

## Related
[[docs/sessions/Index]] | [[TODO]] |
[[apps/api/src/filingguard/modules/analyses/README]] |
[[apps/api/src/filingguard/modules/documents/README]] |
[[apps/web/src/features/intake/README]] |
[[contracts/README]] | [[docs/decisions/ADR-007 - Private preparation boundary]]
