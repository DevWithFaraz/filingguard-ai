---
type: research
status: verified
date: 2026-10-19
tags: [research, court-rules, privacy, nd-texas]
---
# N.D. Tex. formatting and FRCP 5.2 privacy bindings - 2026-10-19

## Question
Which versioned formatting and jurisdictional privacy rules can FilingGuard attach
to the existing N.D. Tex. and synthetic demo profiles without treating unknown
filing type or unknown policy as a pass?

## Sources
- [N.D. Tex. Local Civil Rules PDF](https://www.txnd.uscourts.gov/sites/default/files/documents/CIVRULES.pdf),
  court compilation marked effective September 1, 2026; accessed 2026-10-19.
- [N.D. Tex. LR 7.2 HTML convenience text](https://www.txnd.uscourts.gov/briefs),
  non-official HTML; accessed 2026-10-19. The court states the PDF is controlling.
- [Federal Rules of Civil Procedure (U.S. Courts current-rules page)](https://www.uscourts.gov/rules-policies/current-rules-practice-procedure/federal-rules-civil-procedure),
  used as the catalog source URL for Fed. R. Civ. P. 5.2; accessed 2026-10-19.

## Findings

### Supported facts
- LR 7.2(c) (PDF compilation): unless another local civil rule provides otherwise,
  a brief must not exceed 25 pages excluding table of contents and table of
  authorities; a reply brief must not exceed 10 pages.
- LR 7.2(d): a brief in excess of 10 pages must contain a table of contents and an
  alphabetically arranged table of authorities, with page references.
- LR 7.2(f) remains the AI-use first-page heading already encoded on
  `us-txnd-lr7-2f-v1`.
- Fed. R. Civ. P. 5.2 addresses privacy protection for filings (limited identifiers
  such as Social Security numbers, taxpayer identification numbers, birth dates,
  minor names and financial-account numbers). FilingGuard already scans those
  families conservatively; this research does not add extra detector kinds for
  live N.D. Tex. reviews.

### Product inference
A live 25-page check would overclaim: the evaluator does not know whether the
document is a principal brief, a reply, a summary-judgment brief under another
local rule, or a non-brief filing, and extracted pages are not court-counted pages
excluding tables. T205 therefore stores page-limit and extra-heading rules on the
synthetic demo profile only, and binds N.D. Tex. to a versioned FRCP 5.2 reminder
with zero extra identifier kinds.

### Unresolved questions
- Whether a later intake field for filing type (motion brief vs reply vs LR 56.5)
  would be enough to activate LR 7.2(c)/(d) without excluding tables from the page
  count.
- Whether N.D. Tex. or another court publishes a distinct local privacy rule that
  should replace the FRCP 5.2 reminder.

## Applicability and expiry
Recheck the N.D. Tex. PDF compilation and the U.S. Courts FRCP page before
activating any live page-limit or extra-heading rule. Local rules in this district
are on a September 1 modification cycle. A source-checked date is not proof that
a rule applies to a specific filing.

## Related
[[TODO]] T205; [[FilingGuard_AI_SRS]] FR-147 / FR-167;
[[apps/api/src/filingguard/modules/court_rules/README]];
[[apps/api/src/filingguard/modules/privacy/README]];
[[docs/research/Index]]
