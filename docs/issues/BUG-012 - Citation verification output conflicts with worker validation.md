---
type: issue
status: resolved
date: 2026-10-08
tags: [issues, citations, workers, coverage]
---
# Citation verification output conflicts with worker validation

## Symptom and impact

The T035 `verified_citation_stage` component can construct results that the
contained worker's `StageResult.validate` rejects. Normal reviews still register
the T032 extraction-only runner, so this is a reproduced integration blocker,
not evidence of a failed deployed citation review. Enabling the new runner
directly would lose usable citation results on ordinary partial/outage cases.

## Reproduction

October 8, local Python virtualenv, installed locked dependencies. Construct an
`Analysis` from `extract_text`, with matching `ReviewSegment` records. Pass an
explicit synthetic token and `httpx.MockTransport` adapter to
`verified_citation_stage`; call `result.validate(StageName.CITATIONS)`.
No live provider requests or environment credentials are needed.

Observed probes:

- `See 347 U.S. 483.` with a single verified fake authority: completed,
  eligible/evaluated 1/1, two records; validation accepts the control.
- The same citation with fake HTTP 401: partial with an unavailable Citation;
  validation rejects it with `Partial citation extraction cannot assert source verdicts`.
- `See 347 U.S. 483 and 376 U.S. 254.` with the first verified and second
  unavailable: coverage says evaluated 0/unavailable 2 despite a verified row.
  Authority plus two citations also fails the dedicated partial-output check.
- `See 347 U.S. 483. Id. at 490.`: verified full citation plus unrun short
  reference fails the partial-output check; coverage again reports zero evaluated.
- 200 repeated verified occurrences: 200 Citation rows plus one Authority row
  exceed the worker's 200-record cap; `Stage record limit exceeded`.
- 201 repeated detected occurrences: only 200 retained; constructing completed
  coverage with eligible 201/evaluated 200 fails `Coverage` validation.

Expected: explicit incomplete coverage preserves independently obtained results,
original occurrences and reasons through worker validation and atomic persistence.
Bounds must remain enforced and truncation must remain explicit.

## Evidence and confirmed cause

`apps/api/src/filingguard/modules/citations/runner.py` counts all non-not_run
statuses as evaluated for its branch decision, but reports zero evaluated and
all detected occurrences unavailable in its partial branch. It includes both
Authority and Citation rows in one result.

`apps/api/src/filingguard/modules/analyses/execution.py` deliberately allows
only extraction-only, unverified Citation rows in partial citation output, and
caps every stage at 200 total records. `Coverage` requires a full partition of
eligible counts, while completed stages cannot be truncated.

Existing adapter/service and persistence/API tests do not cover these combined
conditions. The integration deduplication tests invoke the service and
`repo.stage_update` directly, bypassing contained runner execution.
All 65 focused existing tests passed in this review; that does not negate the
new reproduction.

The ignored local probe is `.runtime/citation-review-audit.py`. Its invocation
was `& './apps/api/.venv/Scripts/python.exe' .runtime/citation-review-audit.py`.
The synthetic inputs/results above provide the durable reproduction if that
local script is removed. See the linked session for command outcomes.

## Fix and regression check

Resolved locally October 8–10: narrowly typed partial source results preserve
verified/unavailable outcomes, original spans and accurate coverage. Parent
validation requires receipts, exact locations, owner-scoped relations and bounded
entity/snapshot output. Normal source registration and credential delivery are
explicit opt-ins. Nine verified-stage controls, 19 citation regressions, three
contained claim/source cases and source/query-budget controls passed, including
mixed failures, short references and 200/201 occurrence boundaries.
See [[docs/sessions/2026-10-10 - Grounded review verification]]. No hosted
verification is claimed. Original October 8 recommendation follows:

No runtime fix made in this analysis. Under T036, define a narrowly validated
partial verification result path, accurate coverage accounting and bounded
authority/occurrence output. Preserve owner/provenance/span validation rather
than relaxing the general stage boundary. Verify actual worker execution,
parent persistence, mixed outages/references and boundary/truncation cases with
fake providers before activating normal source verification.

## Related

[[TODO]] (T024, T032-T036),
[[FilingGuard_AI_SRS#9.3 Citation Verification]],
[[apps/api/src/filingguard/modules/citations/README]],
[[apps/api/src/filingguard/modules/analyses/README]],
[[apps/api/src/filingguard/integrations/courtlistener/README]],
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]],
[[docs/decisions/ADR-009 - Local citation occurrences before source verification]],
[[docs/sessions/2026-10-08 - Codebase and vault analysis]].

[[docs/issues/Index]]
