---
type: session
status: completed
date: 2026-09-28
tags: [sessions, persistence, privacy, lifecycle]
---
# Private analysis lifecycle cleanup

## Task and scope
T013 in [[TODO]]. User requested immediate continuation after the reviewed sample,
durable context recovery through the vault, and preservation of future widget/grid/
page motion plans. No custom frontend design or analysis engine work in this task.

## Changes
Added an opaque unique Analysis file UUID and non-table-rewriting 0002 migration.
AnalysisLifecycle coordinates PDF creation compensation, owner-scoped file-first
deletion, bounded expired-row cleanup and interrupted-job recovery. Existing
committed stages/evidence survive failed stages and interrupted execution.

Recoverable storage uses one dedicated absolute private root, process lease and
hash-bound metadata receipts. It restores registered files after abrupt termination,
rejects foreign/tampered material and retries deletion without recursively walking
unowned paths. One failed file does not stop attempts on other files. File retention
is one hour; recorded expiry survives restart subject to clock/filesystem limits.

Application lifespan owns sweeps and shutdown. Default shell has no DB dependency.
Explicit recoverable-root configuration activates background DB recovery and
expiry cleanup without waiting for a new upload. File sweeps precede DB operations
and retry after DB failure. Shutdown drains cleanup before closing storage/engine.
Safe warning logs exclude raw exception messages. No private HTTP route is enabled.

Updated canonical setup, module/architecture notes, SRS clarification and TODO.
Recorded [[docs/decisions/ADR-006 - Retryable private lifecycle cleanup]] and
[[docs/feedback/FB-004 - Durable context and additional motion]]. Detailed motion
specification remains pending; no new animations were authored.

## Verification
- `npm run test:api`: 233 passed, two platform-dependent skips. Includes actual
  subprocess `os._exit` recovery, lease contention, receipt/content/link tampering,
  failed-delete retry, creation/commit compensation, expiry and stage preservation.
- Populated SQLite migration upgrade/downgrade preserves existing parent/child
  data; PostgreSQL offline migration SQL and schema/model checks pass in this suite.
- `npm run lint:api`: all checks passed.
- `npm run test:e2e` with installed Chrome: eight desktop/mobile checks passed for
  health, navigation, disabled intake, reviewed sample/reset and failure/retry.
- `git diff --check`: passed; existing OpenAPI CRLF normalization warning only.

Existing Starlette/httpx deprecation remains; new populated-migration tests also
emit Python's SQLite datetime-adapter deprecation warning. Neither is claimed
resolved. No provider calls or credits spent by these checks.

Not run: new migration against live Neon, production schema changes/deployment,
Linux process-lock branch, hosted private filesystem/ACL tests, power-loss recovery,
confidential-filings tests or actual legal-engine execution. Frontend unit/build
checks were not repeated in this backend-only task; browser regression was run.

## Blockers and next step
No blocker to local T013 completion. Work remains local; no commit, push or deploy.
Next ordered task is T017 HTTP streaming/body limits, privacy-safe parser logging,
execution isolation and exposure checks, followed by T018 anonymous session
transport/ownership, origin protection and abuse/concurrency caps. Public submissions
must remain disabled until the applicable gates are verified together.

Retain the stable private root on one process/replica; Render ephemeral disk is not
durable upload storage. Best-effort deletion/TTL is not secure erasure or a hard
expiry SLA; normal shutdown purges original PDFs while DB results can remain until
expiry. See ADR-006 for database/file consistency and operational limits.

## Related
[[apps/api/src/filingguard/db/models/README]];
[[apps/api/src/filingguard/integrations/storage/README]];
[[apps/api/src/filingguard/modules/analyses/README]];
[[docs/knowledge/Documentation Workflow]]; [[docs/product/UI direction]].

[[docs/sessions/Index]] | [[TODO]]
