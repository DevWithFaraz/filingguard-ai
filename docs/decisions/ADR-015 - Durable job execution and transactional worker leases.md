---
type: decision
status: accepted
date: 2026-10-18
tags: [architecture, analysis, database, lifecycle, queue]
---
# ADR-015 - Durable job execution and transactional worker leases

## Context
Scaling review execution beyond a single in-process thread pool requires worker coordination,
crash recovery, idempotency, and bounded retries. The single-process orchestrator previously
relied on in-memory semaphores and unconditional startup interruption (`interrupt_pending()`).
If an API process restarts or a worker crashes mid-review, incomplete jobs could become
indefinitely orphaned or needlessly fail without an opportunity for bounded recovery, while
concurrent workers could attempt to execute the same analysis simultaneously.

At the same time, FilingGuard AI must maintain a zero-cost serverless deployment on Neon
PostgreSQL and Render, with full local SQLite test compatibility, zero private filing data leaked
into telemetry, and zero breaking schema migrations.

## Decision and alternatives
1. **Evaluated alternatives**:
   - *External broker (Celery / Redis / RabbitMQ / Temporal)*: Rejected. Introducing a separate
     message queue or workflow orchestrator adds external infrastructure, network hops,
     operational complexity, credential sprawl, extra failure modes, and breaches the zero-cost
     serverless PostgreSQL architecture.
   - *Database-backed transactional leases (Selected)*: Store worker lease metadata
     (`worker_id`, `lease_expires_at`, `retry_count`) directly on the analysis record.
     Worker coordination and mutual exclusion are achieved via atomic SQL transactions and
     row-level locking (`with_for_update()`) in PostgreSQL and SQLite.

2. **Schema compatibility & lease storage**:
   - Lease metadata is encapsulated within an internal structure in `Analysis.stage_states`
     under `"lease_metadata"`. This preserves full relational schema compatibility across
     Neon PostgreSQL and SQLite without requiring an Alembic schema migration.
   - Stage iteration and serialization filters (`intake.py`, `reports/service.py`) filter
     by valid `StageName` keys, ensuring internal lease metadata never contaminates domain
     stage models or client responses.

3. **Lease lifecycle and mutual exclusion**:
   - `acquire_lease(owner_hash, analysis_id, worker_id, lease_seconds=120) -> bool`:
     Atomically checks whether the analysis is `queued` or `running` with an expired lease.
     If available, transitions to `running`, assigns the `worker_id`, sets the expiration
     timestamp (`now + lease_seconds`), and commits. If another worker holds an active lease,
     acquisition safely returns `False`.
   - `renew_lease(owner_hash, analysis_id, worker_id, lease_seconds=120) -> bool`:
     Atomically extends the active lease for the owning worker during stage transitions.
   - `release_lease(owner_hash, analysis_id, worker_id) -> None`:
     Clears the active worker lease (`worker_id=None`, `lease_expires_at=None`) in a `finally`
     block when a review completes, fails, or is interrupted.

4. **Idempotency, stage preservation, and crash recovery**:
   - Each stage continues to commit its results independently in parent-before-child order.
   - `recover_orphaned_leases(now=None, max_retries=2) -> tuple[int, int]`:
     Finds `running` analyses whose leases have expired (or are missing).
     - If `retry_count < max_retries`: increments `retry_count`, resets `analysis.status` to
       `"queued"`, and clears the active worker lease so a worker can resume execution. Completed
       stages remain intact (`completed`), preserving partial results idempotently without
       re-running completed work.
     - If `retry_count >= max_retries`: transitions `analysis.status` to `"interrupted"`, clears
       provisional scores, and marks incomplete stages as `"interrupted"`.
     - Returns `(rescheduled_count, interrupted_count)`.

## Consequences
- Workers must periodically renew their leases if stage processing exceeds `lease_seconds`.
  The orchestrator renews leases before executing each stage.
- Mutual exclusion is guaranteed through database transactions without external locking services.
- Transient crashes (such as container restarts or worker process recycling) automatically
  reschedule up to 2 times without losing previously saved citation, claim, or quote evidence.
- Terminal failures after retry exhaustion transition predictably to `interrupted`.

## Evidence and verification
- Unit tests in `tests/unit/test_durable_jobs.py` verify:
  - Atomic lease acquisition and mutual exclusion (two workers cannot lease the same job).
  - Periodic lease renewal during execution.
  - Crash recovery with bounded reschedule (`retry_count < max_retries`).
  - Terminal interruption when max retries are exceeded.
  - Stage idempotency and preservation of previously committed stage results across recovery.
- Zero raw filing text or sensitive tokens are exposed in logs or lease records.
- All backend lint checks (`ruff check .`) and test suites pass cleanly.

## Related
[[docs/decisions/Index]], [[TODO]], [[FilingGuard_AI_SRS]],
[[docs/architecture/stack]], [[apps/api/src/filingguard/modules/analyses/README]],
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]].
