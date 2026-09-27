# FilingGuard AI

Pre-filing assurance for AI-assisted legal filings. LexHack 2026 prototype.

## Start here

The project is also an Obsidian vault. Open this folder as a vault and begin at
[Home.md](Home.md) for linked features, decisions, bugs, lessons and session notes.
Follow [the documentation workflow](docs/knowledge/Documentation%20Workflow.md)
when maintaining project knowledge. Existing documents remain canonical.

Work through [TODO.md](TODO.md) in order, one task at a time. The exact filename
is intentional. [FilingGuard_AI_SRS.md](FilingGuard_AI_SRS.md) is the requirements
baseline; it has not been modified.

This development shell includes dependency manifests, configuration templates,
local PostgreSQL configuration, module guides, a health-only API and a browser
workspace with Review, Activity and Settings. It does not yet implement document analysis,
provider calls, persistence models, database migrations or job execution.

## Chosen stack

- UI: React 19, TypeScript 5, Vite 7, Tailwind CSS 4, shadcn/ui added as needed,
  Lucide icons, React Router 7 and TanStack Query 5.
- Graph: React Flow 12 (`@xyflow/react`).
- API: Python 3.12, FastAPI, Pydantic 2 and Uvicorn.
- Analysis: Eyecite, CourtListener, pypdf and RapidFuzz.
- AI: Groq (free tier), using the OpenAI-compatible Python client. The provisional
  model is GPT-OSS 120B; access checks passed, production integration
  remains unimplemented. No paid fallback.
- Persistence: PostgreSQL 17, SQLAlchemy 2, psycopg 3 and Alembic.
- Tooling: npm workspaces, uv, Ruff and pytest. Add Vitest, Testing Library and
  Playwright with the frontend test setup.
- Deployment target: Vercel static frontend; Railway API and PostgreSQL.

See [architecture decisions](docs/architecture/stack.md) and the
[directory guide](docs/architecture/directory-structure.md).

## Install dependencies

Prerequisites: Node.js 24, npm, uv and Python 3.12. Docker Desktop is needed only
for the local database. Dependencies and lockfiles were verified locally on
September 27, 2026 with Node 24.19.0 and Python 3.12.14.

Run from the project root:

```powershell
npm ci --cache .runtime/tool-cache/npm --ignore-scripts
npm run setup:api
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
if (-not (Test-Path apps/api/.env)) { Copy-Item apps/api/.env.example apps/api/.env }
if (-not (Test-Path apps/web/.env.local)) { Copy-Item apps/web/.env.example apps/web/.env.local }
```

Do not overwrite existing local environment files. Use the lockfiles, not new
unbounded installs. API commands use `scripts/api.mjs` and an ignored local uv
cache to avoid this machine's global-cache failure. uv can download Python 3.12
when necessary; with an existing interpreter use
`npm run setup:api -- --python C:/path/to/python.exe`.

npm lifecycle scripts are disabled for installation. The current lockfile's
esbuild platform binary passed a transform check without them; review scripts
before enabling them for future packages. Full frontend build is still T006.

## API scaffold

After installation:

```powershell
npm run dev:api
npm run test:api
npm run lint:api
npm run typecheck
npm run contracts:export
npm run contracts:generate
```

Run the development server in a separate terminal. The API listens at
`http://127.0.0.1:8000`, exposes `/api/v1/health`, and serves API docs at `/docs`.
Health checks process liveness only; it does not contact the database or providers.
Generated OpenAPI and browser types are created by the contract commands above.

Verified locally: backend lint, one passing health test, TypeScript checking,
OpenAPI export/type generation, and HTTP 200 from health/docs on a running API.
The test suite has a Starlette/httpx deprecation warning. These checks do not
verify legal analysis, providers, PostgreSQL or hosted deployment.

Run `npm run dev:web` in a second terminal and open http://127.0.0.1:5173.
The browser shell reads real API health; document submission remains disabled.
`npm run build` creates apps/web/dist. The Vite config proxies development /api
requests to port 8000. Set VITE_API_BASE_URL to the hosted API origin for production.

Frontend checks: `npm run lint:web`, `npm run test:web` and `npm run test:e2e`.
Install test Chromium with `npx playwright install chromium` from apps/web, or
set PLAYWRIGHT_BROWSER_CHANNEL=chrome to use an installed Chrome locally.
Playwright starts the API and frontend automatically. CI runs locked installs,
lint, tests, typecheck, contract checks, production build and browser checks
without provider credentials. The initial clean-checkout GitHub CI run passed
for checkpoint 95b38e7 on September 27, 2026.
See [deployment steps](docs/delivery/Deployment%20guide.md) for T008.

## Local database

```powershell
docker compose --env-file .env -f infra/compose.yaml up -d db
```

Compose starts PostgreSQL only. Alembic configuration and migrations are T010.
The sample database credentials are for local development only.

## Configuration and data

- Root `.env`: local database configuration for Compose.
- `apps/api/.env`: private backend configuration. Only app name and CORS settings
  are consumed today; remaining entries define planned module settings.
  Put Groq credentials in `GROQ_API_KEY`, CourtListener credentials in
  `COURTLISTENER_API_TOKEN`. `GROQ_MODEL=openai/gpt-oss-120b` is the provisional
  default selected after T005's small synthetic evaluation.
- `apps/web/.env.local`: public browser configuration; never place secrets here.
- `data/demo`: explicitly synthetic fixture material, separated from live mode.
- `.runtime`: ignored private temporary storage, created by future storage code.

All analysis modules are unimplemented. Synthetic/cached results must never be
presented as live verification. Findings support human review, not legal advice
or a guarantee of filing readiness.

## Explicit provider checks

These commands make live requests only when run deliberately. They read local
keys without printing them; keep the account on its free plan. Access checks
support root .env as a fallback, but use apps/api/.env for backend configuration.

```powershell
node scripts/api.mjs run python scripts/check_provider_access.py courtlistener
node scripts/api.mjs run python scripts/check_provider_access.py groq
node scripts/api.mjs run python scripts/evaluate_groq.py openai/gpt-oss-120b
node scripts/api.mjs run python scripts/evaluate_groq.py openai/gpt-oss-20b
```

The last two commands send synthetic evidence tests, not confidential filings.
See [the recorded evidence](docs/research/Provider%20access%20verification.md).
Successful probes do not mean a production provider adapter exists.
