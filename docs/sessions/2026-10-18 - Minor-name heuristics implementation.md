---
type: session
status: verified
date: 2026-10-18
tags: [sessions, privacy, heuristics, minor-names, phase-b, verification]
---
# Minor-name heuristics implementation

## Task and scope
User commanded `/boost start remaining phase B`.
In accordance with `AGENTS.md` ("Work solo unless the user changes the no-subagent instruction"), executed the Solo Routine.
Following task status in [[TODO]], addressed the next Phase B capability: `T108` (Possible minor-name heuristics `FR-163` with explicit uncertainty and false-positive controls).

Requirements:
1. Detect possible unredacted minor names in legal filings under Fed. R. Civ. P. 5.2(a)(3) and state court privacy equivalents.
2. Implement strict false-positive controls to protect compliant initials ("A.B.", "J. D."), non-person adjectives ("minor injury", "minor delay"), case citations ("Minor v. Happersett"), and institutional/legal entities ("United States District Court").
3. Flag detections as high-severity privacy findings with explicit uncertainty statements recommending human review.

## Changes
- **Pattern Detection (`apps/api/src/filingguard/modules/privacy/service.py`):**
  - Added `minor_name` regex pattern to `PATTERNS` capturing title-cased names associated with conventional legal indicators ("minor child", "minor son/daughter/ward", "a minor", "on behalf of ... a minor", "guardian ad litem for ... a minor", "minor: ...").
  - Updated `mask_excerpt` to use `match.lastindex` dynamically, ensuring target name groups are accurately extracted and masked without disturbing surrounding context.
- **Validation & False-Positive Controls (`apps/api/src/filingguard/modules/privacy/checks.py`):**
  - Added `_EXCLUDED_NAME_TERMS` containing legal roles, judicial titles, court entities, and corporate suffixes.
  - Implemented `_valid_minor_name(name, full_text, start)`:
    - Enforces 2-4 capitalized words.
    - Suppresses single-letter initials (e.g. "A.B.", "J. D.") which comply with Rule 5.2(a)(3).
    - Excludes non-person tokens and case citations where "Minor" appears as a party surname.
- **Stage Findings & Uncertainty Disclosure (`apps/api/src/filingguard/modules/analyses/runners.py`):**
  - Mapped `minor_name` to `"Possible unredacted minor name"` in `privacy_stage`.
  - Configured high severity and an explicit uncertainty statement emphasizing that automated heuristic detection is not a legal compliance determination.
- **Documentation & Tests:**
  - Updated canonical module guide [`apps/api/src/filingguard/modules/privacy/README.md`](file:///c:/Users/IT/Documents/FilingGuard%20AI/apps/api/src/filingguard/modules/privacy/README.md).
  - Added synthetic positive and benign control test suites in [`apps/api/tests/unit/test_deterministic_checks.py`](file:///c:/Users/IT/Documents/FilingGuard%20AI/apps/api/tests/unit/test_deterministic_checks.py).

## Verification
- `npm run lint:api` (`ruff check .`) — passed (0 errors).
- `node scripts/api.mjs run pytest tests/unit/test_deterministic_checks.py` — 6 passed in 0.07s.
- `npm run lint:web` — passed (0 errors).
- `npm run typecheck` — passed (0 errors).

## Next step
`T108` is verified and checked off in [[TODO]].
Remaining Phase B tasks:
- `T110` - Expand accessibility (`UX-005`), audit timing/correlation (`LOG-003/004`, `NFR-023`), retention automation (`NFR-044`), and failure observability.
- `T106` - Additional verified real court profiles (`FR-146`): select target court filing context, verify primary sources and effective dates per ADR-014.
- `T109` - Durable job execution if multi-worker concurrency is required.
