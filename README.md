# FilingGuard AI

Pre-filing assurance for AI-assisted legal filings. Product development originating
at LexHack 2026; no active hackathon deadline.

## Start here

The project is also an Obsidian vault. Open this folder as a vault and begin at
[Home.md](Home.md) for linked features, decisions, bugs, lessons and session notes.
Follow [the documentation workflow](docs/knowledge/Documentation%20Workflow.md)
when maintaining project knowledge. Existing documents remain canonical.

Work through [TODO.md](TODO.md) in order, one task at a time. The exact filename
is intentional. [FilingGuard_AI_SRS.md](FilingGuard_AI_SRS.md) is the requirements
baseline; its data-model clarifications are recorded in ADR-004.

This local development app includes dependency manifests, configuration templates,
local PostgreSQL configuration, module guides, a health API and a browser
workspace with Review, Activity and Settings. Typed contracts, persistence models,
initial migration, validated evidence snapshots and private PDF storage foundations
are implemented. T013 integrates retryable file/DB deletion, expiry cleanup and
interrupted-work recovery. The reviewed sample is available through an explicit read-only
demo adapter. Opt-in private document preparation and anonymous session transport
are implemented and verified locally. Local deterministic review jobs run;
Citation/claim extraction preserves original spans, links and method metadata.
Source verification and grounded proposition review are explicit opt-ins; quote
forensics, saved results, graph and Markdown/HTML reports are implemented locally.
External providers and public intake default off. Partial coverage remains visible;
scores are provisional. See [[apps/api/src/filingguard/modules/analyses/README]].

The first homepage redesign is implemented locally: supplied background/logo,
GC Avalance display title, responsive Text/PDF/Demo composer, sample comparison
and GSAP/CSS motion, a glass navigation bar, rounded controls and two lazy-loaded
Three.js studies (hero depth and selectable document/source comparison).
`/demo` opens the reviewed sample; non-home review screens share its visual theme,
workflow navigation and reduced-motion equivalents. See
[[apps/web/src/features/home/README]] and [[design]].

October 11: the full genuine free-credit curated browser journey passes all twelve
SRS acceptance controls against cached public opinions. Desktop/mobile keyboard/axe
checks and measured local limits/performance pass. These synthetic checks do not
establish expert legal accuracy or physical-device performance. October 12:
hosted Text/PDF/cached-demo acceptance, session isolation, exports, deletion,
controlled expiry/restart and live provider/failure/restoration checks pass at
their recorded synthetic scope. `/ready` and `/capabilities` return 200 in the
enabled configuration. No confidential client release is implied; T212/T213 remain.
See [[docs/sessions/2026-10-11 - Accessibility performance and release gates]] and
[[docs/delivery/Deployment guide]] for release checks and remaining access blockers.

D006 adds a silent 26-second process film in "How it works" below the hero.
[[apps/video/README]] owns the separate Remotion authoring workspace, local Chrome
render commands and MP4/WebM/poster production. The web app consumes rendered
assets; authoring tools are not part of its browser runtime. Current revision
and validation evidence: [[docs/sessions/2026-10-07 - Pipeline film visual revision]].

## Chosen stack

- UI: React 19, TypeScript 5, Vite 7, Tailwind CSS 4, shadcn/ui added as needed,
  Lucide icons, React Router 7 and TanStack Query 5.
- Graph: React Flow 12 (`@xyflow/react`).
- Motion: GSAP, `@gsap/react` and ScrollTrigger; CSS control feedback; Three.js for
  nonessential homepage scenes with static/reduced-motion alternatives.
- Film authoring: Remotion 4 in `apps/video`, with separate desktop/mobile
  compositions and a genuine 4K desktop master.
- API: Python 3.12, FastAPI, Pydantic 2 and Uvicorn.
- Analysis: Eyecite, CourtListener, pypdf and RapidFuzz.
- AI: Groq (free tier), provisionally GPT-OSS 120B. Access probes use the
  OpenAI-compatible Python client; feature adapters use the bounded HTTPX
  boundary without implicit SDK retries. Grounded review uses strict output and
  validates source passages; source selection and model confidence are heuristic.
  No paid fallback.
- Persistence: PostgreSQL 17, SQLAlchemy 2, psycopg 3 and Alembic.
- Tooling: npm workspaces, uv, Ruff, pytest, Vitest, Testing Library and Playwright.
- Deployment: Render static frontend/free API and Neon PostgreSQL; hosted shell verified.

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
before enabling them for future packages. Production build and shell tests pass.

## Default runtime

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

The development loop verifies lint, tests, TypeScript checking, contracts and
production build. The hosted shell and isolated PostgreSQL foundation checks are
recorded separately; neither proves the legal analysis pipeline works. The suite
has a Starlette/httpx deprecation warning. See TODO for exact acceptance evidence.

Run `npm run dev:web` in a second terminal and open http://127.0.0.1:5173.
The browser shell reads real API health; document submission remains disabled.
This is the default configuration, not a limitation of the preparation milestone.
With the disposable private preview enabled, prepare a Text/PDF/Demo document,
then select **Run local checks** on its document page. Privacy signals and the
synthetic demo's disclosure check execute locally. The exact curated demo also
executes citation/claim/quote engines against hash-validated cached public opinions.
Live inputs require configured external adapters. Scores remain provisional and
unavailable stages stay unknown; no cached expected classification is replayed.
Executable stages run in contained workers with 30-second stage and 90-second
overall work cutoffs. Timeouts preserve committed checks and terminate local work;
shutdown interrupts remaining stages. Database finalization has separate bounds.
Terminal live reviews offer **New attempt**, which preserves the prior record.
Choose **Open reviewed sample** to inspect the T015-reviewed expectations and
source excerpts. **Reset sample** clears that view. The backend route is
`GET /api/v1/demos/curated-v1?mode=demo`; it performs integrity checks and makes no
provider calls, database writes or legal-engine execution. Material is server-owned
and read from `data/demo/curated-v1` in the monorepo. A standalone packaged install
must supply these resources; missing/changed files return a safe 503. The review
receipt records delegated AI review, not human approval. Draft manifest metadata
remains historical and is not silently promoted to human-reviewed replay.
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

Compose starts PostgreSQL only. Alembic migrations 0001–0004 exist.
Apply `node scripts/api.mjs run alembic upgrade head` deliberately against the
intended database; it writes schema. No migration runs automatically at API startup.
The public Neon schema has not been migrated by this implementation session.
The sample database credentials are for local development only.

## Configuration and data

- Root `.env`: local database configuration for Compose.
- `apps/api/.env`: private backend configuration. App name and CORS settings
  are consumed at startup; DATABASE_URL is read explicitly by migration/database
  tooling and factories. The example contains only implemented settings.
  Put Groq credentials in `GROQ_API_KEY`, CourtListener credentials in
  `COURTLISTENER_API_TOKEN`. `GROQ_MODEL=openai/gpt-oss-120b` is the provisional
  default selected after T005's small synthetic evaluation.
- `apps/web/.env.local`: public browser configuration; never place secrets here.
- `data/demo`: explicitly synthetic fixture material, separated from live mode.
- `.runtime`: ignored tool cache and test artifacts. The private PDF adapter uses
  OS temporary/private storage, never the public asset tree or vault.

By default the shell owns a fresh process-local temporary directory and runs a
threaded file-expiry sweep every 60 seconds, without initializing the DB. For the
opt-in preparation workflow, first apply migrations deliberately, then configure
`PRIVATE_STORAGE_DIRECTORY` in the backend environment to a stable, absolute,
dedicated private directory outside served/synced paths. Its parent must exist;
the adapter creates and owns the directory. Do not reuse an unrelated existing
folder. POSIX requires private permissions; Windows needs private inherited ACLs.
This opt-in also initializes DB recovery/expiry cleanup in a background thread.
`CLEANUP_INTERVAL_SECONDS` accepts 1-3600 seconds. No schema migration runs on startup.

Recoverable receipts permit same-filesystem process-crash recovery, not durable
Render uploads. Normal shutdown purges original PDFs; results can remain in the DB
until their expiry sweep. Cleanup retries failures; deletion is not secure erasure
or a hard TTL guarantee. One API process/replica only. See
[the lifecycle decision](docs/decisions/ADR-006%20-%20Retryable%20private%20lifecycle%20cleanup.md).
`INTAKE_ENABLED=false` is the default. Enabling it additionally requires a private
root and applied migrations, and does not enable legal analysis. Do not enable it
on Render before platform/ownership/abuse/exposure verification. Use public or
synthetic filings only until the T212/T213 confidential-data release gates pass.

## Disposable preparation preview

The preview defaults to disabled live providers. Selecting Demo runs fresh engines
against exact hash-bound cached public opinions; unknown source identities stay
unavailable. It uses disposable SQLite and private storage, not the configured
Neon schema. Reset demo deletes that private analysis and its outputs.

An explicit `--live-semantic` option uses the selected free-credit model, at most
five requests per analysis, with no paid fallback or retries. The complete curated
journey passed locally on October 11 using three shared-authority requests.
Free-tier quota exhaustion still produces explicit unavailability. This is local
synthetic acceptance, not hosted or expert legal verification.
See [[docs/sessions/2026-10-11 - Accessibility performance and release gates]].

To try implemented Text/PDF/Demo preparation without touching Neon, local secrets
or the regular shell, run these in separate terminals from the project root:

```powershell
node scripts/api.mjs run python scripts/run_intake_preview.py
```

```powershell
$env:VITE_API_BASE_URL='http://127.0.0.1:8001'
npm run dev --workspace @filingguard/web -- --host 127.0.0.1 --port 5174 --strictPort
```

Open http://127.0.0.1:5174. The localhost API uses an explicitly overridden, fresh
OS-temporary SQLite database, applies migrations only there, and owns a temporary
private storage root. No provider calls or production writes. Shutdown removes its
temporary data; abrupt termination can leave OS-temp artifacts pending cleanup.
Use synthetic/public input only. Normal `.env` files are not changed. Reset the
terminal's VITE_API_BASE_URL before returning to the default frontend configuration.

Preparation creates a private row and exact text/page/paragraph snapshot, returning
201/not_run. It is not a queued legal analysis. Anonymous bearer access expires
after 55 minutes; only its hash/expiry is in the DB. Original PDFs have one-hour
storage TTL; rows expire with the session. Activity contains summaries, not filing
text. Clear tab storage/close a tab and access may be lost; expiry/deletion is
server-enforced independently. Never share tokens or use this as production auth.
Private `/run` registers privacy/profile checks, citation/claim extraction and
quote forensics. Stored results, graph and Markdown/HTML exports are available
after a terminal run. Routes still return 503 in the default shell because intake
is off. Set `SOURCE_VERIFICATION_ENABLED=true` with `COURTLISTENER_API_TOKEN` to
enable bounded public authority retrieval; set `SEMANTIC_REVIEW_ENABLED=true`
with `GROQ_API_KEY` and `GROQ_MODEL=openai/gpt-oss-120b` to enable grounded review.
Both flags default false. These switches do not enable public intake. Free tier
only; do not configure paid fallback. Missing keys/services produce uncertainty.
`ANALYSIS_TIMEOUT_SECONDS`, `REVIEW_STAGE_TIMEOUT_SECONDS` and `MAX_PROVIDER_ATTEMPTS`
configure the supervisor (defaults 90, 30 and 60). See
[[apps/api/src/filingguard/integrations/providers/README]] for provider policy and
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]] for limits.

The two timeout settings accept positive seconds up to 300; provider attempts accept
1–60. `CORS_ORIGINS` is a JSON array of exact origins. `APP_NAME` controls API naming;
`CLEANUP_INTERVAL_SECONDS` accepts 1–3600. Environment variables override the backend
`.env` file. Root `.env` is for Compose; it is not the normal runtime settings file.
If you change Compose's PostgreSQL port or credentials, also update the backend's
`DATABASE_URL` to match. Never put provider keys or database URLs in browser env.

Playwright also starts this isolated preview plus the default shell, uses one test
worker to respect the single preparation slot, and verifies real API/browser flows.
See [[docs/decisions/ADR-007 - Private preparation boundary]] for limits/tradeoffs.

CourtListener source verification and Groq semantic review use actual bounded
adapters when explicitly enabled. Their configuration is handed only to the
matching contained worker. Saved outputs preserve provenance and limitations.
Synthetic/cached results must never be
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
```

The evaluation sends synthetic evidence tests, not confidential filings.
See [the recorded evidence](docs/research/Provider%20access%20verification.md).
Successful access probes establish connectivity, not the accuracy of review verdicts.

## Foundation checks
`npm run test:api` covers contracts, errors, evidence, persistence and PDF storage
without provider calls. SQLite migrations are applied to fresh in-memory test DBs.
Explicit Neon verification is available with:

```powershell
node scripts/api.mjs run python scripts/verify_postgres_persistence.py --confirm-isolated-write
```

This opt-in command creates, migrates, tests and removes a freshly named disposable
schema; it does not migrate existing/public tables and never prints credentials.
An isolated Neon check passed September 27 before the new file-reference migration.
T013 cleanup and private preparation are verified locally; the current Neon schema
head has not been verified for this release. Migrations 0002–0004 were not applied
to Neon during these implementation sessions. Cached-source demo execution and
the complete genuine-model curated journey pass locally.
The unreviewed starter demo fails closed instead of returning fabricated results.

The supplied-asset homepage direction is accepted. Other pages now share its theme,
workflow navigation and accessible motion; the glass composer awaits aesthetic
feedback. Continuing UI scope is recorded in [AGENTS.md](AGENTS.md).
Only the older shell is deployed. Current checkpoint publication and hosted
acceptance are tracked in [[docs/sessions/2026-10-11 - Release checkpoint publication]].

## Limits and troubleshooting

These are implementation limits, not environment switches: PDF 10 MiB/20 pages,
text 100,000 characters/2,000 paragraphs, 25 distinct authority queries, one active analysis,
two concurrent provider requests, 20-second provider HTTP timeout and zero model
retries. Sessions expire after 55 minutes; original PDF retention is one hour.
Cleanup can be delayed or retried. Scanned PDFs require pasted text; no OCR exists.
Cached public sources are labeled separately from live retrieval. Missing sources,
provider errors and incomplete coverage remain unknown; scores are provisional.

- Submission disabled: the default shell has `INTAKE_ENABLED=false`. Use the
  disposable preview above for local public/synthetic preparation.
- API unavailable: start the API separately, verify `/api/v1/health`, and check
  frontend `VITE_API_BASE_URL`. Port 5174 uses API 8001; normal port 5173 proxies 8000.
  Restart Vite after changing env; production env changes require a rebuild.
- `/api/v1/ready` 503: check intake configuration, private root, migration head,
  cleanup and credentials for explicitly enabled stages. Health 200 is liveness.
  A 404 on this route means the deployed API is older than the working release.
- No previous document access: anonymous credentials are tab/session scoped;
  expiry, reset and deletion remove access. Activity cannot recover a lost token.
- Port already occupied: stop only the process you started, or use the preview's
  documented test ports 8002/5175. Do not attach tests to another person's session.
- Installation/build errors: confirm Node 24, Python 3.12, uv and the locked
  commands above. Do not fix them with an unbounded dependency upgrade.

See [third-party notices](docs/delivery/Third-party%20notices.md) for dependency
license evidence and supplied-asset provenance. Application source has no declared
redistribution license; dependency licenses do not license the application itself.
See [deployment steps](docs/delivery/Deployment%20guide.md) for existing Render
service settings, deliberate Neon migrations and hosted acceptance.
