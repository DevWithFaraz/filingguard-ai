---
type: session
status: verified
date: 2026-10-19
tags: [sessions, claims, p2, t206]
---
# Manual claim corrections

## Task and scope
Implemented **T206** (FR-065): owner-scoped manual claim corrections with history
and a stale-proposition flag. Original extraction is not rewritten.

## Changes
- `Claim.correction_history` JSON via local Alembic `0006_claim_corrections`.
- `POST /api/v1/analyses/{analysis_id}/claims/{claim_id}/corrections`.
- Results expose original `text`, `corrected_text`, history, and
  `propositions_stale`. Affected links reset to `not_run`.
- In-place proposition-only re-run is not available. Full `POST /rerun` clones a
  new analysis and re-extracts claims without the correction.
- Results UI labels original vs user-corrected extraction.

## Verification
- Ruff on changed API modules passed.
- Focused API tests: 143 passed (claim corrections, contracts, propositions,
  claims pipeline, persistence, readiness, saved results).
- Web: ESLint, TypeScript, 67 Vitest tests passed.
- OpenAPI exported and `schema.d.ts` regenerated.

## Checks not run
- Hosted Neon migration to `0006`.
- Live Groq re-review of a corrected claim.
- Physical-device/screen-reader pass on the correction form.

## Blockers and next step
None for T206 local persist/history. Next ordered task remains T207 unless the
user changes order. TODO.md was not edited in this session.

## Related
[[TODO]] T206 · [[apps/api/src/filingguard/modules/claim_corrections/README]]
· [[FilingGuard_AI_SRS]] FR-065

[[docs/sessions/Index]] | [[TODO]]
