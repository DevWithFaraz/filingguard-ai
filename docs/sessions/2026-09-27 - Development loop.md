---
type: session
status: handoff
date: 2026-09-27
tags: [development, phase-1]
---
# Development loop

Scope: P0 phase 1, tasks T001-T008 in [[TODO]], one task at a time.

Official event facts are in [[docs/delivery/LexHack requirements]]. The user
confirmed solo participation, student status, age 22 and free credits only.
T001-T003 are complete. Groq is selected; its model is not selected.

The checklist was renamed by the user to TODO.md; references were repaired rather
than creating a duplicate checklist. Existing Git history is present; the user's
Obsidian graph settings change is left intact.

## Changes and checks
Installed npm and Python dependencies, generated both lockfiles, created ignored
local environment files without overwriting existing files, and exported OpenAPI
and matching browser types. Added a local-cache uv launcher and Groq environment
placeholders. Recorded [[docs/decisions/ADR-003 - Free-tier Groq evaluation]].

Passed: locked offline uv sync, offline npm ci with lifecycle scripts disabled,
esbuild transform, root backend lint, one pytest health test, root TypeScript
check, OpenAPI export and browser generation. A running API returned 200 for
health and docs; the check server was stopped afterward. The pytest suite has
one Starlette/httpx deprecation warning, not a failure.

Not run: provider requests, model benchmarks, database migration, frontend build,
browser UI tests, CI or hosted checks. These are not yet implemented/verified.

## Next task and blockers
T004 needs a CourtListener token. T005 needs a Groq key, actual account quotas
and bounded model comparisons. No credentials were printed or stored in notes.
User must enter keys in ignored apps/api/.env; no paid billing is authorized.
See [[docs/issues/BUG-001 - Global uv cache blocks API commands]] for the resolved
setup issue. Frontend shell remains T006; hosted provider access remains T008.

Related: [[docs/sessions/Index]], [[docs/decisions/ADR-001 - Stack and MVP execution]].
