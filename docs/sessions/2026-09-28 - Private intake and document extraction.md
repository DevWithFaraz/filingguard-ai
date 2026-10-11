---
type: session
status: completed
date: 2026-09-28
tags: [sessions, intake, security, extraction, design]
---
# Private intake and document extraction

## Task and scope
The user expanded work to remaining P0 Phase 3/4, then requested a distinctive
interactive redesign brief. Task status remains exclusively in [[TODO]].
T017/T019-T021 are verified at local development scope. T016 actual engine replay,
T018 full legal-job/report/graph integration and T022 provider-bound masking
integration remain pending; these phases are not claimed wholly complete.

## Changes
Implemented expiring server-issued anonymous bearer sessions with persisted token
hashes, owner-scoped preparation/history/retrieval/deletion, pre-body admission,
bounded streaming input and exact-origin rules. Public intake remains off by default.
Text/PDF/server-owned Demo submissions now extract and persist canonical snapshots,
hashes and Unicode code-point spans, without inventing legal findings or scores.
PDF parsing runs in a time/output/resource-bounded child process; malformed,
encrypted or no-text documents receive paste-text fallback. No OCR is performed.

Added local identifier masking before excerpt clipping, with preserved offsets and
explicit coverage limits. No provider is called by preparation. Added frontend
composer, private prepared view and metadata-only Activity with expiry/deletion.
Regenerated OpenAPI and TypeScript contracts; documented migration 0003 and runtime
boundaries. See [[docs/decisions/ADR-007 - Private preparation boundary]].

Added [[design]] for visual hierarchy, signature evidence choreography, useful
micro-interactions and responsive/accessibility/performance gates. GSAP/CSS are
the proposed primary stack; a meaningful Three.js scene is optional and must earn
its cost. This redesign is planned, not implemented. The supplied image/font and
the user's forthcoming widget/grid-motion ideas remain governed by
[[docs/product/UI direction]] and
[[docs/feedback/FB-005 - Distinctive interactive redesign]].

## Verification
- `npm run test:api`: 261 passed, two host-dependent skips, four warnings.
  Windows symlink creation lacks host permission; POSIX chmod check skips on Windows.
- `npm run test:web`: 17 passed across three files.
- `npm run test:e2e`: 10 passed in real Chrome desktop/mobile, against a disposable
  SQLite API. Covered Text/PDF/Demo, owner isolation, reload, metadata-only Activity,
  deletion and parser fallback, plus the default disabled shell.
- Backend/frontend lint, TypeScript check, contract export/generation, production
  build and `git diff --check` passed. Diff check reports only CRLF normalization.
- Inspected desktop PDF and mobile text screenshots: readable, no observed overlap
  or horizontal overflow in sampled views. This is not final-redesign acceptance.
- Windows child-process normal/timeout and malformed/encrypted/no-text tests pass.
  Fresh/populated SQLite migration checks and offline PostgreSQL schema checks pass.

Not run: new migrations against Neon, Linux resource/locking/ACL checks, hosted
intake threat tests, actual provider masking, legal engines/replay, final redesign
or new hosted deployment. No provider spending, commit or push performed.

## Local preview and next step
Started hidden localhost preview processes: API launcher PID 20744, Vite PID 10136.
`http://127.0.0.1:5174` returned 200; API capabilities on port 8001 confirm intake
enabled and legal analysis disabled. Setup commands are in [[README]].
Use public/synthetic material only. The helper migrates its own temporary SQLite
database, never the configured Neon database. Normal shutdown removes temporary
data; hard termination may leave OS-temp artifacts and is not secure erasure.

Next task is T023 pipeline orchestration, extending admission through actual legal
jobs before report/graph/provider integration. Migration/security release gates
and T212/T213 still precede confidential client use. Changes remain local.

## Related
[[docs/sessions/Index]], [[TODO]], [[Home]], [[contracts/README]],
[[apps/api/src/filingguard/modules/documents/README]],
[[apps/api/src/filingguard/modules/analyses/README]],
[[apps/api/src/filingguard/modules/privacy/README]],
[[apps/api/src/filingguard/db/models/README]],
[[apps/web/src/features/intake/README]],
[[docs/issues/BUG-005 - Windows venv worker process limit]],
[[docs/delivery/Deployment guide]], [[design]].
