---
type: decision
status: accepted
date: 2026-10-14
tags: [decisions, product, court-rules, eu-ai-act]
---
# ADR-014 - Filing-centric court rules and separate Article 50 direction

## Context
FilingGuard is implemented as a pre-submission review workflow for legal filings.
It currently has one explicitly synthetic court-profile fixture; live filings keep
court-rule applicability unavailable. Product exploration raised an Article 50 AI
Act transparency inspector alongside broader jurisdiction-specific court rules.

The current court evaluator can establish only the presence of a standalone heading.
It cannot verify all terms of a real declaration, a filer's role, exact case/judge
assignment, a rule's current force, or a filing's legal sufficiency. The product
must not turn an accessible rule URL or an AI-used checkbox into a compliance claim.

## Decision and alternatives
Keep FilingGuard filing-centric: it helps a filer prepare a document for human
review by surfacing evidence-addressable risks. Versioned court-rule sources may
become a selective layer in that workflow only when their exact scope and all
machine-checkable obligations are supported.

Maintain official-source court records as `reference_only` until they can meet that
bar. They cannot be selected in live intake, loaded as profiles or produce a pass.
Missing jurisdiction, unconfirmed current status, and incomplete implementation
remain unavailable.

Treat an Article 50 transparency assessor as a separate future product direction or
isolated module. It may later share generic rule-versioning, evidence and report
infrastructure, but it will have its own intake and outcomes for provider/deployer
role, system/output type, publication context and human review. Do not place it in
the FilingGuard court-profile selector and do not label results “EU compliant.”

Rejected for now:
- Adding Article 50 to a filing's AI-use disclosure check, because its scope and
  role analysis are different from a court filing rule.
- Activating a single real court profile based on a heading, because the available
  primary examples either require additional declarations or do not require a
  disclosure at all.
- Broad country or court coverage, because the SRS excludes nationwide coverage and
  source maintenance/application evidence is not yet available.

## Consequences
T111 records two source-backed, non-active court-order candidates. It establishes
traceability and prevents accidental activation, but it does not complete T106 or
provide a real court-rule check. The existing synthetic demo and live `unverified`
behavior remain unchanged.

The next active court profile must start from a selected filing context with user
value, current primary-source confirmation and a requirement matrix that distinguishes
deterministic checks, structured user attestations, human review items and unavailable
items. If no such target is supported, prioritize evidence lineage and the existing
pre-filing workflow instead.

An Article 50 discovery effort should occur only after a separate user/problem
hypothesis, official-scope update process and evaluation set exist. It must not use
confidential filings, additional hosted providers or a deployment change as part of
that discovery.

## Evidence and verification
Official primary court orders and Commission/AI Act sources are recorded in
[[docs/research/Court rules and EU AI Act product direction - 2026-10-14]].
`source_registry.py` validates each source's URL, version, locator, scope, checked
date and non-active status. Its focused tests prove the records cannot be passed to
the active profile loader and yield unavailable if evaluated.

The sources support the described texts and scopes, not a conclusion that either
order currently applies to every filing. No legal advice, court consultation,
confidential-filing processing, provider change or hosted deployment was performed.

## Related
[[docs/decisions/Index]], [[TODO]] T111/T106/T212/T213,
[[FilingGuard_AI_SRS]] FR-140 through FR-146,
[[docs/research/Court rules and EU AI Act product direction - 2026-10-14]],
[[apps/api/src/filingguard/modules/court_rules/README|Court rule engine]],
[[docs/decisions/ADR-005 - Product continuation and reviewed demo]],
[[docs/decisions/ADR-007 - Private preparation boundary]].
