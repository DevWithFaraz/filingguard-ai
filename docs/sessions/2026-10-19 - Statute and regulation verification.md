---
type: session
status: verified
date: 2026-10-19
tags: [sessions, statutes, p2, t202]
---
# Statute and regulation verification

## Task and scope
Implemented **T202** (FR-047) locally: statute/regulation verification as a
separate review stage from CourtListener case citations. Public/synthetic test
data only; no live provider spend.

## Changes
- Added `apps/api/src/filingguard/modules/statutes/` (adapter, service, runner,
  schemas) and unit tests with fake HTTP/catalog responses.
- New `statutes` review stage. Unconfigured source (`STATUTE_SOURCE_URL` unset)
  is unavailable with a reason when law citations exist, not skipped-as-pass.
  Filings with no law citations skip. Findings reuse type `citation`
  (`stage=statutes`); no Neon CHECK migration.
- Law/journal kinds remain unsupported for CourtListener and are never queried
  as cases.
- Scoring adds statutes-stage coverage into the existing citation category.
- Regenerated `contracts/openapi.json` and `apps/web/src/lib/api/schema.d.ts`
  for `StageName.statutes`. Browser results validator accepts nine stages.

## Verification
- `ruff check` on the statutes module and touched API files passed.
- `pytest` `tests/unit/test_statutes.py`, `test_citation_extraction.py`,
  `test_citation_dedup.py`, `test_verified_citation_stage.py`,
  `test_contracts.py`, `test_retention_and_observability.py`: all passed
  (77 in the later combined run; citation-dedup/verified-stage also passed
  earlier).
- OpenAPI export and TypeScript contract generation ran successfully.
- Integration `tests/integration/test_orchestrator.py` passed.

## Checks not run
- Full API pytest and frontend unit/lint/typecheck.
- Live GovInfo/LII or any paid statute API.
- Hosted deploy.

## Blockers and next step
Parent marked T202 after re-running statutes/orchestrator tests (73 passed) and
changing unconfigured-source behavior so no-law-citation filings skip instead of
making every review partial. Next ordered feature task is T205. No live statute
source is configured.

## Related
[[TODO]] T202 · [[apps/api/src/filingguard/modules/statutes/README]]
· [[apps/api/src/filingguard/modules/citations/README]]
· [[FilingGuard_AI_SRS]] FR-047

[[docs/sessions/Index]] | [[TODO]]
