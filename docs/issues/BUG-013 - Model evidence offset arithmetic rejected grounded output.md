---
type: issue
status: resolved
date: 2026-10-10
tags: [issues, grounding, evidence]
---
# Model evidence offset arithmetic rejected grounded output

## Symptom, reproduction and evidence
Initial two genuine Groq 120B fixture calls returned unavailable after strict
validation. October 10 one-call diagnostic identified `evidence_excerpt_mismatch`:
model-generated absolute offsets did not select the returned source excerpt.
No supported/misrepresented result was persisted, and no raw response or key was
retained. Deliberate reproduction uses `scripts/verify_grounded_review.py --live`
from apps/api over hash-validated cached Brown public source controls, with at
most two free-tier requests, no retries and no alternative paid model.

## Cause and fix
The v1 wire schema required model arithmetic for immutable source positions.
The strict substring check correctly rejected incorrect offsets. The v2 schema
instead requests supplied passage ID plus exact excerpt; local code requires a
unique verbatim passage match and calculates the original source span. Invented
IDs, absent/ambiguous excerpts and invalid substantive evidence still fail closed.
Prompt/method versions change with this behavior. Offline regressions and the
capped real fixture repeat are in progress; authored code alone is not resolution.

## Related

Resolved October 10 with v3 immutable evidence IDs. Models choose only precomputed
source-unit IDs; application code binds original excerpts/spans/hashes without model
copying or arithmetic. Fifty-two focused tests and Ruff pass. The final two genuine
Groq calls yielded expected supported/misrepresented controls with two exact source
evidence records each, 2.765 seconds total and no rejections. All seven calls across
diagnostics and versions are accounted for; no retries or fallback. See
[[docs/research/Grounded proposition live acceptance - 2026-10-10]]. Broader legal QA
and hosted acceptance remain separate gates.
[[TODO]] (T039–T041) | [[apps/api/src/filingguard/integrations/llm/README]]
[[apps/api/src/filingguard/modules/propositions/README]]
[[docs/sessions/2026-10-10 - Grounded review verification]] | [[docs/issues/Index]]
