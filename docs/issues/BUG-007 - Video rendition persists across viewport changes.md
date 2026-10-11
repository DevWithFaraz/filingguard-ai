---
type: issue
status: resolved-locally
date: 2026-10-06
tags: [issues, frontend, video]
---
# Video rendition persists across viewport changes

## Symptom and impact
Source inspection found that the first embed loaded media-query sources once
and did not reload across the 767px breakpoint. A desktop video already loaded
before narrowing the viewport could keep its smaller evidence text on a phone
layout. This is a local D006 development issue; no deployed incident is claimed.

## Reproduction
Load desktop film above 767px, pause within a beat, then narrow below 768px.
Expected: load the larger-text mobile rendition and preserve position/pause.
The original component had no breakpoint listener or media reload for this case.
The original focused test resized only within each rendition's size range.

## Evidence and cause
Confirmed by inspection of the original `PipelineWalkthrough` effects and source
selection: responsive source selection happens during media loading; the effect
depended only on the first media request. The regression against finished assets
is now verified: `tests/e2e/pipeline-film.spec.ts` crosses the breakpoint
in both directions and checks dimensions, retained time and paused state.

## Fix and regression check
An explicit media-query listener updates the selected pair of sources, reloads
the element, and restores position after metadata. A pending restore position is
retained across rapid switches; playback policy still owns play/pause intent.
The October 7 installed-Chrome desktop/mobile tests cross the 767px breakpoint in
both directions and verify decoded dimensions, retained position and paused state.
The22-case suite passes; the existing layout/rendition case passes 2/2 again after
the unrelated mobile description whitespace repair. Resolved locally; physical
devices remain outside this regression result. Evidence:
[[docs/sessions/2026-10-07 - Pipeline film visual revision]].

## Related
[[apps/web/src/features/home/README]] | [[TODO|D006]] |
[[docs/sessions/2026-10-06 - Programmatic video production]]

[[docs/issues/Index]]
