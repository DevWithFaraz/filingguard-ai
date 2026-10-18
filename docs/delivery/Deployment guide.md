---
type: guide
status: hosted-synthetic-acceptance-verified
date: 2026-10-11
tags: [deployment]
---
# Deployment guide

October 11 release status: accessibility, measured local limits/performance and
the complete genuine-model curated journey pass. Final regression evidence is in
[[docs/sessions/2026-10-11 - Accessibility performance and release gates]].
User reports both services Live on `5b37993`. Read-only hosted checks now verify
frontend SPA routes, API health/capabilities and reviewed sample preview 200 with
exact CORS and the sample's locked filing hash. Readiness now returns 200 after
the user enables the temporary synthetic intake window. Hosted cached-demo/PDF
engine runs, owner isolation, masked exports, deletion and accelerated synthetic
expiry pass. The 18:07 UTC API restart check verifies unchanged saved results/graphs,
masked exports and controlled queued-state recovery; both fixtures are deleted.
The user enabled both provider stages for T058. Genuine hosted live Brown and
explicit cached-source/fresh-model reviews pass their bounded controls, including
masked exports and owner denial; both fixtures are deleted. Coverage remains
partial. October 12 controlled source-authentication failure passes: live citations
remain unavailable and explicitly selected cached sources/quotes/exports work.
The genuine token and semantic setting are restored. A fresh live review passes
25 checks (42.937s), including real source/model evidence, masked exports, owner
denial and deletion. Public readiness/routes/CORS pass again. T058 is verified
at synthetic rehearsal scope; the temporary failure settings are retired.
Latest evidence: [[docs/sessions/2026-10-12 - Hosted dependency failure rehearsal]].
Earlier prerequisite evidence:
[[docs/sessions/2026-10-11 - Closed intake hosted checks]].
The release checkpoint is published on `codex/release-checkpoint`;
the approved Neon production migration now commits at `0004_citation_extraction`.
Render private-storage readiness and the synthetic workflow are verified. Intake
is enabled for synthetic acceptance; external providers are enabled for T058.
The user's Chrome is signed in, but Chrome control is unavailable in this execution
environment. T057 passes at synthetic hosted acceptance scope; direct physical
filesystem inspection and expert legal QA remain separate. The concrete rollout
below records the existing free services and the procedure for future releases.

T008 in [[TODO]]. Current target: Render static frontend and free Python API,
plus Neon free PostgreSQL. User created both accounts and the Neon project;
a direct read-only connection verified PostgreSQL 17.11 and client TLS.
Hosted shell verified on September 27: https://filingguard-ai.onrender.com and
https://filingguard-api.onrender.com/api/v1/health. Direct SPA routes and exact
frontend-origin CORS pass. A second API deployment succeeded. This verifies only
the shell, not hosted database use or analysis features. Evidence:
[[docs/sessions/2026-09-27 - Hosted shell verification]].
No billing upgrade is
authorized. If an account requires payment, stop and ask before proceeding.

## 1. Existing accounts
Open https://dashboard.render.com and https://console.neon.tech using the existing
accounts. Reuse the existing services and Neon project; do not create duplicates.
Do not share passwords, API tokens or connection strings in chat.

## 2. Database
In Neon, select the existing FilingGuard project on the Free plan. Select the
intended branch and filingguard database and use Connect
to obtain its connection string. Save privately as DATABASE_URL in apps/api/.env.
For SQLAlchemy/psycopg, use postgresql+psycopg:// in place of postgresql://;
retain the host, password and SSL parameters. Use the direct connection for
schema migrations later. Do not remove sslmode=require.
Local migrations through 0004 exist. Provisioning is not migration verification.
Run `node scripts/api.mjs run python scripts/check_database.py` for an explicit
read-only connection/version/TLS check. It never prints credentials or DB errors.

## 3. Publish the checkpoint
Deployment needs the new files on GitHub. Before pushing, review the diff and
confirm .env files, .runtime, node_modules and .venv remain ignored. Never force-push.
On October 11 the user lifted the no-commit/push constraint. The reviewed release
checkpoint is now pushed to `codex/release-checkpoint`. Application revision
`325451a` passes the complete [GitHub Checks run](https://github.com/DevWithFaraz/filingguard-ai/actions/runs/38148960096).
The following commit only records documentation/evidence. `main` still contains
the older shell; select the release branch explicitly in both services.

## 4. API service
In Render, open the existing filingguard-api service, then Settings. Confirm its
connected repository and reviewed release branch, root directory blank,
Python runtime and Free instance. Keep auto-deploy off during the gated rollout.
Build: `pip install uv==0.12.15 && uv sync --directory apps/api --locked --no-dev`
Start: `apps/api/.venv/bin/uvicorn filingguard.main:app --host 0.0.0.0 --port $PORT --workers 1`
Leave Root Directory blank so server-owned `data/demo/curated-v1` is included.
Render excludes files outside a configured service root. The former `apps/api`
root worked for the health shell but excludes the current demo resources.
Health path: /api/v1/health. Set PYTHON_VERSION=3.12.14 and
UV_PYTHON_DOWNLOADS=never. Set DATABASE_URL privately from Neon.
Set CORS_ORIGINS to a JSON array of the exact frontend HTTPS origin once known;
never use wildcard origins with credentials. The health shell does not need
Groq or CourtListener secrets in Render yet.

## 5. Static frontend
Open the existing filingguard-ai static site, then Settings. Confirm the same
repository and reviewed release branch; root directory blank.
Build: `npm ci --ignore-scripts && npm run build`
Publish directory: apps/web/dist. Set NODE_VERSION=24.19.0 and
VITE_API_BASE_URL to the API's HTTPS origin without a trailing slash.
Add rewrite /* -> /index.html for React Router. After the site URL is known,
update API CORS_ORIGINS and redeploy. Frontend env changes require a rebuild.
Current API CORS_ORIGINS: `["https://filingguard-ai.onrender.com"]`.
Root render.yaml records these settings as an alternative Blueprint path.
Review all plan choices before applying a Blueprint; do not create paid resources.

## 6. Acceptance gate
Verify frontend HTTPS, /activity and /settings direct navigation, API-connected
status, exact-origin CORS and blocked document submission. Verify database
connectivity without printing its URL/password. Trigger a second deployment
to demonstrate repeatability. Only then check off T008.

Free Render services sleep after 15 minutes idle and may need about a minute to
restart. Local files are ephemeral: no durable uploaded filings on this plan.
Open the deployed app before recording and confirm it is awake. Startup recovery
and durable analysis evidence must be implemented before public analysis use.

## Working-app rollout (T057)

Use the existing free services and selected model; do not add paid resources.
The Blueprint records disabled intake/provider flags, 90-second overall analysis,
60-second review stage and one API worker. `/health` remains the deployment
liveness check so a deliberately closed intake can start. `/ready` must return
200 with every boolean true before calling the working app ready. It only reads
local dependencies and the current migration head; it never migrates or calls a
provider. Missing credentials, disabled intake, old schema and cleanup failure
produce 503. A provider outage can still occur after readiness passes.

Publish the reviewed checkpoint and deploy with intake/providers initially off.
Free Render web services have no dashboard shell or SSH, and pre-deploy commands
require paid compute. Use the reviewed local checkout for deliberate migrations
instead; do not add migrations to the build or startup command. In Neon Connect,
select the intended branch/database and direct connection. Save its TLS connection
privately in `apps/api/.env` as `DATABASE_URL`, retaining `sslmode=require` and the
`postgresql+psycopg://` scheme. Confirm the database target and existing-data recovery
plan before executing schema writes. From the repository root:

```powershell
node scripts/api.mjs run python scripts/check_database.py
node scripts/api.mjs run alembic current
node scripts/api.mjs run alembic heads
# Deliberate write to the configured database, only during the authorized rollout:
node scripts/api.mjs run alembic upgrade head
node scripts/api.mjs run alembic current
```

Confirm current agrees with head (currently `0004_citation_extraction`). Keep connection strings and
credential-bearing output private. No hosted migration was performed in T059.

Create a dedicated absolute private directory outside the served frontend, set
`PRIVATE_STORAGE_DIRECTORY` to it, and verify POSIX owner-only permissions and
resource containment on Render. Keep one process and one replica. Free-plan
storage is ephemeral: a restart may lose retained files, which must surface as
explicit unavailability and cleanup/recovery, not successful evidence retrieval.
The implementation uses a one-hour retention boundary and 55-minute sessions;
there is no configurable `RETENTION_HOURS` switch.

Set the exact frontend HTTPS origin in `CORS_ORIGINS`, the API HTTPS origin in
the frontend's `VITE_API_BASE_URL`, and private provider credentials only for
deliberately enabled stages. Set `GROQ_MODEL=openai/gpt-oss-120b`; keep the
20-second HTTP cap and zero model retries. The curated live timing was verified
with `REVIEW_STAGE_TIMEOUT_SECONDS=60` and `ANALYSIS_TIMEOUT_SECONDS=90`; the
application's existing stage default remains 30. Token admission is advisory,
and other organization usage may cause explicit unavailability.

Enable intake only after storage, migration and containment checks. Run
`node scripts/check_hosted_release.mjs`: it checks health, readiness, capabilities,
exact/forbidden-origin behavior and direct SPA routes without submitting a filing.
Its JSON receipt is ignored under `.runtime`; a failed request cannot pass a CORS
check. Then run a fresh hosted synthetic-only intake-to-export journey, including
second-session denial, masked evidence/report, reset/delete, expiry and restart
recovery. Verify retained results stay owner-scoped. T057 cannot be checked off
until these hosted controls pass. Rehearse both explicit cached and live modes
and a forced provider outage under T058. T212/T213 still gate confidential client use.

Recovery: disable intake/provider flags if readiness, isolation or cleanup fails;
recheck readiness after correction. Review database compatibility before changing
the deployed code revision. Do not undo migrations or delete retained evidence
as an automatic rollback.

## Dashboard sequence when publication is authorized

1. Review and publish the local checkpoint first. Publication is now authorized;
   Render cannot deploy unpublished workspace files. Select the published release
   branch/revision explicitly rather than assuming it is already on main.
2. API > Environment: confirm private `DATABASE_URL`,
   `CORS_ORIGINS=["https://filingguard-ai.onrender.com"]`, Python/uv settings from
   section 4, `ANALYSIS_TIMEOUT_SECONDS=90`, `REVIEW_STAGE_TIMEOUT_SECONDS=60`,
   `MAX_PROVIDER_ATTEMPTS=60`, `CLEANUP_INTERVAL_SECONDS=60` and
   `GROQ_MODEL=openai/gpt-oss-120b`. Keep intake/source/semantic flags `false`.
3. API > Manual Deploy: deploy the reviewed revision. Confirm `/api/v1/health` 200
   and `/api/v1/capabilities` exists. `/api/v1/ready` 503 is expected with intake off.
4. Apply and verify migrations from the local checkout as described above.
5. Set `PRIVATE_STORAGE_DIRECTORY=/tmp/filingguard-private`, a dedicated private
   root whose parent exists. Verify Linux ownership/containment before public
   enablement. Credentials belong only in the API service environment.
6. Static site > Environment: set `NODE_VERSION=24.19.0` and
   `VITE_API_BASE_URL=https://filingguard-api.onrender.com`. Confirm SPA rewrite
   and build/publish settings, then manually deploy the same reviewed revision.
7. During the authorized synthetic acceptance window, enable intake after its
   prerequisites pass; enable external stages only with their matching private
   keys and the free-credit budget. Redeploy the API after env changes.
8. Run the hosted probe and synthetic ownership/export/deletion/expiry/restart
   journey above. Readiness must pass for the enabled configuration. Disable
   intake again if any release control fails. Record the tested deployed revision.

The release branch is published; select `codex/release-checkpoint` and wait for
its GitHub Checks run to pass before manually deploying. Dashboard changes,
hosted migration and hosted acceptance remain outstanding. The user has deployed
the closed-intake services. The configured Neon connection passes the read-only
TLS probe. User confirmed the same host/database and production branch, then
approved migration. The transaction commits through `0004_citation_extraction`;
all 10 application tables and column sets match, and an independent read-only
revision check passes. Do not rerun the initial empty-schema migration helper.

With intake still off, set `PRIVATE_STORAGE_DIRECTORY=/tmp/filingguard-private`
in the API environment after migration and redeploy. The adapter creates the root
with POSIX mode 0700 and rejects existing foreign roots, links or group/other
permissions. Its successful startup establishes these adapter checks; public
readiness alone is not a direct filesystem inspection. Expect readiness to remain
503 because intake is off, while `private_storage`, `database_schema` and `cleanup`
are now verified true after the user's storage configuration/redeployment. Without configured recoverable
storage, readiness does not initialize a DB engine and keeps `database_schema`
false even if the separately checked database has been migrated.

## Sources and related notes
September 28 preparation release boundary: latest code remains local and public
intake is off. Migration 0003 adds session hashes/expiry and document snapshots;
0002/0003 have not been applied to Neon. Before any public enablement, review and
authorize the release, migrate deliberately, verify POSIX worker limits/private
permissions and exact-origin PDF preflight, and test owner isolation, quotas,
expiry/deletion and no public file exposure on the hosted services. Keep one API
process/replica. The localhost preview is disposable SQLite, not hosted acceptance.
Do not use confidential client data before T212/T213. See
[[docs/decisions/ADR-007 - Private preparation boundary]] and [[TODO]] T057.

- [Render free limitations](https://render.com/docs/free)
- [Render shell access](https://render.com/docs/ssh)
- [Render deployment stages](https://render.com/docs/deploys)
- [Render monorepo roots](https://render.com/docs/monorepo-support)
- [FastAPI deployment](https://render.com/docs/deploy-fastapi)
- [Blueprint fields](https://render.com/docs/blueprint-spec)
- [Neon plans](https://neon.com/docs/introduction/plans)

[[docs/delivery/README]], [[docs/architecture/stack]], [[infra/README]].
