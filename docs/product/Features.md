---
type: index
tags: [product, modules]
---
# Feature and module map

[[Home]] | [[FilingGuard_AI_SRS]] | [[TODO]] | [[docs/product/README]]

Feature implementation status lives in TODO. These links connect responsibilities,
not completed functionality. Refer to SRS requirement IDs when recording decisions
or bugs; link back here from those notes when useful.

## P0 processing

- Intake and parsing (FR-001-025): [[apps/web/src/features/intake/README|Intake UI]]
  and [[apps/api/src/filingguard/modules/documents/README|Document engine]].
- Analysis lifecycle: [[apps/api/src/filingguard/modules/analyses/README|Pipeline]]
  and [[apps/web/src/features/analyses/README|Progress and dashboard]].
- Citations (FR-040-046): [[apps/api/src/filingguard/modules/citations/README|Citation engine]]
  and [[apps/api/src/filingguard/integrations/courtlistener/README|CourtListener adapter]].
- Claims/propositions (FR-060-086, FR-088): [[apps/api/src/filingguard/modules/claims/README|Claims]],
  [[apps/api/src/filingguard/modules/propositions/README|Proposition review]],
  [[apps/api/src/filingguard/integrations/llm/README|LLM adapter]] and
  [[apps/api/src/filingguard/resources/prompts/README|Prompt resources]].
- Quotes (FR-120-128): [[apps/api/src/filingguard/modules/quotes/README|Quote forensics]].
- Court checks (FR-140-145): [[apps/api/src/filingguard/modules/court_rules/README|Rule engine]]
  and [[apps/api/src/filingguard/resources/courts/README|Court profiles]].
- Privacy (FR-160-166): [[apps/api/src/filingguard/modules/privacy/README|Privacy detection]]
  and [[apps/api/src/filingguard/integrations/storage/README|Private storage]].

Some requirement ranges include P1 refinements; TODO owns the exact implementation
order and priority reconciliation.

## Review and evidence

- [[apps/api/src/filingguard/modules/scoring/README|Integrity score and coverage]]
- [[apps/api/src/filingguard/modules/evidence/README|Evidence capture and provenance]]
- [[apps/web/src/features/findings/README|Explainable findings UI]]
- [[apps/web/src/features/claim-authority-graph/README|Claim-authority graph]]
- [[apps/api/src/filingguard/modules/reports/README|Report engine]],
  [[apps/api/src/filingguard/resources/reports/README|Templates]] and
  [[apps/web/src/features/reports/README|Report UI]]

## Later features

- P1 Red Team: [[apps/api/src/filingguard/modules/red_team/README|Backend]] and
  [[apps/web/src/features/red-team/README|UI]].
- P1 grounded Q&A: [[apps/api/src/filingguard/modules/grounded_qa/README|Backend]]
  and [[apps/web/src/features/grounded-qa/README|UI]].
- P2 [[apps/api/src/filingguard/modules/table_of_authorities/README|Table of Authorities]].
- P2 [[apps/api/src/filingguard/modules/statutes/README|Statute and regulation verification]].
- P2 claim corrections (FR-065): [[apps/api/src/filingguard/modules/claim_corrections/README|Backend]]
  and [[apps/web/src/features/findings/README|Findings UI]].
- P2 optional local identity claim (bounded T208):
  [[apps/api/src/filingguard/modules/identity/README|Identity]].

## Platform and tests

User-facing design plan: [[docs/product/UI direction]] (proposed, assets supplied)
and [[design]] (motion/interactive redesign brief, not implemented).

- [[apps/api/src/filingguard/api/routes/README|HTTP routes]],
  [[apps/api/src/filingguard/core/README|Configuration and shared infrastructure]],
  [[apps/api/src/filingguard/db/models/README|Persistence]],
  [[apps/api/migrations/versions/README|Migrations]].
- [[contracts/README|API contracts]] and [[apps/web/src/lib/api/README|Browser API boundary]].
- [[apps/web/src/app/README|App composition]], [[apps/web/src/components/layout/README|Layout]],
  [[apps/web/src/components/ui/README|UI primitives]], [[apps/web/src/assets/README|Bundled assets]],
  [[apps/web/public/README|Public assets]].
- [[apps/web/src/test/README|Frontend tests]], [[apps/api/tests/integration/README|Integration tests]],
  [[tests/e2e/README|End-to-end acceptance]] and [[data/demo/README|Demo fixtures]].
- [[infra/README|Infrastructure]], [[scripts/README|Utilities]] and
  [[docs/delivery/README|Release and acceptance]].

Related knowledge: [[docs/decisions/Index]], [[docs/issues/Index]],
[[docs/learnings/Index]], [[docs/research/Index]].
## Demo review material

[[data/demo/curated-v1/README]] and [[docs/product/Demo fixture review]] provide
the T014 fixture and completed delegated T015 AI review; they are not observed engine results.
