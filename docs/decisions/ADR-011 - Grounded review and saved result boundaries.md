---
type: decision
status: accepted
date: 2026-10-08
tags: [decisions, evidence, privacy]
---
# Grounded review and saved result boundaries

## Context
T037–T051 require original filing context, bounded public source passages,
auditable model output and consistent inspection/export. BUG-012 showed that the
extraction-only partial-result contract discarded legitimate source outcomes.

## Decision and alternatives
Retain contained, importable stage workers and parent-only atomic persistence.
Pass allowlisted detached prior records through bounded private JSON pipes;
pass only the credential needed by a stage, through stdin rather than process
arguments or broad environment inheritance. Explicit configuration flags enable
CourtListener and Groq independently; both default off. Public intake stays off.

Accept typed partial citation/claim/proposition/quote results after parent checks
of ownership, original spans/anchors, evidence hashes/slices and relation IDs.
Proposition updates may change only existing link verdict fields, atomically with
their evidence. Do not enable arbitrary DB writes from workers or accept model
supplied evidence without matching it against supplied source passages.

Mask complete filing snapshots before selecting outgoing fields. Public source
windows are bounded and include surrounding context; insufficient selection and
missing opinions remain explicit. Only the provisional free-tier Groq 120B model
is allowlisted, with strict versioned output, no retries and no paid fallback.
Categorical model confidence is uncalibrated; numeric confidence stays absent.

October 10 amendment: proposition prompt/method v3 returns immutable source evidence
unit IDs only. Partition selected source passages into ordered contiguous units of
at most 600 characters, retaining every original character and surrounding context.
The server binds allowlisted IDs to exact excerpts and original Unicode spans;
reject unknown or repeated IDs. Asking models to copy exact source excerpts/count
offsets was rejected after actual v1/v2 calls failed exact excerpt validation.
No normalized or invented excerpt becomes accepted source evidence. The v3 binding
is offline verified, and the final two live Brown controls matched their supported/
reversed expectations with exact bound evidence. Broader expert legal accuracy and
hosted acceptance remain release gates. See
[[docs/research/Grounded proposition live acceptance - 2026-10-10]].

Keep immutable evidence snapshots. Bound citation queries/authorities to 25,
occurrences to 200, claim contexts to 100, proposition links to 25 and quotes to
50. Worker JSON input/output is limited to 16 MiB; source/document snapshot
sub-budgets avoid losing all prior results when later work exceeds a limit.
An omitted opinion is unavailable, never presented as a shortened complete source.

Generate score, graph, findings and Markdown/HTML from persisted results. Score
weights measure review priority and remain provisional; coverage is displayed
separately and no score implies filing safety. Export never reclassifies or calls
providers. Escape HTML and mask evidence against snapshots before clipping.

## Consequences
Lexical passage selection may miss controlling qualifications; the model cannot
review an entire opinion implicitly. Claim extraction is heuristic context
selection, not proof of a legal proposition. Quote similarity is textual only.
Partial results preserve useful checks but require human review of unknowns.
Worker startup counts toward existing deadlines and must be measured separately
from fixture accuracy. Hosted controls need explicit release verification.

## Evidence and verification
Focused tests exercise exact spans, transport-level masking, schema/refusal/
invented-evidence rejection, quote comparison, snapshot integrity and saved-view
agreement. Real worker, browser and live model outcomes are recorded in
[[docs/sessions/2026-10-10 - Grounded review verification]], distinguishing
synthetic controls from genuine public source/model verification.

## Related
[[TODO]] | [[docs/issues/BUG-012 - Citation verification output conflicts with worker validation]]
[[apps/api/src/filingguard/modules/analyses/README]]
[[apps/api/src/filingguard/modules/propositions/README]]
[[apps/api/src/filingguard/modules/reports/README]]
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]]
[[docs/decisions/Index]]
