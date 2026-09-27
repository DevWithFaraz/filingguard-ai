---
type: guide
status: planned
date: 2026-09-27
tags: [deployment]
---
# Deployment guide

T008 in [[TODO]]. Proposed target: Render static frontend and free Python API,
plus Neon free PostgreSQL. Resources are NOT deployed or verified yet.
The user's accounts and approved Git push are required. No billing upgrade is
authorized. If an account requires payment, stop and ask before proceeding.

## 1. Accounts
Sign up at https://dashboard.render.com/register and https://console.neon.tech.
GitHub sign-in makes connecting DevWithFaraz/filingguard-ai easier.
Do not share passwords, API tokens or connection strings in chat.

## 2. Database
In Neon, create a project named FilingGuard on the Free plan. Prefer a region
near the Render service. Create/select the filingguard database and use Connect
to obtain its connection string. Save privately as DATABASE_URL in apps/api/.env.
For SQLAlchemy/psycopg, use postgresql+psycopg:// in place of postgresql://;
retain the host, password and SSL parameters. Use the direct connection for
schema migrations later. Do not remove sslmode=require.
No tables or migrations exist until T010. Provisioning is not migration verification.

## 3. Publish the checkpoint
Deployment needs the new files on GitHub. Before pushing, review the diff and
confirm .env files, .runtime, node_modules and .venv remain ignored. Never force-push.
Ask for authorization to commit/push the reviewed Phase 1 checkpoint.

## 4. API service
In Render, New > Web Service > connect filingguard-ai. Branch main,
root directory apps/api, Python runtime and Free instance.
Build: `pip install uv==0.12.15 && uv sync --locked --no-dev`
Start: `.venv/bin/uvicorn filingguard.main:app --host 0.0.0.0 --port $PORT --workers 1`
Health path: /api/v1/health. Set PYTHON_VERSION=3.12.14 and
UV_PYTHON_DOWNLOADS=never. Set DATABASE_URL privately from Neon.
Set CORS_ORIGINS to a JSON array of the exact frontend HTTPS origin once known;
never use wildcard origins with credentials. The health shell does not need
Groq or CourtListener secrets in Render yet.

## 5. Static frontend
New > Static Site > connect the same repo and main; root directory blank.
Build: `npm ci --ignore-scripts && npm run build`
Publish directory: apps/web/dist. Set NODE_VERSION=24.19.0 and
VITE_API_BASE_URL to the API's HTTPS origin without a trailing slash.
Add rewrite /* -> /index.html for React Router. After the site URL is known,
update API CORS_ORIGINS and redeploy. Frontend env changes require a rebuild.
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

## Sources and related notes
- [Render free limitations](https://render.com/docs/free)
- [FastAPI deployment](https://render.com/docs/deploy-fastapi)
- [Blueprint fields](https://render.com/docs/blueprint-spec)
- [Neon plans](https://neon.com/docs/introduction/plans)

[[docs/delivery/README]], [[docs/architecture/stack]], [[infra/README]].
