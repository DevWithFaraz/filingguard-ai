---
type: issue
status: resolved
date: 2026-10-10
tags: [issues, acceptance, providers]
---
# Free-tier throttling blocks curated semantic acceptance

## Symptom and reproduction
Run the curated browser journey with explicit genuine-model opt-in. Four claims
have cached source text. Three attempts failed the expected supported/reversed
Brown pair; later claim outputs remained unavailable. Independent saved checks
survived, including citations, quote forensics, privacy, rules, graph and exports.

## Evidence and cause
The final diagnostic integrated run retained fixed provider codes: Brown/Miranda
supported; Obergefell/reversed Brown unavailable with `rate_limited`; invented
authority insufficient_source. Earlier two runs did not retain failure codes,
so their precise causes are unconfirmed. A single actual extracted reversed-Brown
call returned misrepresented with two bound evidence records, no clipping.
Those October 10 runs did not measure account limits/reset times.

## Next check and limits
Resolved locally October 11. Allowlisted numerical response headers measured
8,000 tokens/minute. Admission pacing alone still left the fourth individual claim
outside the stage budget. A bounded two-claim request for the same Brown authority
shares overlapping source characters while preserving every qualification and
independent verdict/evidence binding. No response retry, paid fallback or source
pruning was introduced. Admission waits remain inside stage/overall deadlines;
the HTTP operation keeps its own 20-second cap.

The final genuine-model browser journey passes all twelve SRS 18.2 controls,
including three supported claims and reversed Brown misrepresented, evidence,
graph, report and reset. Analysis 52.803s; progress 187ms; dashboard 641ms.
Three actual model requests reviewed four sourced claims. The preview explicitly
uses a 60-second stage budget; production's default remains 30 until deliberately
configured. External organization usage can still exhaust quota, and explicit
unavailability remains required. Cached sources and AI-reviewed synthetic ground
truth do not establish expert real-case legal accuracy or hosted acceptance.

Evidence: `.runtime/curated-live-final-2026-10-11.json` and
`.runtime/live-tokens-final-2026-10-11.json` contain sanitized local receipts.
[[docs/decisions/ADR-013 - Shared authority model requests and bounded quota admission]]
and [[docs/sessions/2026-10-11 - Accessibility performance and release gates]].

## Related
[[TODO]] | [[docs/sessions/2026-10-10 - Curated demo acceptance]]
[[apps/api/src/filingguard/integrations/providers/README]]
[[apps/api/src/filingguard/modules/propositions/README]] | [[docs/issues/Index]]
