---
type: decision
status: accepted
date: 2026-09-27
tags: [decisions, llm]
---
# Free-tier Groq evaluation

## Context
The user is a solo student developer and limits LLM spending to free credits.
The user explicitly chose Groq and wants us to compare available free models.

## Decision and alternatives
Evaluate Groq first; no final model is selected. Compare GPT-OSS 120B and 20B
if available on the account, then other strict-schema models if needed.
Gemini was considered but not selected. Use the existing OpenAI-compatible
client with Groq's base URL; do not send requests to OpenAI by default.

## Consequences
T005 must compare supported, unsupported, contradictory, insufficient-evidence
and prompt-injection examples against attributed source passages. Measure schema
validity, source-span accuracy, false support, refusal handling, tokens and latency.
Choose based on those results and account quotas, not model size alone.
Do not enable billing or silently fall back to paid providers. Use only public
or synthetic material during evaluation; provider privacy terms need review.

## Evidence and verification
User selection is confirmed; account access, quotas and model quality are not.
Groq documents strict structured outputs for GPT-OSS 20B/120B and an
OpenAI-compatible API. Schema validity does not establish legal correctness.

- [Structured outputs](https://console.groq.com/docs/structured-outputs)
- [OpenAI-compatible client](https://console.groq.com/docs/responses-api)
- [Account setup](https://console.groq.com/docs/quickstart)
- [Rate limits](https://console.groq.com/docs/rate-limits)

## Related
[[TODO]] (T005), [[docs/architecture/stack]], [[docs/decisions/Index]],
[[docs/decisions/ADR-001 - Stack and MVP execution]].
