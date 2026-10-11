---
type: session
date: 2026-09-28
tags: [product, demo, frontend, verification]
---
# Product continuation and reviewed demo

Related: [[docs/sessions/Index]], [[TODO]], [[FilingGuard_AI_SRS]],
[[docs/decisions/ADR-005 - Product continuation and reviewed demo]],
[[docs/product/Demo fixture review]], [[docs/product/UI direction]].

## Changes

User reports missing the hackathon deadline and now intends full product development
without a time concern. Updated active planning/SRS with a dated amendment while
preserving historical event evidence. Budget and initial anonymous/private scope
are unchanged. The retired submission task remains unchecked.

T016 read-only milestone: review.json binds seven artifacts to the prior delegated
AI review, retaining all five conditions. The multi-authority adapter checks byte
hashes, raw/text source fingerprints, fixture identity and exact evidence spans.
GET /api/v1/demos/curated-v1?mode=demo returns typed reviewed expectations with
execution_status=not_run; wrong/missing mode and unknown IDs fail, resource changes
return safe unavailability. No arbitrary input or private upload endpoint exists.
Legacy human-reviewed replay admission is unchanged.

Frontend shows the fixed sample, all 18 scenarios, selected source/filing evidence,
conditional judgments, source links/fingerprints, limits and reset. Network/contract
errors are explicit and retryable; no live failure substitutes demo results. User's
2172x724 PNG logo is copied unchanged and rendered responsively in the workspace.
Final homepage/background/font/motion implementation remains a separate task.

## Verification

- Backend: 202 tests pass, two Windows platform skips; one existing Starlette/httpx
  deprecation warning. Includes 18 new admission/transport/integrity tests.
- Frontend: 12 unit tests pass, including reset, Unicode-code-point evidence and
  malformed/falsely live responses; TypeScript and both linters pass.
- Production build passes. OpenAPI/client types regenerated from the actual route.
- Local preview servers started in hidden windows: frontend http://127.0.0.1:5173
  responds 200; API sample endpoint returns execution_status=not_run. Wrapper PIDs
  8300 (web) and 13996 (API); runtime logs stay under ignored .runtime.
- Playwright: eight checks pass in desktop Chrome and mobile Chromium, including
  actual API fixture loading, selected quote reversal evidence, provenance, reset,
  request failure/retry and rendered logo/nonoverflow checks. Screenshots inspected.
- Restricted esbuild ancestor-directory access required approved elevated test/build
  runs; this is local sandbox behavior, not a project dependency change.

## Boundaries and next task

No Groq/CourtListener calls, credentials printed, production schema migrations,
commit/push or hosted deployment this session. No new legal judgments or accuracy
claims; expected outcomes remain separate from executed results. T016 stays unchecked
until the actual analysis/live/demo execution adapters are integrated with the pipeline.
The public deployment still serves the previous checkpoint, not these local changes.

Next: T013 lifecycle cleanup integration, then complete T017/T018 storage/anonymous
session protection before enabling live intake. Domain-expert and production
data-protection gates must precede real confidential-client use. Standalone packaged
deployments need fixture resources; current root assumes monorepo editable install.
