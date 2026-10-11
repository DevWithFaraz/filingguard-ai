---
type: session
status: completed
date: 2026-10-02
tags: [sessions, analysis, providers, security]
---
# Provider budgets and hard deadlines

## Task and scope
T024, authorized by the user's "okay start" after the next-task explanation.
One bounded transport subagent implemented four isolated files; the parent
implemented stage containment, integration, masking helpers, tests and docs.
No frontend behavior, real credentials, public enablement or database schema changed.

## Changes
Executable review stages now run in contained child processes with bounded JSON
IPC. The parent retains database ownership, per-stage transactions and one-job
admission. Privacy/profile checks run first. Missing engines are explicit static
metadata, never executed/favorable findings. Stage/overall deadlines and shutdown
terminate local work and descendants; saved checks survive and pending checks
become unavailable/interrupted. Windows uses a direct base interpreter, Job Object
and independent watchdog, including blocked stdin writes. Existing PDF defaults
are unchanged. Configured defaults are 90/30 seconds and 60 provider attempts.

Fixed-host HTTPX transport provides two shared in-flight calls, atomic attempt
reservation, cross-stage accounting, bounded request/decoded response bytes,
cooperative per-call deadlines, one selected CourtListener retry and no Groq
retry. Retry-After cannot be shortened into an early retry. Redirects, environment
proxies and cookie replay are disabled; errors/logging exclude provider bodies.
Killed workers without receipts exhaust the remaining quota conservatively.

Bounded context helpers preserve original locations and explicit clipping.
Filing masking detects over the full snapshot before slicing. A fake outgoing
JSON test verifies detected identifiers are absent, including a clipped identifier.
Actual semantic request construction is not implemented; T022/T031 remain open.
No credential is sent to the current worker. Future adapters need a reviewed
private credential/prior-result input boundary, not child database access.

## Verification
- `node scripts/api.mjs run pytest -q --durations=5`: **439 passed, two skipped**,
  four deprecation warnings, 123.76 seconds. Skips are host symlink creation and
  POSIX storage permissions on Windows; not missing deadline coverage.
- Focused deadline/orchestrator suite: **18 passed**, 91.67 seconds. Exercises
  actual stuck fake transports, responsive health/status, retained masked privacy
  findings, overall cutoff, shared attempts, shutdown, descendant side effects,
  typed evidence IPC, spawn/input failures and large-input pipe cancellation.
- Isolated transport suite: **149 passed**. Passage suite: **eight passed**.
  Both are also included in the full API result above, not additional counts.
- API Ruff check and format checks for 17 touched Python files passed.
- Frontend Vitest: **20 passed** on retry. The sandbox initially blocked Vite
  config loading; an outside-sandbox default fork run timed out starting workers.
  The repeat root command included pool flags, but npm did not forward them, so
  the successful run still used the default pool. No frontend config workaround
  or dependency change was made.
- `npm run typecheck`, `npm run lint:web` and `npm run build` passed. Build required
  outside-sandbox configuration access and retains the existing Three.js chunk-size
  warning. `git diff --check` passed with the existing OpenAPI line-ending warning.

Initial integration attempts failed on worker startup/test-wait assumptions and
a malformed word-boundary fixture. Runners were separated from test-client imports,
absent engines stopped spawning workers, API polling respected read-rate limits,
and admission tests held the first stage. The final full-suite run above passed.
These adjustments do not change privacy detector behavior or legal judgments.

## Limits and next step
No browser journey, POSIX/hosted containment/performance check, live provider call,
Neon migration, commit, push or deployment ran. Local tests do not establish hosted
resource adequacy, production data protection or legal quality. Process creation,
host scheduling and database finalization are not hard real-time guarantees.
Killing the client does not cancel/refund remote provider computation.

Next: T032 citation extraction with Eyecite, retaining exact occurrences/spans,
then real source-adapter integration. Source/citation demo replay, real semantic
payload masking and hosted intake/security remain separate gates in [[TODO]].

## Related
[[docs/sessions/Index]], [[TODO]], [[README]], [[docs/architecture/stack]],
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]],
[[apps/api/src/filingguard/modules/analyses/README]],
[[apps/api/src/filingguard/integrations/providers/README]],
[[apps/api/src/filingguard/modules/privacy/README]],
[[apps/api/src/filingguard/integrations/courtlistener/README]],
[[apps/api/src/filingguard/integrations/llm/README]].
