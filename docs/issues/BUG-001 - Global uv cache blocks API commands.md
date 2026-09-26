---
type: issue
status: resolved
date: 2026-09-27
tags: [issues, development]
---
# Global uv cache blocks API commands

## Observed behavior
`npm run lint:api` failed before Ruff started: uv could not initialize
`C:/Users/IT/AppData/Local/uv/cache` and reported Windows error 183.
Expected: root commands execute in the backend environment.

## Cause and resolution
The default cache location was unusable on this machine. Its underlying filesystem
cause was not investigated; no global files were changed or deleted.
`scripts/api.mjs` supplies an absolute ignored project-local UV_CACHE_DIR and
backend working directory. Run commands use the locked dependency graph.

## Regression evidence
Root lint, pytest, OpenAPI export and server commands now run successfully.
`node scripts/api.mjs sync --locked --offline` succeeds with installed dependencies.
This is an environment/setup issue, not a defect in legal analysis.

Related: [[TODO]] (T002-T003), [[scripts/README]], [[README]],
[[docs/sessions/2026-09-27 - Development loop]], [[docs/issues/Index]].
