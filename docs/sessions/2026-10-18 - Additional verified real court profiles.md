---
type: session
status: verified
date: 2026-10-18
tags: [sessions, court-rules, profiles, nd-texas, phase-b, verification]
---
# Additional verified real court profiles

## Task and scope
Completed **T106**: Additional verified real court profiles (FR-146) in FilingGuard AI.
Guided by [[docs/decisions/ADR-014 - Filing-centric court rules and separate Article 50 direction]],
[[docs/product/FilingGuard product direction]], and
[[docs/research/Court rules and EU AI Act product direction - 2026-10-14]].

Requirements implemented:
1. Created real court profile `apps/api/src/filingguard/modules/court_rules/profiles/us-txnd-lr7-2f-v1.json`:
   - U.S. District Court for the Northern District of Texas, Local Civil Rule 7.2(f) (Special Order 2-98, effective September 3, 2024).
   - District-wide rule (`judge_scope: null`), active for live filings (`is_demo: false`).
   - Placement constraint `placement: "first_page"` requiring standalone heading "Use of Generative Artificial Intelligence".
2. Updated `service.py`:
   - Added `placement: Literal["anywhere", "first_page"] = "anywhere"` to `DisclosureRule`.
   - Updated `load_profile` allowlist for `synthetic-demo-v1` and `us-txnd-lr7-2f-v1`.
   - Updated `evaluate_disclosure` with page-aware placement evaluation, mode mismatch protection, effective date verification, and clear human-review disclaimer reasons.
3. Refactored `runners.py#court_stage`:
   - Safely extracts page boundaries from `analysis.document_snapshot.get("pages")`.
   - Dynamically produces real rule finding `"Required N.D. Tex. Local Rule 7.2(f) AI-use disclosure missing"` with explicit human-review disclaimer.
4. Updated intake modules and routes:
   - Registered `us-txnd-lr7-2f-v1` in `PROFILES` with `applicability="verified"`, `is_demo=False`.
   - Added `verified` to `CourtProfileSummary` contract.
   - Allowed `us-txnd-lr7-2f-v1` in `prepare` and `submit_file`.
5. Updated Frontend:
   - Enabled Court profile dropdown in live mode as well as demo mode in `IntakeComposer.tsx`.
   - Mapped `us-txnd-lr7-2f-v1` to `"N.D. Tex. LR 7.2(f)"` in `PreparedView.tsx`.
6. Updated Documentation & Tests:
   - Documented real court profiles and placement evaluation in `court_rules/README.md`.
   - Added comprehensive tests in `test_court_rules.py`, `test_intake.py`, and `intakeComposer.test.tsx`.

## Verification
- `npm run lint:api` (`ruff check .`) — passed (0 errors).
- `npm run lint:web` (`eslint .`) — passed (0 errors).
- `npm run typecheck` (`tsc --noEmit`) — passed (0 errors).
- `npm run test:web` — 64 passed across 9 test files.
- `npm run test:api` (`pytest`) — 788 passed, 2 skipped (0 failures).

## Next step
T106 is verified and checked off in [[TODO]].
Phase B roadmap items completed: T106, T107, T108, T109, T110.
