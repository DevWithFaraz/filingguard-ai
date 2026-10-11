---
type: issue
status: resolved-locally
date: 2026-10-07
tags: [issues, tests, frontend, video]
---
# Media failure test blocks Vite imports

## Symptom and impact
The D006 failure/retry browser test aborted a Vite media import wrapper before
the homepage mounted. It could not exercise the player's fallback state. This
was a test interception fault, rather than evidence of a broken player.

## Reproduction and evidence
Run the failure/retry case in `tests/e2e/pipeline-film.spec.ts` against Vite with
a URL-only route abort matching `pipeline-film-*.mp4/webm`. The expression also
matches Vite's `?import` JavaScript resource. The interrupted audit had 7 failures,
including separate intake failures caused by preview-server ownership cleanup.
The corrected clean suite passes 22/22.

## Cause
The mock matched a URL without checking request resource type. This blocked both
media requests and the modules that provide their URLs to React.

## Fix and regression check
Abort only requests whose resource type is `media`; continue matching import
wrappers. A fresh CI=1 run owns its preview servers rather than reusing the
interrupted run's servers. Desktop/mobile failure, poster and retry cases pass
within the 22/22 suite. No playback-policy or media repair was needed.

## Related
[[apps/web/src/features/home/README]] | [[TODO|D006]] |
[[docs/sessions/2026-10-07 - Pipeline film visual revision]]

[[docs/issues/Index]]
