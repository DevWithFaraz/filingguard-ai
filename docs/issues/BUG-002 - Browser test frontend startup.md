---
type: issue
status: resolved
date: 2026-09-27
tags: [issues, testing]
---
# Browser test frontend startup

Observed: Playwright's frontend startup timed out. npm warned that --host was
being parsed as its own configuration and 127.0.0.1 as a positional argument.
Expected: Vite starts at the configured localhost origin.

Cause: arguments were forwarded through nested root/workspace npm scripts without
the extra delimiter needed at the inner boundary. Fix: remove redundant --host;
vite.config.ts already sets 127.0.0.1. Allow 120 seconds for a cold test startup.
Regression evidence: all four desktop/mobile browser checks passed on the rerun.
This is a test-harness issue, not a product analysis defect.

Related: [[TODO]] (T006-T007), [[tests/e2e/README]], [[docs/issues/Index]],
[[docs/sessions/2026-09-27 - Frontend shell and CI]].
