---
type: session
status: verified
date: 2026-10-17
tags: [sessions, lineage, explanations, phase-b, verification]
---
# Rich lineage and explanations implementation

## Task and scope
User authorized executing [[TODO]] `T102` (Rich lineage and explanations: `FR-205`, `FR-224/225`).
The requirements specify:
1. Expandable determination explanation ("How was this determined?") for every finding explaining the forensic method, AI-assisted vs deterministic classification, and explicit uncertainty boundaries (`FR-205`).
2. Responsive 5-hop Visual Lineage Chain (`01 Document Span` -> `02 Extraction Target` -> `03 Source Authority` -> `04 Verification Method & Provenance` -> `05 Finding Verdict`) displayed when a finding is inspected, linking back to the same persisted evidence used for the finding (`FR-224`).
3. Structured 5-hop lineage chain and determination methodology included in exported Markdown and HTML reports (`FR-225`).

## Changes
- **Backend report exports (`apps/api/src/filingguard/modules/reports/`):**
  - Updated `service.py` (`render_report`) to generate determination methodology and 5-hop evidence lineage sections in both Markdown and HTML exports.
  - Formatted character offsets with ASCII hyphens (`offsets {start}-{end} (Unicode code points)`) to maintain strict Windows/CP1252 character encoding stability.
  - Updated module documentation `apps/api/src/filingguard/modules/reports/README.md` to document the P1 lineage and determination export enhancements.
  - Authored unit test `test_report_includes_evidence_lineage_and_determination` in `apps/api/tests/unit/test_review_reports.py`.
- **API contracts & routes alignment:**
  - Added `/api/v1/analyses/{analysis_id}/red-team` route assertion in `apps/api/tests/unit/test_contracts.py` ensuring all 38 documented endpoints pass parity checks.
- **Frontend determination details & lineage chain (`apps/web/src/features/analyses/`):**
  - Updated `ResultsView.tsx` with `getDeterminationDetails` providing explicit forensic methodology, model/rule classification badges, and uncertainty disclosures for quote fidelity, citation verification, rule compliance, and privacy hygiene findings (`FR-205`).
  - Authored `FindingLineageChain` rendering a 5-hop sequential trail:
    - `01 Document Span`: filing location, character offsets, and verbatim extracted span.
    - `02 Extraction Target`: extracted quote, citation string, or privacy identifier.
    - `03 Source Authority`: CourtListener slip opinion or local rule registry link with SHA-256 integrity hash.
    - `04 Verification Method & Provenance`: forensic method identifier, model/tool version, and date.
    - `05 Finding Verdict`: severity badge, verdict title, and forensic description.
  - Extended `results.css` with responsive, accessible glass styling, high-contrast step badges, connector lines, and `@media (prefers-reduced-motion: reduce)` compliance.
  - Authored comprehensive frontend tests in `results.test.tsx` testing determination details toggle, methodology presentation, all 5 lineage hops, and async authority retrieval.

## Verification
- `uv --directory apps/api run --locked pytest tests/unit/test_review_reports.py tests/integration/test_review_results.py tests/unit/test_red_team.py tests/integration/test_red_team_pipeline.py tests/unit/test_contracts.py` — 64 passed.
- `uv --directory apps/api run --locked ruff check .` — passed (0 errors).
- `npm run test:web` — passed (41 passed across 6 test files).
- `npm run lint:web` — passed (ESLint exited 0).
- `npm run typecheck` — passed (`tsc --noEmit` exited 0).
- `npm run build` — passed (Vite production bundle built cleanly).

## Blockers and next step
No blockers. T102 is verified and marked complete in [[TODO]].
Next task in [[TODO]] under Phase B:
- `T103` - Finding-grounded Q&A (`FR-260` through `FR-264`): scoped evidence access, cited answers, refusal of broad legal advice, missing-evidence behavior and request limits.

## Related
[[TODO]] `T101`, `T102`, `T103`, `T212`, `T213`;
[[FilingGuard_AI_SRS]];
[[docs/product/FilingGuard product direction]];
[[apps/api/src/filingguard/modules/reports/README]];
[[apps/web/src/features/analyses/ResultsView]].

[[docs/sessions/Index]] | [[TODO]]
