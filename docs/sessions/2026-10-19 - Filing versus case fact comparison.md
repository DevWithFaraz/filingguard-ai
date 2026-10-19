---
type: session
status: verified
date: 2026-10-19
tags: [sessions, propositions, p2, t203]
---
# Filing versus case fact comparison

## Task and scope
Implemented **T203** (FR-088) as a separate heuristic filing-versus-source fact
comparison inside proposition review. It does not add a legal-strategy engine or
invent analogies.

## Changes
- For each extracted claim with retrieved passages, bounded dates, `v.` parties,
  and numeric holdings are compared with source passages without extra model calls.
- Matching facts add no finding. Contradictory date/party/numeric facts emit a
  `claim_support` finding titled "Filing fact may not match source fact" with
  bound filing and passage evidence. Missing source or missing source facts are
  insufficient, never a pass.
- Semantic review remains opt-in; when disabled the propositions stage, including
  this check, is unavailable with an explicit reason.
- Results copy treats fact-titled `claim_support` findings as heuristic fact
  comparison rather than generative proposition review.

## Verification
- `uv run ruff check` on touched API files: all checks passed.
- `uv run pytest tests/unit/test_fact_comparison.py tests/unit/test_propositions.py`: 32 passed.

## Checks not run
- Full API suite and frontend tests (unless run after this handoff).
- Live Groq or hosted reviews.
- Expert legal validation of extracted facts.

## Blockers and next step
Heuristic extraction covers dates, case-style parties, money, percents, and
day/year/month/week counts. It does not resolve pronouns, implied parties, or
legal analogies. Next ordered task remains T202 unless the user redirects.

## Related
[[TODO]] T203 · [[apps/api/src/filingguard/modules/propositions/README]]
· [[FilingGuard_AI_SRS]] FR-088

[[docs/sessions/Index]] | [[TODO]]
