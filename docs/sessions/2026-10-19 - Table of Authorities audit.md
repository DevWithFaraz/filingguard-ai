---
type: session
status: verified
date: 2026-10-19
tags: [sessions, table-of-authorities, p2, t201]
---
# Table of Authorities audit

## Task and scope
Completed **T201** (FR-280 through FR-284). FilingGuard now detects a Table of
Authorities section, compares comparable reporter identities with the body both
ways, records listed page leaders when present, and treats a missing table as
unevaluated rather than a pass.

## Changes
- Added `table_of_authorities` review stage after citation extraction.
- `service.py` detects standalone TOA/table-of-cases/index headings, ends the
  section at a later known heading, and compares Eyecite full-case/law/journal
  and reporter-candidate identities.
- Missing body authorities are medium findings; extra table entries and
  non-overlapping listed pages are low findings. No table is skipped.
- Scoring, reports, red-team, grounded Q&A, and results filters expose
  `table_of_authorities` as its own category.
- Migration `0005_table_of_authorities` extends the findings type check. Hosted
  Neon remains at `0004_citation_extraction` until an explicit upgrade.

## Verification
- `ruff check` on the changed API modules passed.
- Focused API suites (TOA, contracts, reports, orchestrator, demo, readiness,
  persistence) passed (136).
- Full API pytest: 794 passed, 2 skipped.
- Frontend: 65 tests, ESLint, TypeScript, OpenAPI export and generated
  `schema.d.ts`.

## Checks not run
- Hosted Neon migration to `0005`.
- Physical-device or live hosted TOA review.
- Expert legal validation of table completeness.

## Blockers and next step
None for T201. Next ordered task: T202 statute/regulation verification.

## Related
[[TODO]] T201 · [[apps/api/src/filingguard/modules/table_of_authorities/README]]
· [[FilingGuard_AI_SRS]] FR-280–FR-284

[[docs/sessions/Index]] | [[TODO]]
