---
type: session
status: locally-verified-hosted-blocked
date: 2026-10-11
tags: [sessions, acceptance]
---
# Accessibility performance and release gates

The user authorized T050, T055, T052, T056 and T057 work, with solo execution and
free credits only. No subagents, paid fallback, commit/push or hosted mutation
occurred. This handoff records local verification separately from hosted release.

T050: desktop/mobile sequential keyboard flow and WCAG-tagged axe scans pass 2/2.
Prepared text scrolling is now keyboard-accessible; small text contrast failures
were corrected while preserving homepage design. See
[[docs/issues/BUG-019 - Low contrast labels and inaccessible document scroll]].
Role/live-region checks cover accessible semantics; no physical screen-reader
certification or NVDA/VoiceOver session is claimed.

T055: the real Windows extraction worker accepts a 20-page, exactly 10 MiB trusted
fixture in 1.859 seconds, preserving 47,459 extracted characters and 20 paragraphs.
The 100,000-character / 2,000-paragraph text fixture extracts in 0.031 seconds.
21 pages, 10 MiB + 1 byte, 100,001 characters and 2,001 paragraphs reject with
the intended safe codes. Reproduce using `scripts/verify_input_limits.py` through
the API runner. Sanitized receipt: `.runtime/input-limit-verification.json`.
Six real model-disabled desktop/mobile reviews finish in 12.946–14.086 seconds;
initial progress 208–318 ms; completed dashboard 472–783 ms. The maximum-text
browser flow takes 18.795 seconds / 1,054 ms / 544 ms respectively. The performance
suite passes 3 tests with one deliberately skipped duplicate mobile maximum-input
case. These are Windows/Chromium measurements without CPU/network shaping,
physical-device or hosted cold-start claims. JSON receipt:
`.runtime/workflow-performance-results.json`.

T052: the final opted-in genuine-model browser journey passes all twelve SRS 18.2
controls, including independent supported Brown/Miranda/Obergefell and reversed
Brown misrepresented, citation/quote/privacy/rule checks, score, graph, exact bound
evidence, Markdown export and reset/owner unavailability. The invented authority
is insufficient_source. Forced outage expectations are excluded from the normal
fixture comparison and verified by separate contained-worker controls.

Selected model remains openai/gpt-oss-120b with free credits and zero model retries.
Two same-authority Brown propositions share overlapping source characters in one
strictly validated request; Miranda/Obergefell remain separate. All source context
and qualifications are preserved; no expected status is an inference input. The
three actual requests consume 10,743 prompt and 927 completion tokens (shared batch
counted once). Numerical quota headers show an 8,000 TPM bucket. The final journey
measures 52.803 seconds analysis, 187 ms progress and 641 ms dashboard, with a
deliberately enabled 60-second stage budget inside the 90-second overall limit.
Production's default stage remains 30; the prepared Blueprint specifies 60.
Earlier unbatched runs throttled and are historical failures, not passing evidence.
Earlier batch browser runs returned correct normal verdicts but failed test
assumptions about forced-outage expectations/evidence-card count; the final
corrected journey completes export/reset. No additional model calls are
needed. Cached sources and AI-reviewed expectations remain explicit; expert legal
quality is unverified. Sanitized final receipts are
`.runtime/curated-live-final-2026-10-11.json` and
`.runtime/live-tokens-final-2026-10-11.json`. See
[[docs/decisions/ADR-013 - Shared authority model requests and bounded quota admission]]
and [[docs/issues/BUG-017 - Free-tier throttling blocks curated semantic acceptance]].

Outgoing-payload verification exposed punctuation-adjacent email masking failure;
the original full-filing detector now masks sentence-final addresses and still
preserves offsets before clipping. Synthetic controls only; no observed private
disclosure. [[docs/issues/BUG-020 - Email before sentence punctuation escapes masking]].

Release preparation: added `/api/v1/ready` separate from liveness. It fails closed
for disabled intake, missing/current-schema mismatch, unhealthy cleanup and absent
credentials for enabled providers. It makes no provider requests or migrations.
Focused integration checks pass 2/2. A read-only hosted probe confirms health 200,
exact allowed/forbidden-origin behavior and Activity/settings SPA 200, but readiness
and capabilities both 404. T057 remains open. No hosting credentials or browser
dashboard session are available; GitHub CLI is unavailable. Hosted migration,
POSIX permissions/resource limits, fresh session-isolated intake-to-export,
retention/deletion and restart recovery have not run. The concrete procedure and
closed-by-default Blueprint are prepared in [[docs/delivery/Deployment guide]].

Dependency audit identified source-map-js GHSA-68fv-2mgg-jv7q in the previous
lockfile. A compatible patch update completed; npm audit now reports zero
production vulnerabilities. Production build, API Ruff, frontend lint/typecheck
and 30 frontend tests pass. Vite still warns about two JavaScript chunks above
500 kB; this is a nonblocking bundle-size limitation, with homepage scenes already
lazy-loaded. Physical-device/cold-start measurements remain separate.

The first full backend regression ran 714 controls: 709 passed, two host skips and
three failures. Two failures came from my temporary documentation edit inside the
hash-locked demo manifest; the artifact was restored byte-for-byte to the reviewed
hash, and current wording moved to its README. The remaining failure was an older
route-contract expectation missing the new /ready endpoint. All 76 controls in the
complete affected suites now pass: intake, orchestrator, contracts, curated source
integrity, demo preview and readiness. Combined with the unaffected full-run
controls, all 712 non-skipped backend controls are verified after correction;
no second full 714-case run is claimed. The integrity checks remain unchanged.
Windows skips cover unavailable
symlink creation and POSIX chmod semantics. Sandbox EPERM prevented an initial
Vite test setup; the same command with required host access passes all 30 tests.

Browser regression: public and saved-results desktop/mobile suites pass 2/2 each;
sequential keyboard/axe accessibility passes 2/2 again with retained JSON receipts.
An intake mobile run correctly rejected the temporarily edited fixture; the
corrected isolated desktop/mobile rerun passes 2/2. Offline curated rerun also
passes 2/2. In total, 11 browser controls pass across isolated public, intake,
results, accessibility, offline curated and genuine live curated runs, plus the
separately measured performance suite's three passes/one deliberate skip.

Source provenance: fixture tests cover original/raw source hashes for three public
opinions, retained retrieval/type/conversion/attribution and exact Unicode spans
for all 18 expectations. The offline grounded verifier separately confirms both
Brown reference passages are selected without expected-span hints, no truncation
and zero provider attempts. Human/expert semantic review remains pending.
Vault link validation passes: 176 Markdown documents, 1,181 wikilinks, no missing
targets. Secrets, raw payloads, runtime receipts and environments remain ignored.

Requirement coverage: SRS 18.2 steps 1–12 map to the genuine curated journey;
FR-300–304 / AUD-001–004 map to saved-report/evidence/ownership tests; T050 maps to
keyboard/axe and responsive motion checks; T055 maps to scoped timing/max-input
controls. DEP-001 shell availability is observed, but DEP-002 working hosted demo
and the hosted T057 isolation/readiness gates remain unverified. No hosted or
expert-legal acceptance is inferred from local synthetic tests.

T056 is complete locally: frontend build/lint/typecheck/unit tests, backend lint,
all non-skipped backend controls after the targeted correction, browser journeys,
source provenance and scoped requirement review have no blocking failures.
Contract export and generated TypeScript schema were refreshed for readiness.
Final `git diff --check` passes with only line-ending normalization notices.

The user's disposable model-disabled preview was restarted on API 8001 / frontend
5174. HTTP checks return frontend 200, health 200 and readiness 200. These local
ready results do not certify hosted dependencies or enable external model calls.

Next: make T057 concrete using the prepared rollout once hosting access and the
reviewed publication path are available. Keep
intake/providers closed until hosted storage, migrations and containment are verified.

Related: [[TODO]], [[docs/sessions/Index]], [[docs/delivery/Deployment guide]],
[[docs/issues/BUG-017 - Free-tier throttling blocks curated semantic acceptance]].
