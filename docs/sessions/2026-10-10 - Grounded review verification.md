---
type: session
status: verified-local
date: 2026-10-10
tags: [sessions, grounding, acceptance]
---
# Grounded review verification

## Task and scope
User authorized multiple agents for T037 onward: claims, bounded grounded review,
quote forensics, results/score/graph/export, integrated acceptance and hosted checks.
Work began October 8 and resumed October 10. Existing no-commit/push and free-tier
constraints remain; no public intake or hosted configuration was enabled.

## Changes
Traceable heuristic claims preserve exact original Unicode spans and citation
links. Explicit source verification retains typed receipts and mixed-result
coverage through the contained worker. Every filing-derived model request field
uses complete-snapshot privacy masking before selection. Sources are bounded
lexical windows with qualifications, immutable hashes and disclosed limitations.

Grounded review v3 asks the model to choose precomputed source-unit IDs; local
code binds exact excerpts/offsets. Invented/duplicate IDs, invalid schema/refusal,
missing evidence and clipped favorable verdicts fail closed. Actual model/prompt/
method versions and uncalibrated confidence are saved with transactional link
updates. Quote extraction/comparison preserves exact/normalized/fuzzy outcomes,
original locations and source evidence; similarity does not establish meaning.

Private results/evidence/graph/report routes reuse owner/expiry protection.
Provisional overall/category scores expose deductions and incomplete coverage.
Filters and finding detail show masked excerpts, source/hash/time and metadata.
Bounded React Flow and its complete keyboard list derive from stored relations.
Markdown/HTML exports reuse stored classifications and escape untrusted HTML.
Source/model flags and public intake default off. Canonical setup is [[README]].

## Verification
Full backend: **671 passed, two host-dependent skips**, 673 collected, no failures/
errors, 144.54 seconds. Installed Python pytest -q with
--basetemp=.runtime/final-suite --junitxml=.runtime/final-suite.xml in apps/api.
Windows escalation was required for TestClient socketpair startup. Skips: host
cannot create symlinks; Windows chmod does not verify POSIX privacy. Warnings:
Starlette HTTPX deprecation and SQLite datetime adapter deprecation. Ruff over
src/tests/scripts passes. Nine added relation-tamper controls are included.

Frontend: **30 tests passed**, full lint, TypeScript, generated OpenAPI/client
contracts and production build passed. Build reports large JS chunks. Initial
and enhanced desktop/mobile local results journeys pass masked evidence, two
findings, keyboard controls, saved category/graph agreement, authenticated exports,
owner isolation and deletion. Screenshots inspected; no horizontal overflow.
Final browser verification: results desktop/mobile **2/2 passed** in 35.4 seconds;
intake/shell **10/10 passed** in a separate fresh preview in one minute, with no
failures/skips/retries. The combined run passed 11/12 and hit the intended shared
IP quota of five session issuances per minute; the guard was preserved and the
groups rerun separately. See [[tests/e2e/README]] for reproducible commands.
Four inspected screenshots are retained locally under
`.runtime/review-ui-2026-10-10`. Physical-device and full screen-reader testing
remain unverified. The isolated intake preview explicitly disables both provider
stages even when ambient environment flags enable them.
Final documentation checks: `git diff --check` passes; 161 visible Markdown files
contain 1,029 wikilink file targets with no missing files. This audit validates
file destinations, not heading anchors or external URLs.

Two genuine Groq 120B v3 calls over hash-validated cached Brown public sources
returned expected supported/misrepresented controls with two opinion evidence
records each, 2.765 seconds total. Seven actual calls across v1/v2 diagnostics and
v3; no retries, paid fallback or raw response/credential retention. These controls
are AI-reviewed synthetic filings, not an expert legal benchmark. See
[[docs/research/Grounded proposition live acceptance - 2026-10-10]].

Read-only hosted checks October 10: API health 200 with exact frontend CORS;
/capabilities 404; frontend /activity and /settings 200. Direct Neon read-only
connectivity passed PostgreSQL 17.11 with client TLS. This verifies connectivity/
liveness only; the hosted API is the older health shell. No migration/deployment
or remote data/configuration write occurred.

## Issues and limits
BUG-012 partial citation validation/coverage, BUG-013 model arithmetic/copying and
BUG-014 document/source authority validation are resolved locally with regression
controls. Initial full regression found legitimate document evidence was discarded
when required to carry a source authority; the fixed full rerun passes. Source
opinion evidence retains strict authority/hash/span validation.

Full curated twelve-step SRS 18.2 acceptance, maximum-input/20-page performance,
contrast/assistive-technology audit and broader expert legal QA remain separate.
Local deterministic browser timing and two model calls do not establish T055.
Hosted schema/readiness, POSIX containment/private storage, session isolation,
retention/deletion and fresh intake-to-export remain T057 release gates. The next
product acceptance task is T052, including the still-open T016 cached/live replay
boundary. Do not claim the local synthetic provider matrix is that acceptance.

## Related
[[TODO]] | [[docs/decisions/ADR-011 - Grounded review and saved result boundaries]]
[[docs/issues/BUG-012 - Citation verification output conflicts with worker validation]]
[[docs/issues/BUG-013 - Model evidence offset arithmetic rejected grounded output]]
[[docs/issues/BUG-014 - Filing evidence incorrectly required source authority]]
[[apps/api/src/filingguard/modules/analyses/README]]
[[apps/api/src/filingguard/modules/propositions/README]]
[[apps/api/src/filingguard/modules/quotes/README]]
[[apps/api/src/filingguard/modules/reports/README]]
[[docs/delivery/Deployment guide]] | [[docs/sessions/Index]]
