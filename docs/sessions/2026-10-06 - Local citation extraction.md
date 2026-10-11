---
type: session
status: completed
date: 2026-10-06
tags: [sessions, citations, persistence]
---
# Local citation extraction

## Task and scope
User authorized the next task after the project inspection: T032 only. Local
extraction/pipeline/private-read integration, not live CourtListener, semantic
analysis, redesign, public intake, commit/push or deployment. A Sol/medium subagent
implemented parser schemas/service and focused tests; the parent reviewed and
integrated worker/persistence/API boundaries and the split-format fallback.

## Changes
Eyecite 2.7.8 extracts original Unicode spans, preserving repetitions and parser
ambiguity. Unresolved references and unsupported formats remain explicit; a narrow
numeric reporter fallback retains additional split-line/page candidates without
source verdicts. Up to 200 ordered occurrences are retained; total detections and
truncation are explicit. The curated filing yields five full-case occurrences.
The invented citation is detected but remains unverified.

Migration 0004 adds Citation.extraction_metadata JSON/JSONB with empty legacy
default. The contained citation worker receives snapshot-matched paragraph IDs/
locations; parent and worker validate raw slices, anchors and cross-boundary
warnings. Only unverified Citation rows can pass the dedicated partial-output
path. Source coverage stays unavailable/evaluated zero. Zero detections skips with
a limited-format caveat, not a clean-filing claim.

The private `/analyses/{id}/citations` read returns bounded ordered occurrences,
original locations and distinct parser/verification status. Whole-snapshot masking
protects clipped identifiers; affected normalization is omitted. Ownership,
expiry, no-store, rerun freshness and cascading deletion are preserved. Reads do
not mix pre-commit running stage state with newly committed rows. Shared OpenAPI
and browser declarations were regenerated. Canonical module/stack notes and
ADR-009 record the decisions. No application UI was redesigned in this task.

## Verification
- Initial existing pipeline/persistence/parser check: 84 passed.
- Expanded parser/citation pipeline/persistence check: 98 passed.
- Post-format contracts/parser check: 55 passed.
- API Ruff passed; OpenAPI export/browser declarations generated successfully.
- Frontend TypeScript, ESLint, 20 Vitest tests and production build passed.
- Sandbox Vitest/build startup initially failed because esbuild could not read a
  parent directory. Approved outside-sandbox reruns passed. Build still reports
  the existing large lazy-loaded Three.js chunk warning.
- Initial full API run: 471 passed, two existing host skips, one route-list
  expectation failure. Added the new citations route and max-items assertion;
  corrected full-suite rerun passed: **472 passed, two existing Windows host
  skips, seven deprecation warnings**, 197.59 seconds. Skips are symlink creation
  and POSIX storage permissions, not missing citation/deadline tests.
- Scoped tracked-file whitespace check passed; Git reports only line-ending
  normalization for generated OpenAPI.

Not run: live provider/LLM requests, Neon/production migration, hosted/POSIX parser
containment, end-to-end browser visual testing or real filing evaluation. No keys
or raw provider payloads were printed. No credit spending, commit or deployment.

## Blockers and next step
T032 is verified locally and closed in [[TODO]]. Next is
T033: bounded CourtListener adapter with normalized identity and distinct verified/
not-found/invalid/ambiguous/unavailable outcomes. No additional user action or
provider key is needed for local extraction. Source/opinion retrieval, lookup
deduplication, semantic masking and hosted release checks remain pending.

## Related
[[apps/api/src/filingguard/modules/citations/README]],
[[apps/api/src/filingguard/modules/analyses/README]],
[[apps/api/src/filingguard/db/models/README]], [[contracts/README]],
[[docs/architecture/stack]],
[[docs/decisions/ADR-009 - Local citation occurrences before source verification]],
[[docs/decisions/ADR-004 - Truthful contracts and scoped evidence]],
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]].

[[docs/sessions/Index]] | [[TODO]]
