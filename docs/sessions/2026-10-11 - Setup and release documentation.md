---
type: session
status: verified-local-release-preparation
date: 2026-10-11
tags: [sessions, delivery, setup]
---
# Setup and release documentation

## Scope and changes

User authorized starting T059 locally, with solo work and existing UI scope.
[[README]] now distinguishes default shell, disposable cached-source review,
explicit free-credit model review and hosted acceptance. Corrected obsolete model
throttling/adapter claims, added configuration bounds, fixed implementation limits
and troubleshooting. Removed unused planning switches from the API example;
actual secret environment files were not changed.

[[docs/delivery/Deployment guide]] now targets existing services with concrete
dashboard settings and a local-to-Neon migration sequence. Official Render free
and deployment docs were consulted October 11: free web services lack shell/SSH
and paid pre-deploy commands cannot be assumed. No migration is added to builds
or startup. Working-release migration, private Linux root, owner isolation,
expiry/restart and provider outage acceptance remain hosted gates.
The manifest's API root formerly excluded repository-root demo resources under
Render's documented monorepo contract. Corrected it to the repository root with
explicit API build/start paths; hosted verification remains pending. Evidence:
[[docs/issues/BUG-021 - API deployment root excludes demo resources]].

[[docs/delivery/Third-party notices]] links browser notices (32 dependency-closure
packages, 30 supplied license files plus two GSAP license URLs) and API notices
(52 installed dependencies including development/probe tools, supplied license
files present for each). Export helpers retain supplied text and upstream metadata.
These are inventory evidence, not independent legal clearance of all binary
dependencies or supplied imagery/fonts. Existing user-reported font permission
is preserved without requesting authorization again. No app license was chosen.

Corrected two homepage sentences identifying illustrative quote comparison and
human review; visual layout, assets, material and motion remain intact. Module:
[[apps/web/src/features/home/README]]. Updated stale delivery/infrastructure/demo
summaries to reflect existing implementation without claiming hosted acceptance.

## Checks and limits

Fresh isolated copy `.runtime/t059/reproduction` excludes actual env files, installed
dependencies and generated caches. Locked npm install and fresh uv virtual
environment install pass. npm reports zero vulnerabilities. Production build and
TypeScript pass, retaining existing bundle-size warnings. Existing isolated
desktop/mobile keyboard/axe synthetic private-state journeys pass 2/2 against
fresh preview processes on 8002/5175. A Windows connection-reset callback warning
was emitted; both journeys passed and it is not treated as a new reproducible bug.

`setup-receipt.json` verifies example settings, disabled default providers, identical
lockfile/notice hashes, no copied actual env files, notices included unchanged in
the build, and parsed free/single-worker Render manifest with no automatic migration.
Notice exporters execute locally; Python exporter passes Ruff. Receipt and browser
outputs remain ignored under `.runtime/t059`. No live provider call or Neon write
was made. The full backend regression and live curated model run were not repeated
for documentation/copy changes; their separate prior evidence remains in
[[docs/sessions/2026-10-11 - Accessibility performance and release gates]].
Frontend lint and all 30 existing unit tests pass. Vault validation finds no missing
wikilinks; `git diff --check` reports no whitespace errors (existing CRLF notices).
The revised production `uv sync --directory apps/api --locked --no-dev` command
passes in the disposable copy. That production-only environment loads the exact
cached fixture from the repository root and rejects a missing fixture safely.
Existing demo preview/source controls pass 27/27 in the normal locked test
environment. These Windows checks do not claim a Render Linux deploy was tested.

## Remaining work

[[TODO]] T059 remains unchecked: this verifies current local sources, not a committed
release reproduced by another developer. The no-commit/push constraint still applies.
T057 needs publication and dashboard access plus deliberate hosted migration and
working-app acceptance. T058 then rehearses the deployed walkthrough and failure
modes. User can follow the prepared dashboard sequence when rollout is authorized.

[[docs/sessions/Index]], [[docs/delivery/README]], [[infra/README]].
