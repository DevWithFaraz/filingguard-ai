# analyses

Priority: P0. Tasks: T009, T012-T013, T016 and T023-T027 in [[TODO]].

Orchestrate stages, persist status/partial results, enforce limits and recover interrupted jobs.

Typed stage results in; persisted analysis state, findings and coverage out. Own sequencing, not feature logic.

Implemented foundations: schemas.py separates lifecycle/stage execution from
citation/proposition/quote verdicts. Defaults remain not_run; confidence is
uncalibrated, scores nullable/provisional, coverage partitioned and reconciled.
Stages can skip only if explicitly inapplicable, with no eligible checks and a
reason. Missing/failed source access is not a favorable or not-found result.
Evidence references and AI version metadata are required for substantive verdicts.

demo.py admits only explicit demo selection, a server-owned recognized fixture,
human-reviewed manifest and exact document/source hashes. Altered arbitrary input
never receives starter results. Current unreviewed starter remains disabled.
This remains a separate admission gate for human-reviewed result replay.

demo_preview.py is the T016 multi-authority read-only adapter. review.json binds
seven artifacts by original byte hashes, and source text/raw hashes and all
filing/source spans are checked before returning typed examples. Explicit demo
mode and recognized ID are required; changed caller input is rejected. Provenance
is delegated_assistant, execution is always not_run, and five conditional judgments
are visible. This adapter neither runs feature engines nor creates analysis rows.
The fixed demo GET route remains public; invalid resources fail safely with 503.
Legacy unreviewed material cannot pass this adapter. The receipt is trusted
repository metadata, not a signature or arbitrary client approval.

`lifecycle.py` coordinates admitted PDF bytes with owner-scoped persistence.
Creation compensates file writes if DB creation fails. Deletion removes registered
bytes before cascading DB deletion; failures retain retryable state. Expired DB
rows are swept in batches up to 100. Startup recovery marks queued/running jobs and
their pending stages interrupted, preserving completed stages and saved evidence.
It does not rerun jobs or implement the analysis engine scheduler.

`core/runtime.py` owns the storage lifecycle, threaded periodic sweeps and shutdown.
The default shell never initializes persistence. Explicit recoverable-root
configuration initializes recovery/cleanup in a worker thread, retrying failures
without logging raw exception text. File expiry does not require a working DB.
Private routes authorize before using the lifecycle and are off by default.
See [[docs/decisions/ADR-006 - Retryable private lifecycle cleanup]].

Stage transactions live in [[apps/api/src/filingguard/db/models/README]].
`orchestrator.py` now owns a single in-process review worker and shares admission
with document preparation. `queue_review` atomically saves queued legal stages before
the 202 response; the worker saves running and terminal stage states independently.
Duplicate starts and active deletion conflict; wrong-owner IDs remain 404. A failed
stage is recorded without suppressing independent later checks, preserving earlier
commits. `runners.py` registers privacy/profile checks, local citation/claim
extraction and quote forensics. Explicit flags select the CourtListener citation
worker and Groq grounded proposition worker; both external flags default off.
The normal `/run` accepts live input and hash-revalidated curated demo input, but
disabled providers/missing sources yield explicit partial coverage. Owner-scoped
findings/results/evidence expose masked slices and recorded source/method metadata.
Graph and exports derive from saved output without provider calls. `/rerun`
creates a fresh prepared live ID without erasing prior results. Scores are
provisional and gated on evaluated substantive checks. Provider execution uses
the T024 boundary. `demo_sources.py` connects exact curated-v1 demo analyses to
three reviewed public opinion snapshots using `cached-public-source-v1` receipts.
Its hash-bound admission rejects altered text/identity/source material; live mode
never receives these sources as an outage fallback. Feature engines compute fresh
findings, independent of expected scenario labels. Reset deletes private output.
The delegated review remains distinct from legacy human-reviewed result replay.
See [[docs/decisions/ADR-012 - Exact sample source replay with fresh findings]].
No public intake is enabled; development requires explicit opt-in.
See [[contracts/README]] and [[docs/decisions/ADR-004 - Truthful contracts and scoped evidence]].

T019 private preparation routes create rows/segments with canonical extraction
and initial not_run legal status. A private demo uses the verified server-owned
filing, not replayed expected findings. T016 actual engine replay remains pending.
The current single slot spans preparation and local-review jobs;
Source verification remains unavailable. Reports/graphs must adopt the same ownership checks
when implemented; no unowned result endpoint is authorized by existing schemas.
See [[docs/decisions/ADR-007 - Private preparation boundary]].

T024 adds `execution.py` and `worker.py`: importable stage functions receive a
detached analysis snapshot plus a shared `ProviderBudget`, return typed results
over bounded JSON pipes, and never write to the DB. Local privacy/profile checks
run first; unavailable engines are static metadata without process startup.
Windows Job containment or a POSIX process group terminates the local worker tree
on stage/overall cutoff or shutdown. Saved stages survive; remaining stages become
unavailable on deadline or interrupted on shutdown, releasing the admission slot.
Defaults are a 90-second work cutoff, 30-second stage cutoff and 60 total provider
attempts. Startup counts toward the cutoff; separately bounded DB finalization is
not included in a claim of exact end-to-end duration. Unknown killed-worker quota
receipts consume the remainder conservatively. Provider registration is opt-in.
Shared Windows PDF-helper defaults remain unchanged. POSIX/hosted checks are pending.
See [[apps/api/src/filingguard/integrations/providers/README]] and
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]].

T032 originally added a dedicated partial-output path for citation extraction. Partial
citation records must be Citation rows with verification `not_run`, no authority
ID, valid typed parser metadata and zero evaluated/source-complete coverage. Other
incomplete stages now use their own typed partial paths with provenance validation.
Snapshot-matched segments and allowlisted prior entity rows pass through bounded
IPC without DB access. Stage-specific credentials pass only through private stdin;
the child does not load local environment files. The parent validates slices/anchors before
atomic persistence. `/citations` exposes owner-scoped masked occurrences only after
the citation stage is terminal, avoiding mixed pre/post-commit snapshots. Zero
detections has an explicit limited-parser caveat, never a clean-filing claim.
See [[apps/api/src/filingguard/modules/citations/README]] and
[[docs/decisions/ADR-009 - Local citation occurrences before source verification]].

T036–T051 extend this boundary to source receipts, claim links, grounded verdict
updates and quote evidence. JSON input/output is bounded at 16 MiB; entity and
snapshot sub-budgets preserve earlier results. Claim/proposition updates validate
original relations before transactional persistence. Findings show unavailable
checks without promoting them to passes. See
[[docs/decisions/ADR-011 - Grounded review and saved result boundaries]],
[[apps/api/src/filingguard/modules/claims/README]],
[[apps/api/src/filingguard/modules/propositions/README]],
[[apps/api/src/filingguard/modules/quotes/README]] and
[[apps/api/src/filingguard/modules/reports/README]].
