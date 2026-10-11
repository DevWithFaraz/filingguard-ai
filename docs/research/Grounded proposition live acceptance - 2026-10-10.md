---
type: research
status: verified
date: 2026-10-10
tags: [research, propositions, providers, release-gates]
---
# Grounded proposition live acceptance - 2026-10-10

## Question

Can the actual bounded Groq adapter produce exact grounded evidence for the two
cached public Brown supported/reversed proposition controls required by T039?

## Sources and method

Run `apps/api/scripts/verify_grounded_review.py` from the API environment.
The curated-v1 fixture manifest and public source hashes, original source spans
and filing spans are verified before inference. Expected spans are used only to
check retrieval after selection; they are never inputs to passage selection or
inference. The source is a cached public CourtListener opinion, with provenance
in `data/demo/curated-v1/sources.json`. Synthetic claims are used; no client filing.

Model: `openai/gpt-oss-120b`, free credits, 2,048 completion tokens, low reasoning
effort, 20-second transport cutoff, zero retries and no fallback. Sanitized run
receipts are ignored runtime artifacts under `apps/api/.runtime`, not raw payloads.

## Observed findings

The October 8 two-call v1 run failed with `invalid_response` for both controls.
The remaining authorized October 10 diagnostic used one call and identified
`evidence_excerpt_mismatch`. The v1 contract asked the model to supply absolute
source offsets and an exact source substring.

Version 2 asks for a passage ID and exact excerpt, then computes its unique original
Unicode span locally. Unknown IDs, absent/repeated excerpts, missing substantive
evidence and interrupted/refused output remain rejected. Retrieval version 2 uses
bounded related lexical forms and holding-language preference. Offline selection
now includes each control's actual conclusion without expected-span hints.

The two authorized post-fix live calls on October 10 still failed with
`evidence_excerpt_mismatch`; both returned semantic outcomes were `unavailable`
with zero source evidence. Version 2 produced no verified supported/misrepresented result.
The initial five-call allowance across both dates was exhausted. A final bounded
two-call v3 probe was subsequently authorized after offline contract review.

Fifty-two focused adapter/proposition tests pass locally, including actual outgoing
masking, strict schema, nonzero Unicode span binding, duplicate/invented ID rejection
and cached Brown retrieval. Ruff passes. These verify plumbing and rejection
behavior, not legal classification accuracy.

## Applicability and unresolved questions

The cause may involve model changes to source formatting or quotation characters;
this is an inference, since raw model output was deliberately not retained. The
CourtListener snapshot contains original multiline layout. Do not silently normalize
provider excerpts into source evidence or extrapolate these controls to broader
legal acceptance.
Version 3 now uses precomputed immutable source evidence-unit IDs. The model selects
allowlisted IDs only, while the server binds exact original text and spans. Source
units of at most 600 characters partition the selected passage once, retaining the
complete neighboring context. Duplicate/unknown IDs fail closed. Offline schema,
source reconstruction and span binding are verified. The final v3 live probe completed
in 2.765 seconds with two attempts, zero failures and zero rejections. The supported
Brown control returned `supported`; the reversed control returned `misrepresented`.
Each had two bound `opinion_text` evidence records with prompt
`proposition-source-review-v3` and method `grounded-proposition-review-v3`.
Seven actual calls total were used: two original v1, one v1 diagnostic, two v2 and
two v3. No retry, fallback model, paid credit or additional call was used.
Only sanitized metadata is stored in the ignored runtime run receipts.

The fixture semantic expectations remain awaiting human review. Broader expert legal
QA and hosted acceptance remain independent release gates despite these two
successful live controls.

## Related

[[docs/research/Index]] | [[TODO]] | [[FilingGuard_AI_SRS]]
[[apps/api/src/filingguard/modules/propositions/README]]
[[apps/api/src/filingguard/integrations/llm/README]]
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]]
