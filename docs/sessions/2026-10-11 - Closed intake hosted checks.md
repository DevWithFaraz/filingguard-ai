---
type: session
status: closed-intake-prerequisites-verified
date: 2026-10-11
tags: [sessions, deployment, database, storage]
---
# Closed intake hosted checks

## Task and scope

[[TODO]] T057. User reports API/frontend Live on `5b37993` with intake/source/
semantic flags false, and requests endpoint verification and migration/storage
checks. The deployment revision is user-reported; public endpoints expose no
independent commit identifier. Solo work, no provider calls or intake enablement.

## Verification

`node scripts/check_hosted_release.mjs` at 16:55 UTC verifies health/capabilities
200, exact frontend-origin CORS, no forbidden-origin allow header and direct
Activity/settings routes 200. Readiness 503 with intake/private_storage/schema
false and cleanup/exact_origins/provider_configuration true. Its nonzero exit is
expected because the probe requires fully enabled readiness; this deployment
remains deliberately closed. It does not certify hosted engine acceptance.

Read-only reviewed sample GET passes at 16:59 UTC: curated-v1, exact local filing
hash, three cached sources, 18 examples, delegated review and execution not_run.
This verifies resource availability, not genuine engine/model output. API requests
to the known private ownership/lease paths and repository source path return 404;
this is bounded route verification, not an exhaustive exposure audit.

`scripts/check_database.py` confirms direct Neon PostgreSQL 17.11 and client TLS.
Schema-only read-only queries find no Alembic revision and zero public tables.
Offline SQL preview targets `0004_citation_extraction`, creates the app tables and
adds columns/indexes; no DROP TABLE/COLUMN or DELETE FROM, wrapped in BEGIN/COMMIT.
Ignored receipts/SQL live under `.runtime`; no credentials/raw filing data in notes.
The hosted schema boolean cannot independently identify Render's database because
readiness only reads an already initialized runtime engine.

## Approved migration

User supplied the Render hostname/database, a masked Neon connection string and
a Connect screenshot showing branch production. Those approved target fields
match local configuration. The initial no-migration instruction was respected
until user explicitly approved applying the prepared migration.

The guarded Alembic upgrade checks exact host/database, TLS, expected release head
and an empty public schema. All four revisions execute within an outer PostgreSQL
transaction using the existing migration connection hook. At 17:21 UTC, the
transaction commits at `0004_citation_extraction`; all 10 application tables are
present, no expected tables missing and no column-set mismatches. An independent
read-only query confirms recorded head equals release head and no migration is
needed. No filing/session inserts or provider requests were performed.
Ignored `.runtime/hosted-migration-receipt.json` records the sanitized outcome.

User again confirms both services Live, all three flags false and homepage
Submission disabled. This is expected, not an intake failure.
Post-migration hosted probe at 17:22 UTC still passes health/capabilities, direct
SPA routes and CORS. Readiness remains 503 with intake/storage/schema false:
storage is unset, so the hosted runtime has not initialized the DB lifecycle.
This does not contradict the independently verified Neon migration head.

## Blockers and next step

User added PRIVATE_STORAGE_DIRECTORY=/tmp/filingguard-private and reports the API
Live again. Read-only hosted probe at 17:41 UTC confirms private_storage,
database_schema, cleanup, exact_origins and provider_configuration all true;
intake_enabled remains false. Health/capabilities and SPA routes remain 200 with
correct CORS. Readiness 503 is now solely due to deliberate disabled intake.
This verifies the existing runtime initialized storage and migrated DB lifecycle.
The three known private/repository path probes still return 404 after storage
initialization (17:42 UTC); ignored hosted-storage-path receipt records the scope.
Adapter POSIX ownership/mode/lease checks run on startup, but
direct Render filesystem inspection, hosted worker containment, synthetic engine
ownership/export/reset, expiry and restart acceptance were not run. T057 stays open.

Next: a temporary synthetic-only acceptance window with INTAKE_ENABLED=true and
both provider flags false, followed by readiness and owner-isolation/result/export/
reset controls. No genuine model/source requests are included. Intake has not been
enabled by this work; manual Render configuration/redeployment is required.
Subsequent user enablement and actual hosted workflow/expiry evidence are in
[[docs/sessions/2026-10-11 - Hosted synthetic acceptance]].

## Related

[[docs/sessions/Index]], [[docs/delivery/Deployment guide]],
[[apps/api/src/filingguard/integrations/storage/README]],
[[apps/api/src/filingguard/api/routes/README]],
[[apps/api/migrations/versions/README]],
[[docs/issues/BUG-021 - API deployment root excludes demo resources]],
[[docs/sessions/2026-10-11 - Release checkpoint publication]].
