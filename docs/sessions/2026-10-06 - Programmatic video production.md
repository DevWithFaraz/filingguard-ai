---
type: session
status: paused
date: 2026-10-06
tags: [sessions, frontend, motion, video]
---
# Programmatic video production

## Task and scope
[[TODO|D006]]. The user authorized production with "start now" after choosing
a 26-second widescreen silent loop, rendered MP4/WebM, sharper resolution, the
original PNG, and placement below the hero. No commit, push or deployment.

## Changes
The 810-frame draft was replaced by a 780-frame composition with all nine beats.
Draft layouts, fake percentages and assurance copy were replaced by source-linked
process scenes. Brown's source identity was corrected to cached opinion 105221.
No backend, API, intake or review feature was removed by this film work.

`apps/video` now has registered desktop/mobile compositions, local font loading,
stills/master/encoding/metadata scripts and isolated bundles. Mobile uses larger
comparison text; scaling the desktop composition alone was insufficient at phone
width. Inter and JetBrains Mono binaries and official OFL notices are bundled.
The PNG wordmark is unchanged.

`PipelineWalkthrough` is inserted immediately after the hero. It loads media when
needed, pauses offscreen/hidden, preserves manual pause, supports reduced motion
and retains poster/static stages on failure. Breakpoint changes reload the proper
rendition while retaining playback time and intent. [[docs/issues/BUG-007 - Video rendition persists across viewport changes]].

## Completed export verification
Both masters and all website assets completed before work stopped. The combined
`apps/video/out/media-report.json` passes duration, dimensions, fps, silence and
size budgets. Desktop master: 3840x2160, 26 seconds, 30 fps, 780 frames, no audio,
14,404,255 bytes. Mobile master: 1920x1080, same timing/silence, 3,798,937 bytes.
Website desktop MP4/WebM: 4,571,648 / 3,420,304 bytes; mobile MP4/WebM:
2,272,671 / 2,191,032 bytes. Poster: 1920x1080 WebP, 65,758 bytes.
These files still contain the desktop Authority-card readability problem below.

## Checks and limits
Video and frontend typechecks passed. Desktop key stills and all mobile key
stills rendered and were inspected. Repairs addressed the intake support-label
position, report footer clipping, authority connector rows, graph source/status
detail, mobile quote overflow and mobile graph-box height. Encoded clarity and
motion cannot be established by those stills.

An initial unit-test attempt was blocked by esbuild sandbox path access. The
approved retry launched, but all four Vitest fork workers timed out before any
tests ran during the heavy render. This is not a passing test result. Unit tests
must be rerun with controlled workers after the remaining revision. A later
retry ran 18 API/polling unit tests successfully, while the App suite could not
resolve media imports before exports existed. No complete passing unit run is
claimed. Final video/frontend typechecks and frontend lint passed. Build and
desktop/mobile browser tests have not run for this film.

The first 4K software-rendering run was slow. Same-frame native ANGLE captures
took 6.50s and 4.52s; SwiftShader took 22.07s and 13.61s on frames 336/756.
Both native images were inspected for quote highlights/connectors and PNG edges.
The identified owned render was stopped and restarted with ANGLE/concurrency2;
4K dimensions, PNG capture and CRF16 are retained. This observation is specific
to installed Chrome, Remotion 4.0.529 and this Windows laptop.

## Exact resumption point
After watching the desktop export, the user said the white card in Authority
lookup has text that is too small to see and looks bad. Current cause:
`DocumentText` is authored at 820px and scaled by `w/820` inside a 330px card,
reducing 25px names to about 10px. Source was not changed after this feedback.
[[docs/feedback/FB-010 - Readable authority card in pipeline film]].

The agreed next action is a focused, large citation list in that persistent white
card, with connector origins aligned to its rows. Also inspect decoded frame180:
source cards appear before the shrinking sheet has cleared them, so filing text
shows behind card text. Delay/reorder their entrance to avoid this overlap.
[[docs/issues/BUG-008 - Authority transition overlaps source cards]].
Relevant files: `src/components/FilingSheet.tsx` and
`src/scenes/AuthoritiesScene.tsx` under `apps/video`.

Render new keyframes before another master. A partial 4K rerender/splice of the
authority interval was proposed to save time (roughly frames168–287; confirm the
actual changed interval and seam). It is not implemented or verified. Keep the
existing master as a prior revision; use a full rerender if splicing cannot be
validated. Mobile source is unchanged and already has readable citation rows.
Update desktop MP4/WebM, recheck metadata, then inspect compressed frames and
complete-loop playback. All rubric dimensions >=8 remain unverified.

The user asked to pack and continue tonight, then allowed finishing if everything
would be quick. Existing exports had finished; the font revision plus re-export/
browser checks was estimated at another10–15minutes, so it remains for tonight.
All agents stopped. No render or encode process remains active. No commit/push.

## Review and preview state
`out/master-review` contains desktop master keyframes, eight transition samples
and endpoints. Keyframes60/144/240/336/420/510/612/690/756 and transitions94/180/279
were inspected. Remaining transitions376/454/551/652/724 and endpoints were not
all visually reviewed. `REVIEW.md` was not created; motion scores are unset.
All mobile key stills were inspected; quote/graph overflow repairs passed.
Encoded-still inspection was not run.

The live Studio preview was opened at `http://localhost:3010/PipelineFilm` and
played for the user. It was muted, looping, then paused at frame347 for packing.
Restart command if needed:
`npm run studio --workspace @filingguard/video -- --port=3010 --no-open`.
The Studio server was stopped gracefully for packing; its tab URL is retained.
Studio started with a root-Zod compatibility warning; this composition uses no
Zod props schema and the actual renders succeeded. No dependency change was made.

`tests/e2e/pipeline-film.spec.ts` includes playback, pause, reduced motion,
failure/retry, offscreen/hidden suspension, cross-breakpoint position restoration
and a full-loop case. The full-loop case is authored and unrun. Resume browser
verification with installed Chrome and workers1 for pipeline-film, home,
evidence-motion and intake specs. Run unit tests, lint, typechecks and build after
the revision. Use the existing synthetic preview; make no live provider calls.

## Related
[[apps/video/README]] | [[apps/video/brief/CRITIQUE]] |
[[apps/web/src/features/home/README]] |
[[docs/decisions/ADR-010 - Remotion pipeline film]] |
[[docs/feedback/FB-009 - Programmatic pipeline film]]

[[docs/sessions/Index]] | [[TODO]]
