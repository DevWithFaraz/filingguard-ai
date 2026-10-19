# propositions

October 11: same verified-authority pairs may use the v4 shared-source batch.
Each proposition keeps its own exact filing span, saved verdict and bound source
evidence. Overlapping selected source windows merge without dropping characters;
oversized/nonmergeable pools retain individual calls. No expected fixture verdict
or ID is an inference input. Group IDs/batch size identify shared usage. Invalid
batch identity/evidence or refusal rejects its members without retry; unrelated
stages remain available. See
[[docs/decisions/ADR-013 - Shared authority model requests and bounded quota admission]].

Priority: P0/P2. Tasks: T038-T041 and T203 (FR-088) in the root TODO.md.

Compare claims to bounded retrieved passages and validate structured model results.
T203 adds a separate heuristic filing-versus-source fact comparison on those same
retrieved passages (dates, named parties, numeric holdings). It does not invent
legal analogies or change proposition support classification. Matching facts emit
no extra finding. Contradictory facts emit a `claim_support` finding titled
"Filing fact may not match source fact". Missing source or missing source facts
are insufficient or unavailable, never a pass. Semantic review remains opt-in;
when it is disabled the propositions stage, including fact comparison, is
unavailable with an explicit reason. The check is a labeled heuristic review
signal and requires human review.

Claims/evidence in; support status, explanation, evidence references and uncertainty out.

Implemented locally: deterministic lexical passage selection preserves exact Unicode
offsets and SHA-256, selects up to four source windows (12,000 total code points),
and includes surrounding context qualifications. For long opinions (>15,000 characters),
structural candidate diversity across early, middle, and late sections ensures
representative opinion coverage (`METHOD_VERSION = "lexical-qualified-multi-passage-v3"`).
Clipped windows are disclosed and cannot establish a supported or misrepresented verdict.

User-corrected claim text (T206) is used for passage selection and model review
when present; original `Claim.text` still has to match the filing offsets.

The registered `propositions_stage` consumes detached, analysis-owned prior claims,
citations, claim-authority links and authorities. It emits new findings/evidence and
allowlisted link updates through the contained worker. No usable source produces
`insufficient_source`; missing credentials or invalid inference produce `unavailable`.
Partial checks retain earlier results and unavailable coverage. Per-stage link limits
are disclosed rather than hiding omitted checks.

Strict output validation checks evidence IDs, absolute original-source spans and
verbatim excerpts. Model and prompt versions, source retrieval/hash metadata, context
clipping and uncalibrated confidence levels accompany evidence. Findings explicitly
describe a review flag and recommend human review. Numerical confidence is withheld.

Version 3 resolves model-selected immutable evidence-unit IDs to exact source
excerpts and original spans. Units partition the complete selected context into
contiguous pieces of at most 600 characters; neighboring qualifications are kept.
Unknown/duplicate IDs are rejected. No model-supplied excerpt or offset is trusted.
Retrieval v2 expands a small explicit set of related educational/segregation/equality
forms and prefers explicit holding language among matching paragraphs. These are
retrieval heuristics; negation and original source text are preserved. They do not
establish support or authority hierarchy. Both cached Brown conclusions are selected
without expected-span hints. Live v1/v2 copying failed; the final two v3 live calls matched the supported and
reversed Brown controls with exact bound evidence. This small control does not
establish broader legal accuracy.
See [[docs/research/Grounded proposition live acceptance - 2026-10-10]].

Focused offline tests use synthetic source text and HTTPX MockTransport. Actual
semantic accuracy, broader adversarial resilience and hosted acceptance remain
release gates; exact-excerpt validation proves quotation presence, not legal support.
Related: [[apps/api/src/filingguard/integrations/llm/README]], [[TODO]],
[[FilingGuard_AI_SRS]],
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]].
