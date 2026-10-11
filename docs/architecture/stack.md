# Stack and architecture decisions

October 11 deployment boundary: the API requires repository-root `data/demo`
resources. Render Root Directory must stay blank; scoped uv/build/start commands
target `apps/api` without excluding the fixtures. No runtime source is copied into
public browser assets. See [[docs/issues/BUG-021 - API deployment root excludes demo resources]]
and [[docs/delivery/Deployment guide]]; hosted verification remains pending.

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

September 29: GSAP and @gsap/react own entrance/source-panel choreography, with
ScrollTrigger for editorial section reveals and bounded background drift.
Scoped hooks/matchMedia revert animations on unmount/reduced-motion changes.
CSS owns control feedback. Three.js is dynamically imported for a transparent
hero overlay and a separate selectable evidence study; neither runs legal logic.
Rendering is bounded and on demand; see [[apps/web/src/features/home/README]].
No additional Motion dependency was introduced. Build measurements and limitations
are in [[docs/sessions/2026-09-29 - Glass homepage and evidence motion]].
The root route renders the full-width homepage; inner routes retain the workspace.

October 6: D006 adds a separate Remotion authoring workspace in `apps/video`.
The selected delivery is a silent rendered process film below the hero, with a
4K master and smaller MP4/WebM website derivatives. The web app will consume
media rather than a live Remotion Player. The 780-frame composition and responsive
embed are implemented; revised media pass metadata/size and homepage browser
checks. The October 7 Authority readability revision is verified. A separate mobile
composition enlarges evidence text while retaining the format and timing.
Local fonts remove render-time external font requests. [[apps/video/README]] owns
authoring responsibilities; [[apps/video/brief/BRIEF]] owns delivery requirements and
[[docs/decisions/ADR-010 - Remotion pipeline film]] records the delivery choice.
This adds no legal engine, provider call or change to intake behavior.

October 7 visual revision retains this architecture and adds a structured evidence
workbench background, layered paper/glass surfaces and native-sized Authority
anchors. Source cards wait until the filing clears their area. The previous
exports are hash-verified copies in ignored revision storage; revised export and
browser evidence belong to
[[docs/sessions/2026-10-07 - Pipeline film visual revision]].

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
The user selected `openai/gpt-oss-120b` through `GROQ_MODEL` after an initial
synthetic comparison; broader real-case validation remains. Prompt version, model ID, evidence IDs and
uncertainty must be recorded. Validate passages against stored sources even when
the response obeys its schema. Live integrations are implemented as explicit opt-ins;
October 11 genuine-model synthetic acceptance uses cached public sources and
preserves that provenance. Conservative shared-authority batches and bounded token
admission retain independent verdicts and source qualifications. Hosted provider
acceptance remains separate. See
[[docs/decisions/ADR-013 - Shared authority model requests and bounded quota admission]].
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

Render static frontend/free API plus Neon free PostgreSQL is the deployed shell
target. See [[docs/delivery/Deployment guide]] for verified origins and cold-start/
ephemeral-filesystem limits. T008 passed; production analysis remains unavailable.
No change to the single-process backend architecture is implied.

Typed lifecycle/coverage, lazy SQLAlchemy sessions, initial Alembic migration and
immutable evidence snapshots are implemented. Isolated Neon migration checks passed;
production schema migration and public analysis routes remain pending. Private PDF
storage has UUID admission and one-hour default retention. T013 now adds recoverable
private-file receipts, coordinated file-first DB deletion, interrupted-work recovery
and application-owned threaded cleanup/shutdown. An explicitly configured stable
private root activates persistence cleanup; default-shell health has no DB dependency.
Streaming, anonymous bearer authorization and bounded parser isolation are now
implemented and verified locally. See
[[docs/decisions/ADR-004 - Truthful contracts and scoped evidence]].
Recovery requires one process and the same filesystem; ephemeral Render disk is
not durable original-document storage. No production migration or new deployment
is implied. See [[docs/decisions/ADR-006 - Retryable private lifecycle cleanup]].

Private preparation is synchronous, with 201/not_run after extraction/persistence,
not the future 202 legal job. One process-local admission slot is held before body
buffering through the response; T023 extends the slot over local review jobs.
T024 now runs executable stages in bounded child processes while the parent owns
DB transactions. Privacy/profile checks precede provider-dependent checks; absent
engines are unavailable metadata without worker startup. The shared fixed-host
provider boundary has finite attempt/concurrency/byte budgets and no Groq retries.
Stage/overall cutoffs terminate local process trees, not remote provider work;
DB finalization remains separately bounded. CourtListener/Groq adapters now run
only with explicit independent opt-in flags; public intake still defaults off. See
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]].

Grounded review passes allowlisted owner-scoped detached contexts and stage-only
credentials through bounded private stdin JSON. The parent validates original
spans, relations and evidence snapshots before atomic storage. Saved scores,
results/graph and escaped Markdown/HTML exports reuse stored output without model
reclassification. Coverage and missing sources remain explicit; every score is
provisional. See [[docs/decisions/ADR-011 - Grounded review and saved result boundaries]].
T032 adds local Eyecite occurrence extraction in the contained citation worker.
Parent-supplied paragraph IDs/locations are checked against canonical extraction;
returned raw slices/anchors are revalidated before atomic writes. A dedicated
partial Citation-only path retains parser ambiguity/unsupported formats without
asserting source verification. Migration 0004 stores parser metadata separately
from verification status/authority IDs. Reads are owner scoped, bounded and masked;
total detections/truncation are explicit. No CourtListener/Groq call is registered
for citation extraction. See
[[docs/decisions/ADR-009 - Local citation occurrences before source verification]].
IntakeGuard authenticates server-stored bearer hashes/expiry before reading private
bodies, bounds input/deadline/rate buckets, and rejects invalid origins. Browser
credentials are omitted; no ambient cookies/credentialed CORS are used.
AnonymousSession and Analysis.document_snapshot are migration 0003, verified on
SQLite/offline dialect SQL, not live Neon. PostgreSQL calls have connection/pool/
statement/lock bounds, whose hosted suitability still needs measurement.
The PDF child strips provider credentials and has OS-specific resource limits;
this is not an OS privilege sandbox. A disposable localhost preview migrates only
its own temporary SQLite database. Public intake stays off and the original
single-process/Render-ephemeral limitations still apply. See
[[docs/decisions/ADR-007 - Private preparation boundary]].

User-approved UI planning: image-backed centered filing composer, Text/PDF/Demo
tabs and proposed GSAP motion. Font and HD image are supplied; the user's logo
is now rendered in the functional shell. [[docs/product/UI direction]] owns the
final visual plan. T016 adds a read-only reviewed demo adapter with hash-bound
AI-review provenance and source excerpts. No analysis engines are executed by
opening it. Product continuation removes active hackathon timing, not security
or quality gates; see [[docs/decisions/ADR-005 - Product continuation and reviewed demo]].
