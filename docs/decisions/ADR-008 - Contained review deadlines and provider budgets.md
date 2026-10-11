---
type: decision
status: accepted
date: 2026-10-02
tags: [architecture, analysis, providers, security]
---
# ADR-008 - Contained review deadlines and provider budgets

## Context
T024 needs a work cutoff that stops a stuck stage, not merely an abandoned thread
or an HTTP inactivity timeout. Preserve committed checks and the existing one-job
admission model. The user retains the free-credit-only provider budget.

## Decision and alternatives
The single parent supervisor owns all database transactions. Each executable stage
runs in a short-lived child and exchanges bounded JSON over private pipes, not
pickle, temporary filing files or command-line document arguments. Only trusted
server-registered, importable functions can run. The child receives a detached
snapshot without bearer hashes, storage references or database credentials.
Future adapters must pass their required credentials explicitly through a reviewed
private boundary; the current worker has none and sends no real requests.

Use a Windows kill-on-close Job Object before delivering input, or a new POSIX
process group, with child memory/CPU bounds. Timeout and shutdown terminate local
stage work and descendants. The work deadline defaults to 90 seconds from handoff;
each stage defaults to 30 seconds, including interpreter startup. Database
finalization/cleanup is separately thread-offloaded and retains bounded DB queries;
it is not an assertion that every database write finishes within the work cutoff.
Remote provider computation cannot be cancelled or refunded by killing our client.

On Windows, launch the base interpreter directly with the private virtualenv import
path, avoiding the venv redirector before Job assignment. An independent watchdog
can terminate the tree even while `communicate()` is blocked writing its input.
The OS process-creation call itself is not guaranteed interruptible; the deadline
is enforced once the child exists. Host scheduling and database finalization can
also add latency beyond the work budget, so this is not a real-time API guarantee.

Privacy and court-profile checks run first. Unconfigured/inapplicable stages are
explicit terminal metadata without child startup. Executable completed results
cannot use that shortcut. Persist each result after validating stage state, record
types and analysis ownership. Failures never become favorable legal verdicts.

Use a shared attempt allowance of 60 across stages and at most two provider requests
in flight within the active stage. A killed/crashed worker without an accounting
receipt consumes its remaining allowance conservatively. Later local checks may
still run, but no uncertain quota is spent again.

The fixed-host HTTP boundary accepts only structured paths/parameters for
CourtListener and Groq, refuses redirects, and disables implicit environment proxy
configuration. Requests are capped at 128 KiB and decoded responses at 4 MiB.
HTTPX phase timeouts plus monotonic checks give a cooperative 20-second call
budget; the contained stage supplies hard cancellation. CourtListener allows one
retry for selected transient failures. Groq retries are zero to avoid duplicate
inference/quota consumption. Retry-After is honored, or the call fails when the
wait cannot fit; it is never shortened into an early retry.

Outgoing context helpers cap filing/source passages at 8,000/12,000 code points,
retain original half-open locations, and disclose clipping. Filing masking scans
the whole snapshot before clipping. This is not passage relevance selection,
complete de-identification, legal redaction compliance or an implemented semantic
adapter. T022/T031/T038 remain integration gates.

A thread-only timeout was rejected because it leaves blocked work running. A
distributed worker/queue remains T109; this change does not authorize multi-worker
deployment. Reusing the existing Windows Job helper keeps PDF defaults unchanged.

## Consequences
Interpreter startup adds overhead. Avoid workers for absent engines and keep test
runners separate from test-client imports. The stage IPC currently accepts at most
200 records and 16 MiB output; exceeding either is unavailable, not silent clipping.
Workers have no database access; future feature stages must receive the required
prior persisted context explicitly rather than opening a child DB session.
Containment is not an OS privilege sandbox. Restart recovery remains in-process
and jobs are not durable. Hosted Linux/memory/performance checks remain release gates.

## Evidence and verification
Synthetic tests exercise stuck fake HTTP calls, API liveness/status, saved privacy
findings, shutdown, actual descendant-side-effect cessation, cross-stage attempt
receipts and sanitized errors. Transport tests cover retry/rate limits, shared
concurrency, payload/stream bounds and logging. A fake outgoing filing-context test
checks detected identifiers are masked with original offsets preserved. Exact
session commands/results and platform limits are recorded in
[[docs/sessions/2026-10-02 - Provider budgets and hard deadlines]].

Primary API references consulted: [Python subprocess](https://docs.python.org/3.12/library/subprocess.html),
[Windows Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[HTTPX timeouts](https://www.python-httpx.org/advanced/timeouts/) and
[HTTPX resource limits](https://www.python-httpx.org/advanced/resource-limits/).

## Related
[[docs/decisions/Index]], [[TODO]], [[FilingGuard_AI_SRS]],
[[docs/architecture/stack]], [[apps/api/src/filingguard/modules/analyses/README]],
[[apps/api/src/filingguard/integrations/providers/README]],
[[apps/api/src/filingguard/modules/privacy/README]],
[[docs/issues/BUG-005 - Windows venv worker process limit]].
