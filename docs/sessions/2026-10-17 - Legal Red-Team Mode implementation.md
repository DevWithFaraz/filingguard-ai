---
type: session
status: verified
date: 2026-10-17
tags: [sessions, red-team, phase-b, verification]
---
# Legal Red-Team Mode implementation

## Task and scope
User authorized starting Phase B and executing [[TODO]] `T101` (Legal Red-Team Mode: `FR-240` through `FR-245`).
The requirements specify:
1. Rank filing weaknesses solely from existing persisted findings and evidence without inventing new facts or drafting legal arguments/strategy (`FR-242`, `FR-244`).
2. Explain adversarial attack theories from the perspective of opposing counsel or a skeptical court (`FR-241`, `FR-243`).
3. Link every weakness back to underlying findings, citations, claims, and quotes (`FR-245`).
4. Provide a dedicated "Red Team Filing" action after analysis in the UI and via API routes `POST /api/v1/analyses/{analysis_id}/red-team` and `GET /api/v1/analyses/{analysis_id}/red-team` (`FR-240`).

## Changes
- **Backend schemas & service (`apps/api/src/filingguard/modules/red_team/`):**
  - Authored `schemas.py` with `RedTeamWeakness` and `RedTeamResponse` strictly adhering to `Contract`.
  - Authored deterministic synthesis engine `service.py` (`synthesize_weaknesses`, `synthesize_red_team`). Maps existing findings to adversarial challenge theories, impact summaries, and recommended pre-filing review actions. Uses UUID5 derivation (`uuid5(_NAMESPACE_REDTEAM, ...)`) for deterministic weakness IDs across re-runs.
  - Authored module documentation `apps/api/src/filingguard/modules/red_team/README.md`.
- **API contracts & routes (`apps/api/src/filingguard/api/`):**
  - Added `RedTeamResponse` to `contracts.py`.
  - Added `GET /api/v1/analyses/{analysis_id}/red-team` and `POST /api/v1/analyses/{analysis_id}/red-team` in `routes/intake.py` with session ownership and terminal-state checks (HTTP 409 if analysis is still queued or running).
  - Exported OpenAPI v1 via `npm run contracts:export` and generated TypeScript schema definitions via `npm run contracts:generate`.
- **Frontend client & UI (`apps/web/`):**
  - Extended `apps/web/src/lib/api/results.ts` with `RedTeamWeakness`, `RedTeamResponse`, `validateRedTeamResponse`, `getRedTeam`, and `runRedTeam`.
  - Authored `apps/web/src/features/red-team/RedTeamPanel.tsx` and `red-team.css` adhering to the established purple/lilac/yellow glass identity, responsive layouts, screen-reader semantics, and reduced-motion compliance.
  - Integrated `RedTeamPanel` into `apps/web/src/features/analyses/ResultsView.tsx` with jump navigation (`#result-red-team`) and bidirectional finding selection.
- **Verification & test coverage:**
  - `apps/api/tests/unit/test_red_team.py` (6 unit tests).
  - `apps/api/tests/integration/test_red_team_pipeline.py` (2 integration tests).
  - `apps/web/src/features/red-team/redTeam.test.tsx` (9 unit and boundary validation tests).
  - `apps/web/src/features/analyses/results.test.tsx` (updated with Red-Team jump and finding selection integration test).

## Verification
- `uv --directory apps/api run --locked pytest tests/unit/test_red_team.py tests/integration/test_red_team_pipeline.py` — 8 passed.
- `uv --directory apps/api run --locked ruff check .` — passed (0 errors).
- `npm run typecheck` — passed (`tsc --noEmit` exited 0).
- `npm run test:web` — passed (40 passed across 6 test files).
- `npm run lint:web` — passed (ESLint exited 0).
- `npm run build` — passed (Vite production bundle built in 13.64s).

## Blockers and next step
No blockers. T101 is verified and checked off in [[TODO]].
Next task in [[TODO]] under Phase B:
- `T102` - Rich lineage and explanations (`FR-205`, `FR-224/225`): expandable document-to-source-to-method chain and exported provenance.

## Related
[[TODO]] `T101`, `T102`, `T212`, `T213`;
[[FilingGuard_AI_SRS]];
[[docs/product/FilingGuard product direction]];
[[apps/api/src/filingguard/modules/red_team/README]].

[[docs/sessions/Index]] | [[TODO]]
