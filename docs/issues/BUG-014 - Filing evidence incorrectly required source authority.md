---
type: issue
status: resolved
date: 2026-10-10
tags: [issues, evidence, workers]
---
# Filing evidence incorrectly required source authority

## Symptom and reproduction
The first complete grounded-review regression run failed four quote acceptance
cases. Newly added parent relation validation required every evidence record to
carry its finding's source authority, discarding an otherwise valid quote stage.
This was found locally before release; no public incident is claimed.

## Cause and fix
A quote finding identifies the resolved source authority. Its document evidence
proves the original filing text and legitimately has no authority ID; its opinion
evidence must identify the source authority. Validation now allows an absent
authority for document evidence while checking all other relations and requiring
any present authority to match. Opinion/AI source evidence retains strict source
identity, exact passage and hash validation.

## Verification
Fifteen focused repaired integration/boundary cases passed, including an explicit
document-accepted/opinion-rejected control. Final full-suite evidence is recorded
in [[docs/sessions/2026-10-10 - Grounded review verification]]. The scope is parent
worker evidence validation, not a relaxation of source binding.

## Related
[[TODO]] T040/T053/T056 | [[apps/api/src/filingguard/modules/analyses/README]]
[[apps/api/src/filingguard/modules/evidence/README]] | [[docs/issues/Index]]
