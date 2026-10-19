---
type: session
status: verified
date: 2026-10-19
tags: [sessions, court-rules, privacy, t205]
---
# Advanced formatting and jurisdictional privacy

## Task and scope
Implemented T205 (FR-147 / FR-167): versioned page-limit and extra-heading checks,
plus configurable jurisdictional privacy bindings. Did not edit [[TODO]]. Did not
commit, push, deploy, or add a Neon migration.

## Changes
- `court_rules` profiles may include optional `page_limit`, `required_headings`,
  and `privacy_policy`. Checks run only when those fields are present and the
  profile is in-scope for demo/live mode and effective dates.
- Synthetic demo: 20-page training limit, `STATEMENT OF ISSUES` heading, and
  `synthetic-demo-privacy-v1` (email extra). Not a real court.
- N.D. Tex. live profile: still LR 7.2(f) only for formatting. Binds
  `us-frcp-5-2-v1` as a conservative FRCP 5.2 reminder with no extra identifier
  kinds. LR 7.2(c) page limits stay off because filing type is unknown.
- Unknown, stale, source-mismatched, or demo/live-mismatched privacy policies
  are unavailable limitations and do not enable extra kinds or a pass.
- Unpaginated page-limit evaluation is unavailable, not a pass.

## Verification
- `uv run ruff check` on court_rules, privacy, `runners.py` and the focused tests:
  passed.
- Parent re-run: ruff plus `test_court_rules.py`,
  `test_deterministic_checks.py`, `test_court_rule_source_registry.py`,
  `test_curated_demo.py`: 36 passed.
- Parent fix: unpaginated demo page-limit is counted as `unavailable` and the
  court_rules stage is `partial`, not completed-with-omitted-check.
- Not run: full API suite, web tests, hosted/Neon, browser review.

## Blockers and next step
Live N.D. Tex. page-limit/TOC checks need a filing-type input and a
court-counted-page method before they can be activated. Next ordered task is
the bounded T208 identity slice. Curated demo reviews can emit a synthetic
missing `STATEMENT OF ISSUES` finding.

## Related
[[apps/api/src/filingguard/modules/court_rules/README]]
[[apps/api/src/filingguard/modules/privacy/README]]
[[docs/research/N.D. Tex. formatting and FRCP 5.2 privacy bindings - 2026-10-19]]
[[docs/sessions/Index]]
