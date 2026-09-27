---
type: research
status: verified
date: 2026-09-27
tags: [research, providers]
---
# Provider access verification

## CourtListener (T004)
Authenticated GET api-usage, POST citation-lookup for 576 U.S. 644, and GET
opinions/2812209 returned HTTP 200 on September 27 at 11:49 UTC.
Lookup was unambiguous, cluster 2812209; opinion plain_text had 206,987 characters.
SHA256: 01284cf31aa9e64c152f3be8f095c3559be25896882d1be402bcf97bf86d73df.
This verifies access and text availability, not the filing's propositions.

Account-reported limits: user 10/minute, 100/hour, 250/day; citations 60/minute;
usage endpoint 10/minute and 120/hour. Limits are an observation, not a permanent
contract; honor live quotas/429 and bound/cache opinion retrieval later.

- [Opinion source](https://www.courtlistener.com/api/rest/v4/opinions/2812209/)
- [Citation API](https://wiki.free.law/c/courtlistener/help/api/rest/v4/citation-lookup)
- [Usage API](https://wiki.free.law/c/courtlistener/help/api/rest/v4/api-usage)

## Groq (T005, preliminary evaluation)
Authenticated model listing returned 200. Active IDs include openai/gpt-oss-120b,
openai/gpt-oss-20b and qwen/qwen3.8-27b. Model listing alone does not prove inference
permission, free-tier billing state or legal accuracy.

Two explicit generation calls succeeded with strict JSON schemas, temperature 0,
low reasoning effort, 2,048 maximum completion tokens, a 20-second timeout and
no retries. Each evaluated the same five synthetic lease-notice propositions.

- GPT-OSS 120B: 5/5 expected verdicts, 1.516 seconds, 703 prompt tokens,
  409 completion tokens (1,112 total).
- GPT-OSS 20B: 3/5 expected verdicts, 0.932 seconds, 703 prompt tokens,
  236 completion tokens (939 total). Reserved question classified as not_addressed;
  instruction-attack case also classified as not_addressed rather than contradicted.

Both passed schema, case identity and verbatim evidence-substring checks. These
checks prove quotation presence, not that the quote supports a proposition.
One request per model is not a robust benchmark; no real-case accuracy claim is
made. The harness itself was authored for this project and is labeled synthetic.
User confirmed 120B as the provisional default; GROQ_MODEL is set locally.
No raw responses were saved. Measured token usage is not a billing receipt;
the user authorized a free-tier-only plan and no billing changes were made.

Response headers reported an 8,000 token limit and 1,000 request limit; provider
docs describe their windows. Verify actual account limits before load testing.
Throttle conservatively; do not treat a model's context window as our quota.

Offline checks: nine validator tests cover a valid result, refusal, truncation,
invalid JSON, invented quote, duplicate ID, missing result, extra field and missing
evidence. With the health test, the suite has ten passing tests. Refusal/truncation
were synthetic tests, not observed live provider behavior.

- [Model list](https://console.groq.com/docs/models)
- [Structured outputs](https://console.groq.com/docs/structured-outputs)
- [Rate-limit windows](https://console.groq.com/docs/rate-limits)

## Reproduction and boundaries
From root: `node scripts/api.mjs run python scripts/check_provider_access.py courtlistener`
or replace courtlistener with groq. Explicit live checks print whitelisted metadata
only. No raw provider payloads or keys are persisted. Environment fallback supports
keys entered in the root .env, but apps/api/.env is preferred.
Initial sandbox connection failed; the approved network retry succeeded.

Related: [[TODO]], [[docs/research/Index]], [[docs/decisions/ADR-003 - Free-tier Groq evaluation]],
[[apps/api/src/filingguard/integrations/courtlistener/README]].
