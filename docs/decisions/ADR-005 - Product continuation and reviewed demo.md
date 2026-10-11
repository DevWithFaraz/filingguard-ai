---
type: decision
status: accepted
date: 2026-09-28
tags: [product, demo, provenance]
---
# Product continuation and reviewed demo

Related: [[docs/decisions/Index]], [[TODO]], [[FilingGuard_AI_SRS]],
[[docs/product/Demo fixture review]], [[docs/product/UI direction]].

## Context and decision

User confirmed the hackathon deadline was missed and wants continued product work
without a time constraint. Retain historical delivery evidence but stop applying
submission freezes. P0 is now the core workflow, followed by staged enhancements.
The free-credit budget, stack and anonymous-private-session decision remain unchanged.
Do not enable real confidential-client use before security/provider-policy and legal
quality gates, even though those tasks originally appeared under P2.

T015's delegated AI review supports controlled demo development, not human validation.
T016 adds a separate read-only preview adapter with explicit mode, server-owned
fixture identity, hash-bound receipt and exact evidence checks. It exposes expected
scenarios and all five conditional notes. No LLM/provider calls or analysis rows are
created. Court-rule scenarios remain planned/unavailable until their profile exists.
The old human-reviewed result-replay gate is retained; silently changing its meaning
would falsely confer human approval. Actual engine execution belongs to later tasks.

## Consequences

Reset unmounts sample state and removes its transient query cache; it does not claim
server deletion of a private analysis. The API has only liveness and public sample
GET routes. Live submission stays disabled until ownership/admission/lifecycle
protection is connected. The review receipt is repository-owned approval metadata,
not a cryptographic signature or user-provided approval. Rebuilding/changing material
invalidates its byte hashes and requires another relevant review.

The resource path currently assumes a monorepo editable install, as on Render.
Standalone wheel/container packaging must bundle or explicitly locate these
resources before deployment; missing material fails closed with a safe 503.
