# Persistence

Related: [[TODO]] (T010/T013), [[FilingGuard_AI_SRS#11. Data Model]],
[[docs/architecture/stack]], [[apps/api/src/filingguard/modules/evidence/README]].

Implemented: Analysis, DocumentSegment, Citation, Authority, Claim,
ClaimAuthorityLink, Quote, Finding and EvidenceRecord. UUIDs work on SQLite and
PostgreSQL. JSON uses generic SQLAlchemy JSON with a PostgreSQL JSONB variant.
Every private record belongs to an analysis, including authority snapshots and
evidence without a finding. Analysis deletion cascades through all eight child
tables; finding deletion cascades only through its attached evidence. Composite
`(analysis_id, entity_id)` foreign keys reject cross-analysis references. Scoped
unique keys and analysis lookup indexes keep relationships queryable.

`session.py` exposes explicit engine/factory creation and a transaction context.
There is no global engine/session or default-shell startup connection. Settings/env/dotenv
resolve DATABASE_URL privately; Alembic stores no URL and configures no logging.
Use an injected `config.attributes["connection"]` for isolated migration tooling.
The caller owns engine disposal. SQLite connections always enable foreign keys.
Stored timestamps normalize to aware UTC; naive timestamp inputs are rejected.
Health remains independent of database connectivity.

`AnalysisRepository` requires the owner hash and analysis UUID on reads, stage
writes and deletion. Missing, foreign-owned and expired analyses all fail with
AnalysisNotFound. T018 now issues/hashes opaque tokens at the HTTP boundary; no raw
session token is stored. Internal `expired_ids`/`delete_expired` maintenance is
separate from public owner-scoped access, with a bounded batch and expiry recheck.

Each `stage_update` opens a fresh transaction and locks the analysis on PostgreSQL.
Its `StageWrite.add` appends output, flushes parents before children and rejects
foreign-owned records. Stage state is a validated StageState JSON object keyed by
one of the seven StageName values, including explicit reason, coverage and
applicability. Incomplete states need a reason. New analyses and verdicts default
to `not_run`; stage state defaults to an empty object, and score/risk stay nullable.
Verdict/status checks match the parent analysis contracts exactly. A failed stage
rolls back its new work and status change, preserving previously committed results.
Record its failure/partial status in a subsequent, separate stage transaction.

Evidence has nullable `finding_id`, `snapshot_text`, URL/hash/retrieval time,
document and source offsets, excerpt, method/model/prompt versions and JSON
source_metadata. Store `rule_version`, `court_profile_id`, `rule_id`, `external_id`,
`offset_unit` and `provenance` in source_metadata. The typed evidence service
requires and validates a source snapshot for new evidence. Nullable legacy fields
do not imply verified evidence. Provenance columns are immutable through ORM
updates; linking an existing record to a finding is allowed and still FK-scoped.
Append a new record for a new retrieval/method. Direct Core SQL is a trusted
migration/test escape hatch and bypasses the ORM immutability guard. Repository
return values are detached; use a session for lazy relationship traversal.

Verified locally: 64 persistence integration cases cover SQLite migration and
downgrade, SQLite/PostgreSQL offline SQL generation, schema/model agreement,
round trips, every composite FK edge, unknown defaults, scoped expiry, rollback,
stage coverage/reasons, immutable snapshots and deletion cascades.
Command: `.venv/Scripts/python.exe -m pytest tests/integration/test_persistence.py -q`
from apps/api. The parent also verified a fresh isolated Neon schema: migration,
nine-entity round trip, validated evidence and cascade deletion passed; only the
disposable test schema was removed. No public/production tables were migrated.
See [[docs/sessions/2026-09-27 - Contracts persistence and UI planning]].

T013 adds Analysis.stored_file_id: nullable, unique, indexed UUID4, never a filesystem
path or public response field. Migration 0002_analysis_file preserves populated
parent/child rows on SQLite upgrade and downgrade. Original-input fingerprints are
SHA-256 of PDF bytes for file creation; text inputs use the original UTF-8 text.
Extracted text/snapshot hashes are separate evidence identities, not substitutions
for the original upload fingerprint.

`delete_analysis` requires a file-cleanup callback for file-backed records. File
failure rolls back deletion; a DB commit failure can leave a row whose file is
already gone, and retry is deliberately idempotent. `interrupt_pending` marks
abandoned queued/running work without erasing committed stages/evidence. The app
owns these operations through [[apps/api/src/filingguard/modules/analyses/README]].
Session authorization is implemented locally; hosted integration remains pending. Current
PostgreSQL verification predates 0002; its offline SQL is tested, not a live Neon
upgrade. See [[docs/decisions/ADR-006 - Retryable private lifecycle cleanup]].

Migration 0003 adds Analysis.document_snapshot (nullable JSON/JSONB) and the
AnonymousSession table (owner_hash primary key, indexed server expiry). No token,
IP or browser identity is stored there. Issuance prunes expired hashes and caps
live sessions at 256. Expiry rejects access immediately; background maintenance
removes expired hashes and analysis rows independently, with file-first cascades.
Session hashes are not analysis IDs or accepted request-body ownership values.
Preparation saves validated canonical extraction separately from stage-state JSON.
Activity emits summaries only; owner-scoped detail exposes the original snapshot.
PostgreSQL connection/pool timeouts are five seconds; statement/lock limits are
10/5 seconds. SQLite has no claim of equivalent hosted timeout behavior.
Fresh/populated SQLite migration, model agreement and preparation round trips
pass; no 0002/0003 production or isolated Neon check has been run this session.
See [[docs/decisions/ADR-007 - Private preparation boundary]].

Migration 0004_citation_extraction adds Citation.extraction_metadata JSON/JSONB.
Its empty default preserves legacy/unrun rows without inventing parser provenance.
New T032 records validate typed parser metadata and exact original spans at the
worker boundary; verification still defaults to `not_run` and authority ID stays
null. `list_citations` is owner/expiry scoped, ordered by original location and
limited to 200 rows. The stage records total detected count/truncation separately.
Populated SQLite 0003 -> 0004 -> 0003 preserves citations and scoped foreign keys;
schema/model agreement and offline dialect SQL are regression checked. No live
Neon/production 0004 migration is authorized or performed. See
[[docs/decisions/ADR-009 - Local citation occurrences before source verification]].
Migration `0005_table_of_authorities` extends the findings type check to include
`table_of_authorities`. Migration `0006_claim_corrections` adds
`Claim.correction_history` JSON/JSONB (default `[]`) so user edits never rewrite
`Claim.text`. Local tests upgrade through `0007_local_identities`; hosted Neon remains at
`0004_citation_extraction` until an explicit production migration is approved.

Migration `0007_local_identities` adds optional `local_identities` (unique username,
hashed secret, unique claimed `owner_hash`) and `identity_sessions` (bearer SHA-256
to claimed owner, 55-minute expiry). Anonymous sessions are unchanged. This is a
local recovery claim, not production authentication. See
[[apps/api/src/filingguard/modules/identity/README]] and
[[docs/decisions/ADR-016 - Optional local identity claim]].
