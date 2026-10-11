---
type: decision
status: accepted
date: 2026-09-27
tags: [contracts, persistence, evidence]
---
# Truthful contracts and scoped evidence

## Context and decision
T009-T013 need unknown/partial results to remain distinct from successful legal
checks, with finding provenance and private analysis ownership. SRS examples were
not sufficient as production invariants; the evaluator's experimental labels are
not the legal API contract.

Use typed Pydantic execution/verdict/coverage contracts with explicit applicability
and evidence prerequisites. Aggregate counts reconcile with stages. Numerical
confidence is uncalibrated with a stated method; unexamined results have unknown
confidence. No eligible/evaluated checks means no integrity score. API envelope
errors carry a server-generated UUID, never raw input/provider exception details.
Only enabled operations appear in OpenAPI paths; declared future boundaries are
components, not pretend endpoints.

Analysis is the private aggregate owner. All child records, including authorities
and evidence, have analysis IDs and scoped composite FKs. Retain each stage in a
separate transaction; failure rolls back new work, not earlier stage output.
Evidence can exist without a warning. Save original source snapshots, validated
SHA-256 and half-open Unicode-code-point spans, retrieval/method/model/profile
provenance; create new evidence for a new snapshot rather than mutate old evidence.

## Alternatives and limits
Rejected default-green enums, scores of 100 for zero coverage, polymorphic foreign
IDs and private authorities in a globally shared cache. P0 duplicates scoped
source material rather than introducing shared-cache authorization complexity.
JavaScript UTF-16 offsets require conversion at the future browser adapter.
ORM immutability does not constrain trusted Core SQL/migrations. Snapshot retention
and file cleanup need lifecycle integration. Random IDs/CORS are not authorization.

The user confirmed anonymous private sessions for P0, with automatic expiry and
no account signup. Accounts and shared reviews remain P2. Every private status,
finding, graph, report and deletion operation must check session ownership and
expiry; knowing an analysis ID is not sufficient authorization.

Anonymous transport is still proposed for T018: server-issued opaque bearer token
kept in tab-scoped sessionStorage, only its hash/expiry server-side. This avoids
third-party-cookie dependence between Render hosts, but increases the importance
of XSS controls and loses access when the tab session is gone. No session endpoint,
token issuance, rate limiter or submission admission is implemented yet. Expiry
must be enforced server-side independently of browser storage; closing a tab is
not proof of immediate server deletion. Retention/cleanup timing and transport
security still require implementation and verification under T013/T017/T018.

## Verification
September 28 update: the proposed transport below is now implemented for private
document preparation; see [[docs/decisions/ADR-007 - Private preparation boundary]].
Its historical proposal is retained as rationale, not current implementation status.

Typed validators, SQLite migration/downgrade, owner/expiry rejection, cross-analysis
FK rejection, immutable snapshots, stage rollback and cascades pass. An approved
opt-in Neon probe migrated and round-tripped all nine entities/evidence in a
fresh disposable schema, then removed it. Public schema and hosted analysis were
not migrated/enabled. See [[docs/sessions/2026-09-27 - Contracts persistence and UI planning]].

[[docs/decisions/Index]], [[FilingGuard_AI_SRS#11. Data Model]], [[TODO]],
[[contracts/README]], [[apps/api/src/filingguard/modules/evidence/README]],
[[apps/api/src/filingguard/db/models/README]].
