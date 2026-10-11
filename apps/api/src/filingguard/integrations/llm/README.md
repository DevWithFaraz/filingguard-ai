# llm adapter

Groq structured outputs with bounded passages and explicit model selection. Schema
validity is not factual validity: validate evidence IDs/excerpts. Record actual
model, prompt version, timing and usage without logging filing text. An installed
OpenAI-compatible SDK does not authorize its implicit retries or a paid fallback.

Implemented locally: `GroqPropositionAdapter` uses the selected
`openai/gpt-oss-120b` model, strict JSON schema, 768 completion-token cap, low
reasoning effort and the existing 20-second fixed-host transport with zero retries.
Explicit worker credentials are required; this adapter never reads environment or
settings files, chooses another model or supplies demo output automatically.

October 11: outgoing source passages are unchanged. A conservative byte-based
token estimate, calibrated with prior actual prompt usage plus a 5% allowance,
and allowlisted numerical TPM headers pace new calls within the hard stage
deadline. Admission waits precede the independently capped 20-second HTTP
operation; they cannot extend the stage or overall deadline. Estimates are
advisory; external organization
usage can still cause 429. An unfittable wait returns explicit unavailability
before spending an attempt; actual 429 responses are never retried. Responses
ending because of the smaller output limit remain rejected. Focused offline
pacing/transport/evidence checks pass; final integrated acceptance is recorded in
[[docs/sessions/2026-10-11 - Accessibility performance and release gates]].
The opt-in preview allows a 60-second stage budget within the 90-second overall
deadline to measure the complete genuine-model journey. Production's existing
30-second stage default is unchanged.

`batch.py` can review two independently identified propositions against the same
verified authority. Overlapping source windows are pooled without dropping a
character or qualification; the existing two-passage / 12,000-character limit
still applies. A pool that exceeds those limits declines before transmission.
The batch uses a 1,024-token output cap and the v4 batch prompt/method. Each verdict
must bind a unique claim ID and allowlisted evidence IDs; malformed batches fail
atomically without a fallback request. Shared request-group metadata prevents
double-counting usage. No fixture expectation participates in grouping or review.
See [[docs/decisions/ADR-013 - Shared authority model requests and bounded quota admission]].

T024's [[apps/api/src/filingguard/integrations/providers/README]] provides the
fixed-host HTTP boundary, zero Groq retries, passage-size/masking helpers and
deadline/attempt accounting. Every outgoing filing-derived field comes from
`prepare_passage(full_original_filing, start, end, filing=True)` so detection scans
the full filing before clipping. Caller-supplied prompt strings and raw copied claim
fields are never accepted. Common instruction-injection patterns are rejected in
filing/source text, and the versioned prompt treats all evidence as untrusted data.
This is conservative defense, not a guarantee against all prompt injection.

Refusals, interrupted generations, unexpected tools/models, extra schema fields,
invented evidence IDs and mismatched exact excerpts fail closed. Only bounded usage,
timing and actual model/prompt/method metadata are retained. No production key or
live inference is used by focused HTTPX MockTransport tests.

The v3 wire contract asks for immutable evidence-unit IDs only. Selected source
passages are partitioned into contiguous units of at most 600 original characters,
with every character transmitted exactly once. Neighboring units retain surrounding
qualifications. The adapter resolves allowlisted IDs to exact source excerpts and
absolute Unicode spans locally; duplicate or unknown IDs are rejected. The stored
evidence contract still includes exact source offsets and hashes. Model copying and
offset arithmetic are not trusted inputs.

October 10 live v1/v2 controls failed: one diagnostic and two
post-fix calls using cached public Brown text failed exact excerpt validation.
No raw model response or credential was retained. After offline contract review,
the final two-call v3 live probe returned supported/misrepresented for the respective
Brown controls, each with two exact bound source evidence records. Seven calls total
across v1/v2/v3 were used, without retries or fallback. Broader legal accuracy and
expert review remain unverified. See
[[docs/research/Grounded proposition live acceptance - 2026-10-10]].

Protocol checked against [Groq structured outputs](https://console.groq.com/docs/structured-outputs)
and [Groq API reference](https://console.groq.com/docs/api-reference) on October 8, 2026.
Related: [[apps/api/src/filingguard/modules/propositions/README]], [[TODO]].
