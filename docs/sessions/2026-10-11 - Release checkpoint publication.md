---
type: session
status: published-hosted-rollout-pending
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

GitHub publication succeeded for checkpoint `0b6d9c2` on the release branch.
Fresh committed checkout installs both locked dependency sets, but cached-demo
controls exposed a missing ignored pytest temporary parent (15 passes/12 setup
errors). GitHub CI run `38147262802` fails at API tests. Correct the bootstrap
and reverify before deploying; [[docs/issues/BUG-023 - Clean checkout lacks pytest temporary parent]].
Bootstrap correction `10b1a6d` is pushed. A fresh committed checkout initially
without the API runtime parent passes all 27 cached-demo controls. Linux GitHub
run `38147439448` reaches 712 passes and two quote-stage deadline failures, without
setup errors. The exact two failures reproduce in an isolated Linux container.
[[docs/issues/BUG-023 - Clean checkout lacks pytest temporary parent]] is resolved.

[[docs/issues/BUG-024 - Linux stage pipe stalls on large snapshots]] identifies
partly written POSIX stdin abandoned after the first short communication timeout.
One-call delivery preserves the independent shutdown/deadline watcher and resource
limits. A delayed-start/100,000-character regression fails on the old Linux code;
the affected 21-control suite passes on both Windows and Linux after correction.
Ruff passes. Correction `325451ada388dc908b7a28c9d2b8dd8362a52338` is pushed and
GitHub Checks [run 38148960096](https://github.com/DevWithFaraz/filingguard-ai/actions/runs/38148960096)
passes: 715 API controls, 30 frontend unit controls, 28 baseline browser controls,
eight navigation/intake/results/accessibility controls, and three performance
controls/one deliberate mobile maximum-input skip. Locked setup, both linters,
typecheck, contract regeneration/no-diff and production build all pass. Existing
large-chunk and deprecation warnings remain. The clean Linux checkout reproduces
the documented app; [[TODO]] T059 is complete. No genuine provider calls occur in CI.

Final follow-up changes only documentation; the verified application revision is
`325451a`. The temporary diagnostic Linux container was stopped and removed.
Unrelated local graph/showreel work remains uncommitted and preserved.

Read-only Neon TLS connectivity passes; the database has no recorded Alembic head,
while the release head is `0004_citation_extraction`. The hosted probe still finds
/ready and /capabilities 404. No hosted migration or dashboard setting has changed.

## Hosting access and next step

The in-app Render browser reaches sign-in. User requested the signed-in Chrome
session; the control tool reports Chrome unavailable, so that session cannot be
operated here. User can follow [[docs/delivery/Deployment guide]] in Chrome after
publication. Reuse existing services and select `codex/release-checkpoint`;
keep intake/providers off during the first deployment. Working-app acceptance,
deliberate Neon migration, Linux containment, owner isolation, expiry/restart and
live/cached rehearsal remain T057/T058 gates. This note does not claim deployment.
Next action: user applies the closed-intake Render API/static settings in Chrome,
then run the public hosted probe against the deployed revision. Deliberate Neon
migration and enabled synthetic workflow acceptance follow before calling T057 done.
Physical assistive-device and expert legal-quality acceptance were not run here.

[[TODO]] T057/T059/T062, [[docs/sessions/Index]],
[[docs/sessions/2026-10-11 - Setup and release documentation]],
[[docs/issues/BUG-021 - API deployment root excludes demo resources]].
