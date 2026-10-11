# Shared API contract

Pydantic/FastAPI owns the schema. Run `npm run contracts:export`, then
`npm run contracts:generate` after installing dependencies. Commit the OpenAPI JSON
and generated browser declarations with endpoint changes; do not edit generated
types by hand. Health, read-only reviewed demo, capabilities/court-profile metadata,
opt-in private preparation/session and owner-scoped review status/run/findings/
citations/rerun routes are runtime routes today. The exporter
also includes the implemented domain contracts as components: analysis/stages,
coverage, findings, evidence and future v1 request/response boundaries. The
`x-filingguard-contract-status` annotation distinguishes schemas from enabled
operations. Default intake is disabled. Opt-in local review does not imply a
completed legal analysis; external source checks remain unavailable.

HTTP errors use the ApiError envelope, a server-generated request UUID and no-store
headers. Validation/internal errors do not echo inputs or provider exceptions.
JSON booleans are strict. Never accept an owner/session hash from a request body.
POST /api/v1/sessions requires an allowed browser Origin and returns an opaque
bearer/expiry with 201/no-store. All /analyses operations require Authorization:
Bearer token, owner hash lookup and unexpired server state. Foreign IDs return 404.

POST /analyses/text consumes TextSubmission; POST /analyses/file consumes raw PDF
bytes with `court_profile_id`/`ai_used` query metadata and encoded X-Document-Name
header; POST /analyses/demo consumes only a recognized server-owned fixture ID and
explicit demo mode. Each returns PreparedDocument with 201/not_run, not queued
legal results. GET /analyses returns DocumentSummary[] without text; GET/DELETE
/analyses/{UUID} are owner-scoped. Later reads return the saved execution status.
GET /analyses/{UUID}/status returns stage coverage and a provisional score marker;
POST /analyses/{UUID}/run returns 202/queued only after an owned prepared analysis
is persisted as queued and all stage runners are registered. Duplicate
starts return 409. Demo runs revalidate the server-owned curated fixture. Prefix every relative
operation with /api/v1. Capability/profile requests do not connect to DB/providers;
intake_enabled reports configuration, not DB readiness. Default intake is off and
legal_analysis_enabled reports configured external review flags, not provider
readiness. Saved graph/report/results and finding evidence are runtime private
routes. Active terminal-only reads return 409, foreign/expired resources 404. See
[[docs/decisions/ADR-007 - Private preparation boundary]].

Opt-in local review now registers privacy, synthetic disclosure and citation
extraction/claims and quote forensics; providers are independent opt-ins. `/run` also admits the
hash-revalidated server-owned curated demo, not caller-supplied starter findings.
`GET /analyses/{UUID}/findings` returns masked local findings, not raw evidence.
`POST /analyses/{UUID}/rerun` creates a fresh prepared live ID. Default intake
remains off and no completed legal analysis is implied.

`GET /analyses/{UUID}/citations` returns SafeCitationsResponse: terminal extracted
occurrences (max 200), exact original locations, masked display text, optional
normalized text, parser metadata and a distinct verification status. Before
extraction it returns `not_run`/no occurrences; failed/unavailable work has no
extraction rows. Extracted occurrences remain unverified, and the stage stays
partial unless source checks run with configured authority access. Coverage gives total detected count
and explicit truncation. Zero detected supported formats is skipped with an
incomplete-coverage caveat. Legacy rows with empty parser metadata have null
extraction metadata, not fabricated provenance. Private authorization, expiry,
no-store/error envelopes and whole-snapshot masking apply to this route too.
No raw provider data, arbitrary fetch URL or score is exposed. See
[[apps/api/src/filingguard/modules/citations/README]] and
[[docs/decisions/ADR-009 - Local citation occurrences before source verification]].

See [[apps/api/src/filingguard/modules/analyses/README]],
[[apps/api/src/filingguard/modules/evidence/README]], [[TODO]] (T009-T012).
