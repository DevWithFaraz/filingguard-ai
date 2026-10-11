---
type: session
status: publication-in-progress
date: 2026-10-11
tags: [sessions, release, deployment]
---
# Release checkpoint publication

## Authorization and scope

User lifted the no-commit/push restriction and authorized help reviewing/publishing
the checkpoint and verifying the hosted workflow. Work remains solo, free-credit
only and synthetic/public material only. Existing homepage and workflow UI scope
is preserved. No paid resource or confidential-data release is included.

Review/publish the current implementation on `codex/release-checkpoint`, based on
the synchronized `main`/`origin/main` checkpoint `2879aba`. Preserve local unrelated
`videos/` showreel work and `.obsidian/graph.json` without including their changes.
The project/vault, synthetic public fixtures, browser assets and Remotion authoring
source belong to the release; private env, runtime artifacts and dependencies do not.

## Review and verification

Bounded candidate audit inspects 441 files/approximately 36 MB: no known secret
prefix/private-file findings and no files over 25 MiB. This is not an exhaustive
security certification. API Ruff and the full suite pass: 712 passed, two Windows
platform/permission skips, seven existing deprecation warnings. Contract generation,
frontend lint and production build/typecheck pass. Existing large-chunk warnings
remain. Baseline desktop/mobile browser checks pass 28/28.

CI formerly combined private browser suites on shared session-rate buckets despite
an observed 429 recorded in [[tests/e2e/README]]. It now runs private workflow
suites independently on fresh disposable servers. Production limits are unchanged;
the usual user preview is preserved. Genuine model calls remain outside CI.

All five isolated workflow suites pass: public/intake/results/accessibility 2/2
each, performance 3 passed/one deliberate mobile maximum-input skip. No provider
calls or production rate-limit relaxation. Windows pipe reset warnings remain.

Staging exposed line-ending normalization of hash-locked fixture JSON. Extended
existing Git attributes to preserve exact fixture and supplied license bytes, then
restaged them deliberately. All 14 fixture files now equal the working bytes;
[[docs/issues/BUG-022 - Git normalization changes locked fixture bytes]] records it.
Staged whitespace checks pass, with source snapshots/license texts intentionally
exempt from normalization. Final audit: 442 files/approximately 36 MB, no findings.

GitHub fetch and dry-run push authenticate successfully. Publication and clean
committed-checkpoint reproduction receipts will be added after those actions.
No hosted migration or dashboard setting has been changed.

## Hosting access and next step

The in-app Render browser reaches sign-in. User requested the signed-in Chrome
session; the control tool reports Chrome unavailable, so that session cannot be
operated here. User can follow [[docs/delivery/Deployment guide]] in Chrome after
publication. Reuse existing services and select the published release branch;
keep intake/providers off during the first deployment. Working-app acceptance,
deliberate Neon migration, Linux containment, owner isolation, expiry/restart and
live/cached rehearsal remain T057/T058 gates. This note does not claim deployment.

[[TODO]] T057/T059/T062, [[docs/sessions/Index]],
[[docs/sessions/2026-10-11 - Setup and release documentation]],
[[docs/issues/BUG-021 - API deployment root excludes demo resources]].
