---
type: session
status: verified-foundations
date: 2026-09-27
tags: [contracts, persistence, privacy, design]
---
# Contracts persistence and UI planning

Related: [[TODO]], [[docs/decisions/ADR-004 - Truthful contracts and scoped evidence]],
[[docs/product/UI direction]], [[docs/feedback/FB-003 - Image-backed filing composer]].

## Changes
User explicitly expanded scope to Phase 2/3 and authorized bounded subagents.
One agent reviewed contracts, one implemented persistence, one implemented private
storage. Parent reviewed/integrated and corrected schema invariant gaps.

- T009: typed execution/verdict/status/severity, coverage, confidence and location
  contracts; no favorable defaults, reconciled counts, explicit inapplicability.
- T010: nine analysis-owned entities, composite FKs/indexes, lazy SQLAlchemy sessions
  and initial Alembic migration; no startup migrations or database dependency for health.
- T011: immutable source snapshots/hash/spans and method/source/model/profile
  lineage, validated before write and on owner-scoped finding retrieval.
- T012: future v1 request/response schemas, generated OpenAPI/TypeScript components,
  strict inputs, scoped response references and sanitized HTTP errors/request IDs.
  Only health is an enabled runtime operation; no fake submission handlers.
- T013: owner/expiry-scoped reads/writes, stage transactions and DB cascades.
  File attachment/deletion integration is not finished.
- T016: demo admission rejects live mode, unknown/altered inputs and unreviewed
  manifest/hash material. Starter fixtures remain unchanged and disabled.
- T017: private UUID PDF storage, strict signature/parser limits, deletion/retention
  and filesystem checks. HTTP streaming/lifecycle cleanup/public integration pending.

User approved the filing-focused composer and will supply the HD background/font
and possibly logo. Design plan covers pages, controls, palette, responsive layouts,
purposeful GSAP motion and reduced motion. Official GSAP guidance skills installed
outside the repo with approval; no animation runtime dependency or final UI code
was added. No purchases or paid compute changes were performed. User removed the
internal deadline constraint; the recorded event deadline remains unchanged.

## Verification
- `npm run test:api`: 180 passed, 2 skipped (Windows native symlink/POSIX permission
  checks), existing Starlette/httpx deprecation warning.
- `npm run lint:api`, frontend lint and typecheck pass.
- Frontend unit tests: 4 pass; production build passes.
- Desktop/mobile Playwright smoke tests: 4 pass after error-boundary integration.
- OpenAPI export and browser type generation pass; diff whitespace checks pass.
- Approved Neon probe: migration, nine-entity round trip, validated finding evidence
  and cascades pass in a freshly generated disposable schema; schema removed.
  No existing/public tables were migrated. Probe never prints credentials.

No Groq/CourtListener requests, legal accuracy evaluation, full demo fixture curation,
human review of expectations, public session transport, rate-limiter/admission tests,
hosted new-code deployment or final-design screenshots were performed. PDF limits
are not hard process-memory/CPU isolation. Future public intake also needs privacy-safe
third-party parser logging. The previously exposed credential still needs rotation
before private data use; no credential is recorded here.

## Handoff
T009-T012 complete as contracts/persistence/provenance foundations. T013 and
T016-T018 retain pending integration criteria in TODO. Next independent task is
T014 curated demo material, then T015 explicit human-reviewed expected spans.
Anonymous tab-private sessions are proposed; user decision requested, not yet implemented.
No commit, push or deployment occurred in this session. Existing user graph settings
and ignored credentials were not changed. Final UI stays a plan pending assets.
