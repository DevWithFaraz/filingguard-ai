---
type: issue
status: resolved-locally
date: 2026-10-07
tags: [issues, frontend, video]
---
# Mobile film description joins words

## Symptom and impact
The 390px homepage screenshot showed “briefto” in the How it works description.
This was a local copy-layout defect discovered after the 22-case browser suite;
no deployed incident is claimed.

## Reproduction and evidence
View the film section below 767px, where CSS hides the description's line break.
Expected: “brief to”. Actual before repair: the adjacent JSX text nodes joined.
The repaired CSS-size screenshot is `.runtime/pipeline-film-mobile.png`.

## Cause
`PipelineWalkthrough.tsx` had `brief<br />to` with no whitespace, while mobile
CSS applied `display:none` to the break. The line break supplied desktop visual
separation but no mobile space.

## Fix and regression check
Add explicit whitespace before the break. The existing layout/rendition test
passes 2/2 after the repair, and the 390px screenshot reads “brief to”. Final
web typecheck/lint/build pass. Playback policy and media did not change.

## Related
[[apps/web/src/features/home/README]] | [[TODO|D006]] |
[[docs/sessions/2026-10-07 - Pipeline film visual revision]]

[[docs/issues/Index]]
