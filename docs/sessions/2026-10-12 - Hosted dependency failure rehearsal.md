---
type: session
status: verified
date: 2026-10-12
tags: [sessions, deployment, acceptance, providers]
---
# Hosted dependency failure rehearsal

[[TODO]] T058 continues after the normal live/cached checks. User confirms Live
after applying the requested invalid non-secret CourtListener test token and
disabling semantic review, retaining source verification/intake and other settings.
Solo work, synthetic public inputs, existing free services. No product code change.

## Verified

Ran `node scripts/api.mjs run python ../../.runtime/hosted-provider-rehearsal.py source-failure`.
All 46 named checks pass at 01:09–01:10 Asia/Karachi on October 12
(20:09–20:10 UTC October 11). Readiness stays 200; this confirms configuration
presence, not usable provider authentication.

Live Brown review takes 41.219 seconds. Citations are unavailable with the
allowlisted `http_failure` reason and no authority attached. Claim support stays
not_run, propositions unavailable, model evidence absent; no failure becomes a
not-found or favorable legal verdict. Privacy completes; masked Markdown/HTML
exports retain explicit live mode and second-owner results access returns 404.

Explicit cached demo review takes 37.750 seconds. Three cached authorities remain
available, quote checks retain exact/close outcomes, privacy/court checks complete,
and both masked reports explicitly identify cached_public sources. Semantic review
is unavailable and there is no model evidence because it was deliberately disabled.
Second-owner access fails. Both analyses finish partial, preserving unavailable
coverage. Both fixtures are deleted and their saved results return 404.

Sanitized receipt: ignored `.runtime/hosted-provider-source-failure-receipt.json`.
This is controlled authentication-failure rehearsal, not an actual provider network
outage or evidence of provider health. No Groq inference request was intended or
model evidence produced. Tokens/raw provider bodies were not printed or saved in
vault notes. Full application regression was not repeated for evidence-only docs.

## Restored configuration verified

The user confirms Live after restoring the real token and semantic flag. Ran
`node scripts/api.mjs run python ../../.runtime/hosted-provider-rehearsal.py restore`.
All 25 named checks pass at 01:16–01:17 Asia/Karachi on October 12
(20:16–20:17 UTC October 11). Live Brown takes 42.937 seconds: citation and
proposition stages complete, live CourtListener source hash verified, supported
verdict with three fresh bound evidence records from `openai/gpt-oss-120b`, masked
Markdown/HTML exports, explicit live source labeling and second-owner denial.
Overall partial status accurately reflects the unavailable real court profile.
The test analysis is deleted and its saved results return 404. Sanitized receipt:
ignored `.runtime/hosted-provider-restore-receipt.json`.

The post-restoration public probe passes readiness 200 with all six checks true,
health/capabilities, Activity/settings routes and exact/forbidden-origin CORS.
No settings or secrets were changed by the verifier. One fresh synthetic analysis
was used; there was no cached-demo rerun, paid fallback or schema mutation.

## Next and limits

T058 passes at synthetic hosted rehearsal scope across normal/failure/restoration
phases, with prior T057 restart evidence. Source/semantic flags and intake remain
enabled as confirmed by the user; the temporary invalid-token setup is retired.
Next ordered task is T060: a two-to-three-minute walkthrough matching released
behavior, with truthful unavailable coverage and AI limitations. T061 is retired;
T062 final release record/tag/URLs remains separate. No real-case expert legal QA,
physical assistive-device acceptance or physical storage erasure is inferred.
Documentation checks pass; no product code changed or full regression repeated.
Release evidence documentation remains local, uncommitted/unpublished in this
session; the deployed product revision is user-reported `5b37993`.

Normal phase evidence: [[docs/sessions/2026-10-11 - Hosted provider rehearsal preparation]].
Restart evidence: [[docs/sessions/2026-10-11 - Hosted synthetic acceptance]].
Related: [[docs/sessions/Index]], [[docs/delivery/Deployment guide]],
[[apps/api/src/filingguard/modules/citations/README]],
[[apps/api/src/filingguard/modules/analyses/README]],
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]].
