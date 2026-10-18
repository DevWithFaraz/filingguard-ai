---
type: session
status: complete
date: 2026-10-18
tags: [sessions, architecture, analysis, database, lifecycle, queue]
---
# 2026-10-18 - Durable job execution and transactional worker leases

## Task and scope
Complete **T109**: Durable job execution (worker/queue, leases, idempotency, crash recovery, and bounded retries).
Prepares review execution for durable coordination without introducing external broker dependencies,
preserving the lightweight serverless PostgreSQL architecture, zero-migration relational schema compatibility,
and zero raw filing text leakage into logs or telemetry.

## Changes
1. **Architecture Decision Record**:
   - Authored [[docs/decisions/ADR-015 - Durable job execution and transactional worker leases]].
   - Evaluated external brokers (Celery, Redis, RabbitMQ, Temporal) and selected database-backed
     transactional leases using SQLAlchemy row locking (`with_for_update()`) in PostgreSQL and SQLite.
   - Encapsulated lease state (`worker_id`, `lease_expires_at`, `retry_count`) inside `stage_states["lease_metadata"]`
     to avoid breaking Alembic migrations. Updated `docs/decisions/Index.md`.

2. **Database Repository (`apps/api/src/filingguard/db/repository.py`)**:
   - `acquire_lease(owner_hash, analysis_id, worker_id, lease_seconds=120) -> bool`: Atomically claims
     a queued or expired running analysis, setting status to `running`, worker ID, and expiry timestamp.
   - `renew_lease(owner_hash, analysis_id, worker_id, lease_seconds=120) -> bool`: Atomically extends the
     lease for the holding worker during execution.
   - `release_lease(owner_hash, analysis_id, worker_id) -> None`: Clears active worker ID and lease expiry.
   - `recover_orphaned_leases(now=None, max_retries=2) -> tuple[int, int]`: Scans running analyses with expired
     leases. For analyses with `retry_count < max_retries`, increments `retry_count`, clears lease, resets
     running stages to `queued`, and resets analysis status to `queued` (rescheduled count). For analyses
     exceeding `max_retries`, clears lease and marks the job and pending stages `interrupted` (interrupted count).

3. **Lifecycle Coordination (`apps/api/src/filingguard/modules/analyses/lifecycle.py`)**:
   - Updated `recover(now=None, max_retries=2) -> tuple[int, int]` to delegate to `recover_orphaned_leases()`,
     emitting structured operational counts (`retention.recover rescheduled=%d interrupted=%d`) without
     leaking sensitive filing data.

4. **Review Orchestrator (`apps/api/src/filingguard/modules/analyses/orchestrator.py`)**:
   - Added worker ID generation/parameter (`self.worker_id = worker_id or f"worker-{uuid4().hex[:12]}"`).
   - Integrated atomic lease acquisition in `_run_and_release`; safely aborts if another worker claimed the job.
   - Integrated periodic lease renewal in `_run` before each stage and after stage update.
   - Guaranteed lease release in `finally` block upon job completion, failure, or cancellation.

5. **Stage Filtering Hygiene (`intake.py`, `reports/service.py`)**:
   - Updated stage iteration to filter `row.stage_states` by valid `StageName` enum values, ensuring internal
     `lease_metadata` is never mistakenly parsed as a `StageState` contract.

6. **Automated Unit Testing (`apps/api/tests/unit/test_durable_jobs.py`)**:
   - Created comprehensive test suite with 8 tests covering atomic lease acquisition, mutual exclusion,
     renewal, expired reacquisition, bounded crash recovery (retries 0 -> 1 -> 2 -> interrupted), stage
     idempotency and record preservation, orchestrator lease lifecycle, competing workers, and zero telemetry leakage.
   - Updated `test_lifecycle.py` to assert recovery counts tuple.

## Verification
- `npm run lint:api` (`ruff check .`): passed cleanly with 0 errors.
- `uv run pytest tests\unit\test_durable_jobs.py`: 8 passed in 1.65s.
- `uv run pytest tests\integration\test_lifecycle.py tests\integration\test_orchestrator.py`: 13 passed in 28.49s.
- Full test suite: 772 backend tests passed with 0 failures (2 Windows host skips).
- Checks not run: hosted Neon deployment / production branch migration (not needed because no schema migration was required; local verification is complete).

## Blockers and next step
No blockers. T109 is complete. Next active task in Phase B: T106 (verified real court profiles).

## Related
[[docs/decisions/ADR-015 - Durable job execution and transactional worker leases]],
[[docs/decisions/Index]], [[TODO]], [[apps/api/src/filingguard/modules/analyses/README]],
[[docs/sessions/Index]].
