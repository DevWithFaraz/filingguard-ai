---
type: session
status: verified
date: 2026-10-17
tags: [sessions, grounded-qa, phase-b, verification]
---
# Finding-grounded QA implementation

## Task and scope
User authorized starting the next task: [[TODO]] `T103` (Finding-grounded Q&A: `FR-260` through `FR-264`).
The requirements specify:
1. Scoped evidence access allowing users to ask forensic questions about a specific finding (`FR-260`, `FR-261`).
2. Answers shall be grounded strictly in the finding, source passages, and analysis metadata, citing authentic evidence records and source links (`FR-262`).
3. Explicit refusal of broad legal advice questions (e.g. "What should I argue?", "Should I file this?", "Will I win?"), redirecting safely to independent legal counsel (`FR-263`).
4. General document chat unrelated to findings excluded from scope (`FR-264`).
5. Missing-evidence behavior and transparent disclosures when sources are unavailable from public databases.
6. Rate and request limits preventing cross-session leakage, denial-of-service, or quota exhaustion.

## Changes
- **Backend module & schemas (`apps/api/src/filingguard/modules/grounded_qa/`):**
  - Authored `schemas.py` with `GroundedQuestionRequest`, `GroundedAnswerResponse`, and `GroundedQuestionHistory`.
  - Authored `service.py` (`ask_finding_question`, `get_finding_qa_history`, `classify_question_intent`):
    - Rigorous intent classification detecting queries requesting litigation strategy, odds of winning, or argument drafting (`FR-263`), and general chatbot prompts (`FR-264`).
    - Grounded answer generator citing exact `evidence_record_ids`, authentic case names, and CourtListener opinion URLs. Never invents unsupported authorities.
    - Transparent disclosures when no corroborating public records exist, explicitly cautioning that absence in a database does not prove fabrication.
    - Session isolation, terminal state check (409 Conflict if running), and rate limiting (`MAX_QUESTIONS_PER_ANALYSIS = 20`).
  - Authored module documentation in `apps/api/src/filingguard/modules/grounded_qa/README.md`.
- **API contracts & REST endpoints (`apps/api/src/filingguard/api/`):**
  - Added Grounded Q&A contracts to `CONTRACT_MODELS` in `contracts.py`.
  - Added REST endpoints `POST /api/v1/analyses/{analysis_id}/findings/{finding_id}/questions` and `GET /api/v1/analyses/{analysis_id}/findings/{finding_id}/questions` in `routes/intake.py`.
  - Updated OpenAPI specification (`npm run contracts:export`) and generated TypeScript schema bindings (`npm run contracts:generate`).
  - Updated `apps/api/tests/unit/test_contracts.py` with the new endpoint route.
- **Frontend client & UI component (`apps/web/`):**
  - Added `askFindingQuestion`, `getFindingQuestions`, and response validators to `apps/web/src/lib/api/results.ts`.
  - Authored `FindingQA.tsx` featuring quick prompt suggestion chips ("Why was this flagged?", "What evidence was used?", "What source passage supports this?"), character counter, live thread, status pills (`Grounded`, `Refused: Legal Advice`, `Missing Source`), cited evidence record pills, CourtListener links, and legal advice disclaimers.
  - Integrated `<FindingQA>` into `EvidenceDetail` in `apps/web/src/features/analyses/ResultsView.tsx`.
  - Styled in `apps/web/src/features/analyses/results.css` using the purple/lilac/yellow glass identity, high-contrast states, and reduced-motion compliance.
- **Verification & tests:**
  - `apps/api/tests/unit/test_grounded_qa.py` (9 unit tests).
  - `apps/api/tests/integration/test_grounded_qa_pipeline.py` (3 integration tests).
  - `apps/web/src/features/analyses/findingQA.test.tsx` (6 unit tests).

## Verification
- `uv --directory apps/api run --locked pytest tests/unit/test_grounded_qa.py tests/integration/test_grounded_qa_pipeline.py tests/unit/test_review_reports.py tests/integration/test_review_results.py tests/unit/test_red_team.py tests/integration/test_red_team_pipeline.py tests/unit/test_contracts.py` — 76 passed.
- `uv --directory apps/api run --locked ruff check .` — passed (0 errors).
- `npm run test:web` — passed (47 passed across 7 test files).
- `npm run lint:web` — passed (ESLint exited 0).
- `npm run typecheck` — passed (`tsc --noEmit` exited 0).
- `npm run build` — passed (Vite production bundle built cleanly).

## Blockers and next step
No blockers. T103 is verified and marked complete in [[TODO]].
Next task in [[TODO]] under Phase B:
- `T104` - PDF report export (`FR-305`): select renderer, embed readable evidence, pagination and disclaimers.

## Related
[[TODO]] `T101`, `T102`, `T103`, `T104`, `T212`, `T213`;
[[FilingGuard_AI_SRS]];
[[docs/product/FilingGuard product direction]];
[[apps/api/src/filingguard/modules/grounded_qa/README]];
[[apps/web/src/features/analyses/FindingQA]].

[[docs/sessions/Index]] | [[TODO]]
