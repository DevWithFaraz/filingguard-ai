---
type: session
status: completed
date: 2026-10-10
tags: [sessions, design, frontend]
---
# Document workspace redesign

## Task and scope

[[TODO]] D007, first complete page for user review: `/analyses/:id`.
The user explicitly invoked the installed apple-design skill and requested one
page before proceeding to others. Solo work; homepage preserved; no deployment,
commit, push or model calls.

## Changes

PreparedView has a scoped shell with glass home/activity/settings navigation,
homepage logo/background/display font and a purple hero. Three-step wayfinding
and a server-status-aware next-action card cover preparation, running and terminal
states. Document/check anchors, inspectable text, keyboard details/findings,
retention summary and deletion/reset remain available. Reduced-motion disables
arrival/press animations; reduced transparency gives a solid toolbar. Masking,
source limitations, extraction warnings and provisional score remain explicit.
The summary now follows polled status instead of stale preparation status.
Remaining pages retain their earlier UI; aesthetic acceptance is pending.

## Verification

- Typecheck and lint pass; 30 frontend tests pass; production build passes
  (existing large-chunk warning remains). Sandbox Vite realpath EPERM required
  an approved local rerun outside the sandbox.
- Desktop/mobile curated journeys pass 2/2 against disposable preview servers:
  step results gating, keyboard detail/findings expansion, Activity return,
  masked findings, normal/reduced-motion styles, no horizontal overflow,
  actual review/results/evidence/report export/reset. Screenshot evidence:
  `.runtime/playwright-curated/*/prepared-page.png` and `prepared-completed.png`.
- Text/PDF journey passes on desktop and mobile: reload, outsider denial,
  masked findings, paragraph spans, Activity summaries, delete, PDF extraction
  details, malformed PDF fallback and demo preparation. The first mobile attempt
  reached the test's old ten-second wait while the real quote worker was still
  running; a bounded thirty-second wait passed on rerun in 13.6 seconds total.
- Desktop/mobile preparation and desktop terminal screenshots inspected. Final
  copy-only CSS adjustment restores ordinary casing for stage reasons/findings.
- Local frontend 5174 and private API 8001 return HTTP 200; diff whitespace check
  passes. No backend behavior changes or backend suite rerun. No full contrast,
  screen-reader, physical-device, hosted or performance acceptance claim.

## Blockers and next step

First page is ready for user visual review. Continue D007 remaining non-home
pages after feedback on this direction. T052 semantic acceptance remains at
its previously recorded free-tier gate, unrelated to this UI change.
Local review: open `http://127.0.0.1:5174/`, select Demo, then Prepare document.
Private analysis URLs depend on the originating tab's bearer and are not share links.

## Related

[[docs/sessions/Index]] | [[TODO]] | [[docs/product/UI direction]] |
[[docs/feedback/FB-012 - Match workflow pages to homepage theme]] |
[[apps/web/src/features/intake/README]] | [[apps/web/src/app/README]] |
[[docs/decisions/ADR-007 - Private preparation boundary]]
