---
type: decision
status: accepted
date: 2026-09-28
tags: [decisions, persistence, privacy, lifecycle]
---
# Retryable private lifecycle cleanup

## Context
T013 requires stage rollback isolation and deletion of analysis-owned records and
private files. A process-local file registry cannot recover files after abrupt
termination. The existing shell must retain database-independent liveness, with
public intake disabled until T017/T018 protection is connected.

## Decision and alternatives
Persist only an opaque unique file UUID on Analysis, not a client path. The new
0002 migration adds this nullable field without rewriting existing parent tables.
AnalysisLifecycle owns file creation compensation and file-first database deletion.
If file deletion fails, retain the DB row for retry; DB cascades remove its children
after successful file cleanup. If DB commit fails after file deletion, the row can
remain without its original PDF; retry accepts an already absent file. These are
two coordinated resources, not one atomic transaction or an undelete guarantee.

Use one server-configured absolute private directory with an ownership marker,
exclusive process lease, bounded UUID namespace and hashed metadata receipts.
Restore only identity-validated files; reject foreign/tampered material. Remove
recognized crash leftovers only inside that flat owned directory. Never recursively
delete arbitrary folders or scan the global temporary directory.

Keep the default public shell on process-local storage, with no DB initialization.
Explicit recoverable-storage configuration activates threaded lifecycle recovery
and expiry sweeps. Recover queued/running work as interrupted once before new work;
preserve committed stage results. File sweeps precede DB operations, retry errors
and still execute after DB failure. Each DB sweep considers up to 100 expired rows.
One failed file does not prevent attempting cleanup of other registered files.
Shutdown drains the cleanup task and attempts file purge before releasing the lease.

Rejected for this stage: deleting DB rows before files (loses retry references),
random orphan-directory scans (unsafe ownership), and introducing a distributed
worker/object-storage system before the single-process workflow is complete.

## Consequences
The root must remain stable, private and outside served/synced paths. One API
process/replica only; lease contention fails closed. Recovery depends on the same
filesystem and valid receipts; Render's ephemeral disk is not durable storage.
Normal shutdown deletes original PDFs even when persisted results remain until
expiry. Reads fail when bytes are gone; do not silently reconstruct originals.

Deletion is best effort with retries, not secure erasure or a hard expiry SLA.
Database stalls, OS deletion failures and service downtime can delay cleanup.
Windows privacy still depends on inherited ACLs; disk encryption and production
access/retention assurance are not established by this work. HTTP session ownership,
bounded intake/abuse controls and parser isolation remain T017/T018 release gates.
No public analysis endpoint is enabled and no production migration is applied.

## Evidence and verification
Local tests cover actual subprocess abrupt exit and registry recovery, exclusive
leases, tampering, expiry, deletion retries, rollback compensation, preserved stage
output and a populated SQLite migration upgrade/downgrade. Default-shell health
remains independent of DB availability. PostgreSQL offline migration SQL is tested;
this new migration has not been applied to Neon.

Locking uses Python's documented
[Windows nonblocking byte locks](https://docs.python.org/3/library/msvcrt.html#msvcrt.locking)
and [POSIX flock](https://docs.python.org/3/library/fcntl.html#fcntl.flock).
The Windows branch is exercised locally; the POSIX branch requires Linux CI checks.

## Related
[[TODO]] T013, T017, T018; [[docs/decisions/ADR-004 - Truthful contracts and scoped evidence]];
[[docs/architecture/stack]];
[[apps/api/src/filingguard/db/models/README]];
[[apps/api/src/filingguard/integrations/storage/README]];
[[apps/api/src/filingguard/modules/analyses/README]].

[[docs/decisions/Index]]
