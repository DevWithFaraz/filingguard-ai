# evidence

Priority: P0 capture; P1 rich UI. Tasks: T011, T040-T041, T102 in the root TODO.md.

Preserve document locations, source identity, passages and method metadata.

Persisted source snapshots and spans in; traceable evidence references out. Validate excerpt identity.

Implemented: typed provenance and persist_evidence/finding_evidence services.
Evidence may exist without a warning. Preserve the original snapshot, SHA-256,
half-open Unicode-code-point offsets, excerpt, timestamp, method and optional
model/prompt/profile identity. External evidence requires URL, authority and
external ID; rule evidence requires profile/rule/version. Never embed credentials
in source URLs. Validate excerpt identity before saving and on retrieval.

The persistence service writes through an owner-scoped stage transaction and
retains immutable snapshot text. Evidence records reference their analysis; DB
composite FKs prevent cross-analysis joins. Original document locations and
triggering entities are optional for system evidence, captured when available.
Browser adapters must convert code-point offsets to UTF-16 indices, not directly
slice JavaScript strings using Python offsets.

Verified: SQLite finding/evidence round trip, foreign-owner rejection and hash
mismatch rollback; isolated Neon round trip. No source-retrieval/provider adapter,
privacy masking or lineage UI is implied. Retention of snapshots is subject to
analysis expiry/deletion; scheduled cleanup remains integration work.

October 10 integration extends this foundation: the parent validates returned
finding/evidence relation IDs and source hashes/slices before stage persistence.
Document evidence may omit a source authority when it proves the filing text;
opinion/AI source evidence must match the finding's authority. V3 semantic output
selects immutable source-unit IDs and binds original excerpts/positions locally.
Owner-scoped saved evidence/result/report views mask complete snapshots before
clipping and expose method/model/prompt/retrieval metadata. Deletion/expiry remain
analysis-scoped. See [[docs/sessions/2026-10-10 - Grounded review verification]] and
[[docs/issues/BUG-014 - Filing evidence incorrectly required source authority]].

[[docs/decisions/ADR-004 - Truthful contracts and scoped evidence]],
[[docs/sessions/2026-09-27 - Contracts persistence and UI planning]].
