# FilingGuard AI

Pre-filing assurance for AI-assisted legal filings. LexHack 2026 prototype.

## Start here

The project is also an Obsidian vault. Open this folder as a vault and begin at
[Home.md](Home.md) for linked features, decisions, bugs, lessons and session notes.
Follow [the documentation workflow](docs/knowledge/Documentation%20Workflow.md)
when maintaining project knowledge. Existing documents remain canonical.

Work through [TDOD.md](TDOD.md) in order, one task at a time. The exact filename
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
- AI: OpenAI Python SDK with structured outputs and bounded retrieved passages.
- Persistence: PostgreSQL 17, SQLAlchemy 2, psycopg 3 and Alembic.
- Tooling: npm workspaces, uv, Ruff and pytest. Add Vitest, Testing Library and
  Playwright with the frontend test setup.
- Deployment target: Vercel static frontend; Railway API and PostgreSQL.

See [architecture decisions](docs/architecture/stack.md) and the
[directory guide](docs/architecture/directory-structure.md).

## Install dependencies (next task)

Prerequisites: Node.js 24, npm, uv and Python 3.12. Docker Desktop is needed only
for the local database. Dependencies have not been installed in this scaffold.

Run from the project root:

```powershell
npm install
uv sync --project apps/api
Copy-Item .env.example .env
Copy-Item apps/api/.env.example apps/api/.env
Copy-Item apps/web/.env.example apps/web/.env.local
```

Do not overwrite existing local environment files. The first install must produce
`package-lock.json` and `apps/api/uv.lock`; commit them after compatibility checks.
Subsequently use `npm ci` and `uv sync --project apps/api --locked`. Manifest
version ranges are selected major-version baselines, not verified lockfiles.

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
- `apps/web/.env.local`: public browser configuration; never place secrets here.
- `data/demo`: explicitly synthetic fixture material, separated from live mode.
- `.runtime`: ignored private temporary storage, created by future storage code.

All analysis modules are unimplemented. Synthetic/cached results must never be
presented as live verification. Findings support human review, not legal advice
or a guarantee of filing readiness.
