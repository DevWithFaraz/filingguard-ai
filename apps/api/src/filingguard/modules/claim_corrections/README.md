# claim_corrections

Priority: P2. Task: T206 in the root TODO.md.

Let owners correct extracted claim text without rewriting original extraction.

Owner-scoped correction requests in; persisted history, stale proposition links,
and results fields out. Never mutate `Claim.text` or document offsets.

`POST /api/v1/analyses/{analysis_id}/claims/{claim_id}/corrections` appends a
JSON history entry on the existing claim. Original extraction stays in `text`.
Related `ClaimAuthorityLink` rows reset to `not_run` with an explicit stale
explanation. Other review stages and existing proposition findings are kept.

In-place proposition-only re-run is not implemented: the orchestrator only queues
a first full review, and `POST /analyses/{id}/rerun` clones a new analysis that
re-extracts claims without this correction. Hosted Neon is not upgraded; local
head is `0006_claim_corrections`.

Related: [[TODO]] (T206), [[FilingGuard_AI_SRS#9.4 Claim Extraction]],
[[apps/api/src/filingguard/modules/claims/README]],
[[apps/api/src/filingguard/modules/propositions/README]].
