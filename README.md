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

This scaffold includes dependency manifests, configuration templates, local
PostgreSQL configuration, module guides, a health-only API entry point and its
smoke test. It does not yet implement product screens, document analysis,
provider calls, persistence models, database migrations or job execution.

## Chosen stack

- UI: React 19, TypeScript 5, Vite 7, Tailwind CSS 4, shadcn/ui added as needed,
  Lucide icons, React Router 7 and TanStack Query 5.
- Graph: React Flow 12 (`@xyflow/react`).
- API: Python 3.12, FastAPI, Pydantic 2 and Uvicorn.
- Analysis: Eyecite, CourtListener, pypdf and RapidFuzz.
- AI: Groq (free tier), using the OpenAI-compatible Python client. Model selection
  and live connectivity remain T005; no paid fallback.
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

There is no frontend screen or frontend dev/build command yet. Task T006 adds
`apps/web/index.html`, `src/main.tsx`, `src/app/App.tsx`, and Vite scripts. The
existing Vite config proxies development `/api` requests to port 8000.

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
  `COURTLISTENER_API_TOKEN`, and leave `GROQ_MODEL` blank until T005 evaluation.
- `apps/web/.env.local`: public browser configuration; never place secrets here.
- `data/demo`: explicitly synthetic fixture material, separated from live mode.
- `.runtime`: ignored private temporary storage, created by future storage code.

All analysis modules are unimplemented. Synthetic/cached results must never be
presented as live verification. Findings support human review, not legal advice
or a guarantee of filing readiness.
