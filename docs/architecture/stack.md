# Stack and architecture decisions

Decision date: September 26, 2026. Scope: LexHack implementation scaffold.

## Architecture

Use one repository with two applications: a React browser client and a modular
FastAPI backend. PostgreSQL holds analysis state and evidence. The API owns all
legal-data and LLM calls. This resolves the SRS's open Spring Boot/Node choice in
favor of Python because legal citation and document processing are central.

```text
React browser -> FastAPI routes -> analysis orchestrator -> feature modules
                                      |                      |
                                 PostgreSQL           provider adapters
                                                      /              \
                                                CourtListener       Groq
```

## Technology choices

React/Vite keeps the browser workflow straightforward. TanStack Query owns server
state and polling; React state owns transient selections. Use React Router for
pages, Tailwind for styles, shadcn/ui primitives added only as needed, and Lucide
for icons. React Flow renders section/claim/authority relationships; PostgreSQL
stores the graph entities without a separate graph database.

Python/FastAPI provides typed request/response boundaries. Pydantic schemas are
the API source of truth; export OpenAPI and generate TypeScript types instead of
maintaining duplicate contracts. SQLAlchemy and Alembic own persistence and schema
changes. Use ordinary sessions in synchronous/thread-offloaded units of work.

Eyecite extracts legal citations; CourtListener resolves authorities and supplies
source material. pypdf handles text-based PDFs, with a paste-text fallback for
scanned/poorly extracted documents. RapidFuzz complements exact and normalized
quote comparison. These are separate checks: extraction is not verification and
text similarity is not a finding of legal support.

Groq was selected by the user on September 27 under a free-credits-only budget.
Use its OpenAI-compatible API for bounded claim extraction and proposition review.
Choose the actual model through `GROQ_MODEL` after account access, fixture
quality and latency are measured. Prompt version, model ID, evidence IDs and
uncertainty must be recorded. Validate passages against stored sources even when
the response obeys its schema. No live provider integration exists yet.
See [[docs/decisions/ADR-003 - Free-tier Groq evaluation]]. The installed OpenAI
SDK is a client library, not a commitment to paid OpenAI-hosted inference.

## MVP execution plan

One API process/replica owns in-process background execution. Persist an analysis
record before returning HTTP 202. Poll status every 1 second while pending, back
off on errors, and stop on terminal state/unmount. Reserve a slot before accepting
work; initially allow one active analysis. Do not create an unbounded queue.

Persist each stage and its partial findings. Bound external requests and retry
only retryable failures within the overall deadline. PDF/CPU and synchronous DB
work must not block the event loop. In-process tasks are not durable: startup must
mark abandoned running/queued analyses interrupted and offer an explicit rerun.
Move execution to a durable worker before scaling beyond one API process (P1).

Initial limits: 10 MB, 20 pages, 100,000 extracted characters, 25 unique authorities,
20-second provider timeout, 90-second overall cutoff. These are proposed defaults
to validate, not measured performance. Target the curated demo at <=60 seconds.
Bound long opinion passages from the first implementation; richer retrieval is P1.

## Module boundaries

Routes validate input and delegate. `modules/analyses` composes feature modules.
Modules expose small typed results and do not import routes. Provider-specific
payloads stay inside `integrations`; pure quote/scoring logic needs no HTTP or DB.
Start with `schemas.py` and `service.py` only when code is needed. Add repositories
or interfaces when a real dependency boundary requires them, not in every folder.

Evidence locations and source identity are P0 foundations. Rich lineage UI is P1.
Store score coverage separately: missing/unavailable checks cannot become passes.
Preserve original text offsets separately from normalized matching strings.

## Scope decisions

- No Redis/Celery, vector database, Kubernetes, agent framework or microservices
  for P0. Add a durable job system only if the demonstrated workload requires it.
- No OCR, accounts, billing, multi-user collaboration or automatic court filing
  for P0. Session-scoped result access is still required before public uploads.
- Demo material must be visibly synthetic or attributed cached public material.
  Live failures remain unavailable; they do not silently become demo results.
- One synthetic court profile can demonstrate the rule mechanism. Any real court
  profile needs verified primary-source scope, dates and judge applicability.

## References used for these choices

- [Eyecite](https://github.com/freelawproject/eyecite): legal citation extraction.
- [CourtListener citation lookup](https://wiki.free.law/c/courtlistener/help/api/rest/v4/citation-lookup).
- [React Flow](https://reactflow.dev/learn): graph library and stylesheet ordering.
- [pypdf text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html): extraction limits; no OCR.
- [FastAPI background tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/): execution and limitations.
- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
- [uv projects](https://docs.astral.sh/uv/guides/projects/).

Deployment providers are selected targets; provisioning, current plan limits,
credentials and hosted performance are tasks, not claims of a deployed system.
