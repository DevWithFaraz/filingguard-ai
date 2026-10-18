---
type: session
status: verified
date: 2026-10-14
tags: [sessions, product, court-rules, eu-ai-act]
---
# Filing-centric direction and court-source foundation

## Task and scope
User requested a solo reassessment of FilingGuard, jurisdiction-specific court
rules and an Article 50 AI Act concept. This session completed [[TODO]] T111 as a
small, reversible source-traceability foundation. T106 remains open; no real court
profile was activated.

## Changes
Read the current SRS, TODO, documentation workflow, relevant product/module notes,
decisions and prior MVP handoff, then checked the active court-rule implementation.
It supports only the synthetic demo profile and keeps live court rules unavailable.

Added a validated `reference_only` source registry with two official court-order
records: a judge-specific Southern District of Ohio declaration order and an S.D.
Texas accuracy/Rule 11 order that is not a disclosure rule. Records carry version,
official URL, locator, source-check date, scope, applicability state and activation
blockers. They cannot load as runtime profiles, be selected in live intake, or
produce a court-rule pass.

Moved the existing intake profile-eligibility guard ahead of repository access, so
an unsupported source ID is rejected before any intake state is touched.

Recorded ADR-014, source research and user feedback. The product direction is
filing-centric pre-submission review. Article 50 is a separate future product or
isolated module direction, because its provider/deployer, system and public-output
assessment differs from a filing-specific court rule. No “EU compliant” or
all-jurisdiction claim is made.

Added [[docs/product/FilingGuard product direction]] as the durable vault entry
point. It records the current product boundary, working workflow, rule lifecycle,
Article 50 separation, brainstormed options, phased roadmap and a future-agent
reading order without replacing TODO task status. [[AGENTS]] now directs relevant
future work to that note before scope or implementation decisions.

## Verification
- `uv --directory apps/api run --locked pytest tests/integration/test_intake.py tests/unit/test_court_rule_source_registry.py tests/unit/test_deterministic_checks.py` — 14 passed.
- `node scripts/api.mjs run ruff check src/filingguard/modules/court_rules tests/unit/test_court_rule_source_registry.py` — passed.
- `git diff --check` — passed; it reported only existing CRLF-to-LF warnings for
  modified tracked vault files.

No full API/frontend suite, browser test, live provider call, confidential filing,
database migration, hosted setting or deployment was run because this change adds
only local source records and fail-closed validation.

## Blockers and next step
The planning-conversation attachment referenced by the user was not available in
the workspace or message context; the stated ideas and project records were used.
The official court records do not establish current force for every filing, and no
target jurisdiction/court/judge has product-demand evidence yet.

T062 remains release hygiene. For the next court-rule investment, select one target
filing context and build a complete requirement matrix before T106. If that evidence
is not available, prioritize the existing workflow's lineage and reviewer value
instead. Keep Article 50 as a separately scoped discovery track.

## Related
[[TODO]] T111/T106/T212/T213;
[[docs/decisions/ADR-014 - Filing-centric court rules and separate Article 50 direction]];
[[docs/research/Court rules and EU AI Act product direction - 2026-10-14]];
[[docs/feedback/FB-015 - Filing-centric product direction and EU AI Act assessment]];
[[apps/api/src/filingguard/modules/court_rules/README|Court rule engine]];
[[docs/sessions/2026-10-12 - Product MVP readiness and priorities]].

[[docs/sessions/Index]] | [[TODO]]
