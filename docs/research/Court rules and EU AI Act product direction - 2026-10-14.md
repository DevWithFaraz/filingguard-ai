---
type: research
status: verified
date: 2026-10-14
tags: [research, court-rules, eu-ai-act, product]
---
# Court rules and EU AI Act product direction - 2026-10-14

## Question
How should FilingGuard develop court-rule coverage without turning uncertain rules
into compliance claims, and does an Article 50 transparency assessment belong in
the filing-review product?

## Sources
- [Regulation (EU) 2024/1689, the AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng),
  especially Articles 50 and 113; primary legislation, accessed 2026-10-14.
- [European Commission Article 50 transparency FAQ](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act),
  official guidance updated 2026-07-24, accessed 2026-10-14.
- [European Commission Article 50 guidelines page](https://digital-strategy.ec.europa.eu/en/library/guidelines-transparency-obligations-providers-and-deployers-ai-systems),
  official guidance published 2026-07-20, accessed 2026-10-14.
- [S.D. Ohio Judge Graham standing order](https://www.ohsd.uscourts.gov/sites/ohsd/files/10-21-25%20JLG%20Standing%20Order%20on%20the%20Use%20of%20Generative%20AI.pdf),
  primary court order signed 2025-10-21, accessed 2026-10-14.
- [S.D. Texas General Order 2025-04](https://www.txs.uscourts.gov/sites/txs/files/general-orders/General_Order_2025-04_Use_of_Generative_AI_in_Court_Filings.pdf),
  primary court order signed 2025-05-07, accessed 2026-10-14.

The planning-conversation attachment mentioned in the task was not available in
the workspace or message context. The stated ideas in the request, current SRS,
current implementation and the sources above are the evidence used here.

## Findings

### Supported facts
- Article 50 applies from 2026-08-02. Its transparency obligations address defined
  provider and deployer roles, including direct AI interaction, machine-readable
  marking of certain generative outputs, deepfakes, and some published text. The
  Commission describes a limited Article 50(2) transition for pre-existing systems;
  it is not a general filing-disclosure rule.
- For Article 50(4), the Commission identifies three cumulative conditions for
  generated text: it is published, informs the public, and concerns a matter of
  public interest. Published text that has substantive human review or editorial
  control is described as exempt. A legal filing may involve administration of
  justice, but a filing workflow alone does not establish the remaining conditions,
  the responsible role, or the exception.
- The current FilingGuard live intake permits only `unverified`; the active profile
  is a synthetic training fixture. Its evaluator checks a standalone heading only.
  It cannot establish a declaration's required factual content, a signer's review,
  legal sufficiency, or actual court applicability.
- Judge Graham's order is scoped to that judge in the Southern District of Ohio's
  Eastern Division. It calls for a declaration with more than a caption: assisted
  content location, platform and stated certifications are also required.
- S.D. Texas General Order 2025-04 cautions filers to check accuracy and confirms
  signer responsibility under Rule 11. It does not state an AI-use disclosure or
  declaration heading requirement.

### Product inference
FilingGuard's central user problem is a responsible filer or reviewer trying to
catch avoidable, evidence-addressable defects before submitting a legal filing:
citation, proposition, quote, privacy and selected filing-rule risks. Court rules
fit as a selective, source-scoped layer of that workflow.

An Article 50 assessment has a different unit of analysis: the AI system, its
provider or deployer, output-publication context, audience, and substantive human
review. It can later reuse evidence, versioned rules and reporting infrastructure,
but it should not be represented as a court profile or a generic AI-use disclosure
check. It is a separate product or isolated future module pending a validated user
and evaluation scope.

### Unresolved questions
- Neither court order retrieved here states a current end date. Their records are
  therefore reference-only, with current force unconfirmed rather than assumed.
- No target jurisdiction, court or judge has been selected from observed FilingGuard
  user demand. An active profile would need that choice, a current official source,
  exact scope confirmation, and full support for every machine-checkable condition.
- This research does not decide whether a particular legal filing falls within
  Article 50, whether a user is a provider or deployer, or whether a human-review
  exception applies. Those are context- and legal-assessment questions.

## Applicability and expiry
Recheck the Commission guidance, AI Act consolidated text, and each court source
before any activation. A rescission, amendment, case assignment, local rule, or
later official guidance can change applicability. The checked date records source
access, not an opinion that a rule is in force for every filing.

## Related
[[TODO]] T111/T106; [[FilingGuard_AI_SRS]] FR-140 through FR-146;
[[docs/decisions/ADR-014 - Filing-centric court rules and separate Article 50 direction]];
[[apps/api/src/filingguard/modules/court_rules/README|Court rule engine]];
[[apps/api/src/filingguard/resources/courts/README|Court source records]].

[[docs/research/Index]]
