---
type: session
status: completed
date: 2026-10-01
tags: [sessions, analysis, privacy, court-rules]
---
# Local review pipeline

Related: [[TODO]], [[apps/api/src/filingguard/modules/analyses/README]],
[[apps/api/src/filingguard/modules/privacy/README]],
[[apps/api/src/filingguard/modules/court_rules/README]],
[[apps/web/src/features/intake/README]],
[[docs/sessions/2026-09-30 - Review job foundation]].

## Changes
The existing queue-before-202 single worker now registers local privacy and
synthetic-demo disclosure runners. Other legal stages return unavailable rather
than silently passing. Per-stage transactions preserve findings across failures;
independent later stages continue. Structured logs use the analysis UUID, stage,
status, duration and error class, not filing text or exception messages. Owner-
scoped `/findings` projects masked snippets, while exact raw source evidence stays
private in the database. `/rerun` creates a new prepared live analysis ID.

The curated demo's private run revalidates the server-owned filing hash and runs
the same local checks. Its synthetic court rule is not a real-court statement;
reviewed preview expectations are not converted into execution findings. The
browser polls status each second while active, backs off on errors, stops at a
terminal state and forwards abort on unmount. The prepared screen shows stage
coverage, masked findings and a new-attempt action.

## Verification
- Full API suite: 270 passed, two host-dependent skips; Ruff passed.
- Frontend: 20 Vitest tests, TypeScript, ESLint and production build passed.
- Disposable SQLite + installed Chrome desktop/mobile intake E2E passed,
  including an actual local review and masked result display.
- OpenAPI export and TypeScript generation passed. The initial bundled Chromium
  attempt could not launch because its binary is absent; installed Chrome passed.
- Provider calls, PostgreSQL migration, hosted deployment, full source/citation
  replay, Linux behavior and real-device performance were not run.

## Remaining
T024 needs provider concurrency/retry/429 limits and a deadline that can actually
terminate affected work; an in-process Python thread alone cannot provide that.
T022/T031 need outbound payload tests once semantic adapters exist. T016 source
replay and T018 report/graph ownership remain separate. No public intake was
enabled and no credentials, production database or hosted services were changed.
Next: T024 with T022/T031 masking at the outbound boundary, then T032 citation
extraction. Current task status is only in [[TODO]].
