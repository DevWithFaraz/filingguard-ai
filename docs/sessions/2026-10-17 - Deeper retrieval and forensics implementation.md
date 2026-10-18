---
type: session
status: verified
date: 2026-10-17
tags: [sessions, forensics, retrieval, quotes, citations, phase-b, verification]
---
# Deeper retrieval and forensics implementation

## Task and scope
User authorized starting Phase B task: [[TODO]] `T107` (Deeper retrieval and forensics: `FR-025`, `FR-045/046`, `FR-087`, `FR-127`).
The requirements specify:
1. `FR-127`: Flag quotation alterations that may reverse or alter meaning (negations added or omitted, modal obligations changed such as shall/must vs may, contradictory antonyms, or qualifying clauses omitted before ellipses) with elevated severity (`critical` or `high`) and structured `meaning_alteration` metadata.
2. `FR-025`: Detect document text parsing quality diagnostics (sparse or empty pages, Unicode replacement characters, fused tokens exceeding 40 characters without whitespace, and low character density under 40 characters/page) and warn the user via a system finding.
3. `FR-045` & `FR-046`: Detect duplicate citations, surface repeated occurrences in the UI with a `Repeated ({duplicate_count}x)` badge and clickable repeated location pills, and track versioned source cache metadata (`cached`, `cache_hit`, `cache_version="courtlistener-cache-v1"`).
4. `FR-087`: Multi-passage retrieval from long opinions exceeding 15,000 characters, selecting up to 4 non-overlapping qualified passages (<=12,000 code points) with structural candidate diversity across early, middle, and late sections while prioritizing holding language (`METHOD_VERSION = "lexical-qualified-multi-passage-v3"`).

## Changes

### 1. Quotation Meaning-Changing Alteration Detection (FR-127)
- **Schemas (`apps/api/src/filingguard/modules/quotes/schemas.py`):**
  - Added `MeaningAlteration` contract: `alteration_type: str`, `description: str`, `filing_cue: str | None`, `source_cue: str | None`.
  - Added `meaning_alteration: MeaningAlteration | None = None` to `QuoteComparison`.
- **Forensic Detection (`apps/api/src/filingguard/modules/quotes/service.py`):**
  - Defined lexical dictionaries: `_NEGATION_WORDS`, `_MANDATORY_WORDS`, `_PERMISSIVE_WORDS`, `_QUALIFIER_WORDS`, and `_ANTONYM_PAIRS`.
  - Implemented `check_meaning_alteration(filing_quote, source_match, source_context)` to detect negation mismatch, modal flips, dropped qualifying clauses preceding ellipses, and direct antonym reversals.
  - In `compare_quote`, expanded source context around RapidFuzz matching slice to sentence boundaries (up to 200 characters) so boundary words and surrounding caveats are evaluated.
- **Stage Severity Escalation (`apps/api/src/filingguard/modules/quotes/runner.py`):**
  - When meaning alteration is detected, escalated finding severity to `critical` (negations/modals/antonyms) or `high` (dropped qualifying clauses), updated finding title with explicit warning, and attached structured metadata.
- **Tests:** Added 5 unit tests in `apps/api/tests/unit/test_quotes.py` covering negation addition, negation removal, modal flipping, ellipsis qualifier omission, and antonym reversals.

### 2. Document Parsing Diagnostics (FR-025)
- **Schemas (`apps/api/src/filingguard/modules/documents/schemas.py`):**
  - Added `diagnostics: list[str] = Field(default_factory=list, max_length=50)` to `ExtractedDocument`.
- **Extraction Diagnostics (`apps/api/src/filingguard/modules/documents/extraction.py`):**
  - Implemented `detect_parsing_diagnostics(text, pages, paragraphs)` checking for empty/sparse pages (<20 chars), replacement characters (`\ufffd` density > 1%), fused tokens (>40 consecutive non-whitespace characters), and low overall density (<40 chars/page).
- **Stage Findings (`apps/api/src/filingguard/modules/analyses/runners.py`):**
  - In `privacy_stage`, checks `analysis.document_snapshot.get("diagnostics")` and emits an actionable system finding (`severity="high"` if replacement chars or fused tokens, otherwise `"medium"`) with diagnostic details.
- **Tests:** Added unit tests in `apps/api/tests/unit/test_documents.py` for diagnostics detection and stage finding generation.

### 3. Duplicate Citation Display & Source Cache (FR-045, FR-046)
- **Schemas & Contracts (`apps/api/src/filingguard/modules/citations/schemas.py`, `apps/api/src/filingguard/api/contracts.py`):**
  - Added `cached: bool = False`, `cache_hit: bool = False`, and `cache_version: str | None = None` to `CitationVerificationMetadata`.
  - Defined `SOURCE_CACHE_VERSION = "courtlistener-cache-v1"` in `citations/service.py`.
  - Added `duplicate_count: int | None = None` and `repeated_locations: list[DocumentLocation] = Field(default_factory=list)` to `SafeCitation`.
- **Aggregation (`apps/api/src/filingguard/modules/reports/service.py`, `apps/api/src/filingguard/api/routes/intake.py`):**
  - Grouped citations by normalized/raw key, populating `duplicate_count` and distinct `repeated_locations`.
  - Regenerated OpenAPI specs (`npm run contracts:export`) and TypeScript definitions (`npm run contracts:generate`).
- **Frontend UI (`apps/web/src/features/analyses/ResultsView.tsx`, `results.css`):**
  - Rendered `Repeated ({duplicate_count}x)` badge and repeated locations pill list under citation occurrences.
- **Tests:** Added UI test in `apps/web/src/features/analyses/results.test.tsx` verifying duplicate badge and repeated location rendering.

### 4. Multi-Passage Retrieval from Long Opinions (FR-087)
- **Retrieval Engine (`apps/api/src/filingguard/modules/propositions/passages.py`):**
  - Upgraded `select_passages` to `METHOD_VERSION = "lexical-qualified-multi-passage-v3"`.
  - Allowed selecting up to 4 distinct non-overlapping passages (each bounded, sum <= `MAX_SOURCE_PASSAGE` = 12,000 characters).
  - For long opinions exceeding 15,000 characters, partitioned document into early, middle, and late structural sections, selecting the globally top-scoring candidate first, then ensuring candidates from other sections are represented before filling remaining slots.
  - Prioritized explicit holding language (`+3` score boost) and dynamically clipped windows if necessary to respect total character budget.
- **Integration Boundary (`apps/api/src/filingguard/integrations/llm/adapter.py`, `apps/api/src/filingguard/integrations/llm/batch.py`):**
  - Updated passage count limit from 2 to 4 in LLM adapter and batch executor validation guards.
- **Tests:** Added `test_multi_passage_retrieval_across_structural_sections` and `test_multi_passage_miranda_fixture_structural_diversity` in `apps/api/tests/unit/test_propositions.py`.

## Verification
- `npm run lint:api` (`ruff check .`) — passed (0 errors).
- `node scripts/api.mjs run pytest` — 749 passed, 0 failed, 2 skipped across all test files.
- `npm run lint:web` (`eslint .`) — passed (0 errors).
- `npm run typecheck` (`tsc --noEmit`) — passed (0 errors).
- `npm run test:web` (`vitest run`) — 52 passed across 7 test files.
- `npm run build` (`vite build`) — production bundle built cleanly in 15.34s.

## Blockers and next step
No blockers. T107 is verified and checked off in [[TODO]].
Next tasks in [[TODO]] under Phase B:
- `T108` - Possible minor-name heuristics (`FR-163`), with explicit uncertainty and false-positive controls. Done when synthetic cases and benign controls are reviewed.
- `T106` - Additional verified real court profiles (`FR-146`): primary sources, applicability/effective dates, judge-specific scope and profile regression tests. Note: requires selecting an external court profile and primary-source verification per ADR-014 and product direction.
- `T109` - Durable job execution if needed: worker/queue, leases, idempotency, crash recovery and bounded retries.

## Related
[[TODO]] `T104`, `T105`, `T107`, `T108`;
[[FilingGuard_AI_SRS]];
[[docs/product/FilingGuard product direction]];
[[apps/api/src/filingguard/modules/quotes/README]];
[[apps/api/src/filingguard/modules/documents/README]];
[[apps/api/src/filingguard/modules/citations/README]];
[[apps/api/src/filingguard/modules/propositions/README]];
[[apps/web/src/features/analyses/ResultsView]].

[[docs/sessions/Index]] | [[TODO]]
