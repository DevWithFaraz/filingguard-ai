---
type: session
status: partial-acceptance
date: 2026-10-10
tags: [sessions, demo, acceptance]
---
# Curated demo acceptance

## Scope and changes
User requested starting T052/T016 and explicitly stopped further subagent use.
This work was performed solo. No commit/push, hosted changes or billing changes.

Exact curated-v1 demo runs now adapt three hash-validated cached public opinions
to the real citation engine. Claims, quote comparison, privacy and synthetic rules
compute fresh results; expectations never become cached classifications. Live
mode cannot receive these cached sources, even on provider failure. The legacy
human-reviewed cached-result loader remains distinct and disabled.

Demo court/AI-use controls are selectable. UI/export source mode is explicit;
Reset demo deletes saved private output. Quote-forensics-v2 repairs the explicit
preceding-citation/`The Court stated:` attribution gap with bounded ambiguity
controls. Reports include per-evidence provenance. Semantic opinion evidence
retains cached_public provenance, distinct from fresh model classification.

Preview defaults to disabled providers. `--live-semantic` explicitly opts into
the configured free-credit model with at most five attempts per analysis; source
HTTP is disabled, with no retry or paid fallback. Provider errors expose only
fixed sanitized codes; no raw response, credential or private filing is retained.

## Checks
74 focused API tests passed, followed by 28 checks for the adjusted prior-demo
expectations, outage/cache separation and proposition service. Frontend 30 tests,
TypeScript, lint, generated contracts and build pass; existing large-chunk warning
remains. Initial full backend run: 684 passed, two host skips, one stale prior-demo
assertion failed. The assertion was updated to the actual cached citation/quote
behavior; targeted rerun passes. Final full rerun: **686 passed, two host skips**,
688 collected, zero failures/errors, 170.35 seconds. JUnit receipt:
`apps/api/.runtime/curated-final.xml`. Skips cover unavailable Windows symlink
capability and POSIX chmod verification, not failed application checks.

Final offline curated browser journeys pass desktop/mobile **2/2 in 34.5 seconds**
(13.7/13.4 seconds per journey). They
exercise loading, court/AI choice, run, score/categories, verified and unresolved
citations, exact/altered quotes, privacy/disclosure, graph, two evidence details,
authenticated report and reset/deleted-resource rejection. Semantic review is
disabled in this run, so it establishes eleven SRS 18.2 controls, not all twelve.
Final screenshots were inspected and remain under `.runtime/playwright-curated`;
the assertions confirm no horizontal overflow. No contrast/physical-device/real
screen-reader acceptance is inferred. `git diff --check` passes; vault audit finds
166 visible Markdown files, 1,066 wikilink file targets and no missing files
(file paths only, excluding heading anchors/external URL validation).

Three genuine-model desktop journeys failed the supported/misrepresented pair.
Each was bounded to five attempts, with four source-eligible links in the sample.
The final diagnostic integrated run shows later requests rate_limited. First two
failure codes were not retained and cannot be attributed conclusively. One separate
diagnostic call for the actual extracted reversed Brown claim returned
misrepresented with two evidence records, two selected passages and no clipping.
No automatic retry/paid fallback or CourtListener HTTP call occurred.

## Remaining and next task
T016 source replay is verified locally. T052 remains open at semantic step 7,
tracked in [[docs/issues/BUG-017 - Free-tier throttling blocks curated semantic acceptance]].
Next: bounded free-tier request/input scheduling verification, then the twelve-step
journey. Full contrast/assistive-technology audit, maximum-input/20-page performance,
expert legal QA and hosted release remain unverified. Existing hosted API is still
the older health shell; no migration or deployment was performed.

## Related
[[TODO]] | [[docs/decisions/ADR-012 - Exact sample source replay with fresh findings]]
[[docs/issues/BUG-015 - Explicit court attribution loses quote source]]
[[docs/issues/BUG-016 - Report omits evidence cache provenance]]
[[apps/api/src/filingguard/modules/analyses/README]] | [[tests/e2e/README]]
[[docs/sessions/Index]]
