---
type: session
status: verified
date: 2026-10-19
tags: [sessions, identity, t208]
---
# Optional local identity claim

## Task and scope
Bounded **T208** slice: optional local identity claiming of an anonymous
tab-bearer `owner_hash`. Not production auth, matters, OAuth, or collaboration.

## Changes
- Anonymous `POST /sessions` and owner-scoped `/analyses` unchanged.
- `POST /api/v1/identities` binds the current owner to a username + hashed secret.
- `POST /api/v1/identities/login` issues a recovery bearer resolved to that owner.
- `GET /api/v1/identities/me` reports the bound username or 404.
- Local Alembic `0007_local_identities` (`down_revision` `0006_claim_corrections`).
  Hosted Neon is not migrated.
- OpenAPI exported; `schema.d.ts` regenerated.

## Verification
- Ruff on identity, admission, models, repository, contracts, migration and tests: passed.
- Parent re-run: ruff plus pytest `test_identity`, `test_intake`,
  `test_readiness`, `test_contracts`, `test_persistence`: 120 passed.

## Checks not run
- Hosted Neon `0007`.
- Web UI for claim/login.
- Production OAuth, email, matters/history, reviewer roles.

## Blockers and next step
Remaining T208 work is saved matters/history and production authorization.
T208 stays open on [[TODO]]. Hosted Neon is not at `0007`.

## Related
[[TODO]] T208 · [[apps/api/src/filingguard/modules/identity/README]] ·
[[docs/decisions/ADR-016 - Optional local identity claim]]

[[docs/sessions/Index]] | [[TODO]]
