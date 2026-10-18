---
type: session
status: verified
date: 2026-10-11
tags: [sessions, deployment, acceptance, privacy]
---
# Hosted synthetic acceptance

## Task and scope

[[TODO]] T057. User enabled intake and redeployed during the synthetic acceptance
window; both external provider flags remain false. Services are user-reported on
release `5b37993`. Solo work; actual hosted HTTP/DB controls use only newly created
test sessions and reviewed synthetic public fixtures. No provider requests.

## Verified workflow

Read-only probe at 17:46 UTC returns readiness 200 with all six checks true;
health/capabilities, direct SPA routes and exact/forbidden-origin CORS pass.
Capabilities legal_analysis_enabled=false verifies external analysis is disabled.

Hosted real contained cached-demo and PDF journeys pass. Cached demo review,
results/evidence/graph and exports take 39.203 seconds, with three source authorities,
exact/close quotations, explicit cached-public provenance and partial citation
coverage. PDF review-to-export takes 37.047 seconds; source-unavailable quotes,
unknown court profile and disabled propositions remain explicit. Both reviews
correctly finish partial, with local privacy completed and no model verdicts.

Results/evidence and Markdown/HTML exports mask the synthetic SSN. Saved graphs,
five score categories, no-store and HTML sandbox headers pass. A second session
cannot read documents/status/findings/citations/results/graphs/reports/evidence or
run/rerun/delete the first session's analyses: 404 throughout. Unauthenticated
requests return 401; forbidden origin returns 403. Second-owner Activity stays
empty. Both test analyses are deleted, and their saved views/reports return 404.
Sanitized receipt: ignored `.runtime/hosted-acceptance-receipt.json`.

## Controlled expiry

A separate newly created synthetic PDF/session has a declared expiry within 55
minutes. Only its own owner/analysis timestamps are advanced to expired using
guarded database updates. Expired-session API access returns 401; the existing
hosted scheduled sweep removes its analysis, all analysis-owned children and the
session within 21.969 seconds. Readiness/cleanup remain healthy. Receipt:
ignored `.runtime/hosted-expiry-receipt.json`. This is accelerated expiry/sweep
verification, not natural 55-minute observation, secure erasure or direct Render
filesystem inspection. No real user timestamps, TTL configuration or schema change.

## Restart verification

Prepare a new synthetic PDF with real completed partial review, recording canonical
saved result/graph digests. Prepare a separate synthetic text row and queue its
citation metadata through the existing owner-scoped repository method without
scheduling an actual worker. This tests controlled queued-state recovery, not
termination of an in-flight worker. Both records were retained for the restart check.

After the user reported the API redeployment Live, ran
`node scripts/api.mjs run python ../../.runtime/hosted-restart-check.py verify`.
At 18:07 UTC all 14 controls pass: readiness, external analysis disabled, canonical
saved result/graph digests unchanged, Markdown/HTML export masking, queued analysis
and citation stage recovered as interrupted, second-owner denial, and deletion/
subsequent 404 for both fixtures. The private token state file is removed after
successful cleanup. Sanitized receipt: ignored `.runtime/hosted-restart-receipt.json`.
Verification occurred before the test session's 18:50 UTC expiry.

T057 passes at synthetic hosted acceptance scope. Genuine hosted source/model, forced
provider outage and cached/live rehearsal remain T058. Broad expert legal QA and
physical assistive-device checks remain separate; no confidential filing release.
No product code, provider settings or production limits changed in this work.

Next task: T058. Prepare the genuine hosted cached/live and forced dependency-failure
rehearsal within the existing free-credit limits. Neither external provider flag
was enabled here. No new application regression suite was run for these evidence-only
documentation changes; the hosted verifier is the check for this restart.

## Related

[[docs/sessions/Index]], [[docs/sessions/2026-10-11 - Closed intake hosted checks]],
[[docs/delivery/Deployment guide]], [[apps/api/src/filingguard/modules/analyses/README]],
[[apps/api/src/filingguard/integrations/storage/README]],
[[apps/api/src/filingguard/modules/reports/README]],
[[docs/decisions/ADR-006 - Retryable private lifecycle cleanup]].
