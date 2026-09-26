---
type: learning
status: validated
date: 2026-09-26
tags: [verification, scaffolding]
---
# LEARN-001 - Scaffold is not runtime verification

## Observation
The initial scaffold's JSON/TOML parsing, Python syntax checks and task/fixture
references passed. Dependencies were not installed, so framework tests, provider
calls, frontend compilation and migrations were not verified. Evidence is recorded
in the [[TDOD#Work log|task work log]] and [[README|setup status]].

## Reusable practice
Report exactly which layer was checked. A module folder is not a working feature;
a syntax check is not an integration test. Keep runtime acceptance tasks open until
their commands and behavioral checks actually pass.

## Applicability and limits
Useful for starter repositories and code generation. This observation does not
show that the selected dependencies will fail or succeed, or that any provider is
available. Tasks T002-T003 establish the next verification level.

Related: [[docs/learnings/Index]], [[docs/decisions/ADR-001 - Stack and MVP execution]],
[[docs/sessions/2026-09-26 - Documentation vault setup]].
