---
type: decision
status: accepted
date: 2026-10-11
tags: [decisions, providers]
---
# Shared authority model requests and bounded quota admission

Repeated genuine-model acceptance attempts returned explicit quota unavailability.
Measured response headers identify an 8,000 TPM bucket on this account. Selected
source windows contain 6,995–9,756 characters per proposition; two Brown checks
repeat overlapping authority context. No paid fallback, retries, expected verdict
substitution or source-context removal is authorized.

Pair at most two owned propositions citing the same verified authority. Merge
only overlapping/touching selected windows and transmit every original character
once. If the pooled context exceeds two windows or 12,000 characters, decline
batching before sending and retain the independent-call path. Never group using
fixture identity, expected status or legal risk labels.

The v4 batch schema requires exactly two uniquely identified verdicts. Each has
its own status, explanation, confidence and immutable source-evidence IDs. Missing,
foreign or duplicate claim IDs, invalid evidence, refusal and incomplete output
reject the batch without retrying it individually. Independent stages continue.
Source hashes, exact Unicode offsets, complete-filing masking and original stored
claim/link identities remain enforced. Every member records its shared request
group/batch size so usage is not incorrectly counted as separate provider calls.

Groq admission retains only allowlisted numeric TPM headers. Initial token cost is
a conservative byte estimate; later estimates scale prior actual prompt usage with
a 5% allowance. These are advisory estimates, not exact tokenization or guaranteed
quota reservations. Admission waits remain within the hard stage budget; afterward
the HTTP operation retains its 20-second cap. No required wait is shortened to fit.
Single replies cap at 768 completion tokens; a two-member batch caps at 1,024.
Incomplete replies remain unavailable. Source passages are unchanged.

The explicitly opted-in synthetic preview uses a 60-second stage limit within the
existing 90-second overall limit. Production's default stage limit remains 30
seconds; deployments enabling semantic review must choose and verify their budget.
This amends the quota-admission distinction in
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]].

Evidence: focused single/batch/masking tests pass, including punctuation and clipped
email addresses. Seven actual-contained-worker integration tests pass, including
paired verdict persistence, source evidence, graph/reports and batch refusal.
Synthetic responses are plumbing controls, not legal acceptance. Genuine batch
acceptance is recorded separately in the current handoff.

Related: [[TODO]] T052/T055/T056, [[docs/decisions/Index]],
[[apps/api/src/filingguard/integrations/llm/README]],
[[apps/api/src/filingguard/modules/propositions/README]],
[[docs/issues/BUG-017 - Free-tier throttling blocks curated semantic acceptance]],
[[docs/sessions/2026-10-11 - Accessibility performance and release gates]].

Reference: [Groq rate limits](https://console.groq.com/docs/rate-limits), checked
October 11. Limits apply to the organization; the published base table is not an
assertion about an account's exact quota. The measured header is the evidence here.
