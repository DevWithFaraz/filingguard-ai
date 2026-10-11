---
type: session
status: completed-locally
date: 2026-10-07
tags: [sessions, frontend, motion, video]
---
# Pipeline film visual revision

## Task and scope
[[TODO|D006]]. The user resumed the Authority-card fix and requested a richer
whole-film/background treatment. Previous pause is revoked by this request.
All work remains local, with no commit or push.

## Implemented changes
The shared backdrop, intake platform, graph nodes/paths and logo reveal now form
a layered evidence workbench. Desktop evidence panels and mobile stage motion
have paper/glass depth, lit edges and traveling evidence paths. The Authority
sheet uses native 32px names and 24px citations, with shared row-center geometry
for its connectors. Source cards wait until the filing clears their area.
The final static round moved the graph Quote ring clear of the excerpt, faded
report content before the logo entrance, and repaired two mobile spacing issues.
Existing masters/media/evidence were copied into `apps/video/out/revisions/v1`;
34 copied files passed SHA-256 comparison with their originals before replacement.

## Verification
Production-script syntax checks passed. A same-bundle 4K ANGLE capture benchmark
on the prior design compared PNG to JPEG quality 100: mean 3.35s versus 2.85s for
frames 336/756. Visual comparison found no obvious JPEG softening, but the modest
gain did not justify changing lossless master capture. PNG/ANGLE/concurrency 2
remain selected. This is a local measurement, not a general performance claim.

Video typecheck passes. Web unit tests pass 20 tests in 4 files. Final web
typecheck/lint/build pass after the new media and mobile copy correction; the
existing Three.js chunk-size advisory remains. The build includes all five
revised asset hashes.

Reviewed 20 desktop samples plus final 594/690/724 repairs, 14 mobile samples and
44 decoded web frames. All eight internal critique scores are 8–9, including a
qualified Motion 8 after continuous browser playback. Desktop 0/779 source PNG
hashes match; encoded texture differs slightly. See [[apps/video/brief/REVIEW]].

The revised desktop master verifies: 3840×2160, 26 seconds, 30fps, 780frames,
H.264/yuv420p, no audio, 21,910,281 bytes. Full render elapsed 1,029 seconds with
PNG/ANGLE/concurrency 2. This local timing includes frame capture/encoding, not
website-device performance. The mobile 1920×1080 master verifies at 8,634,981 bytes
with the same duration/fps/silence; render elapsed 241 seconds.

Web sizes: desktop MP4/WebM 6,545,687/5,133,879 bytes; mobile MP4/WebM
4,784,963/3,562,714 bytes; poster 83,874 bytes. Desktop 2560×1440, mobile 1920×1080,
poster 1920×1080. All budgets pass on the first quality attempt. Exact results
are in `apps/video/out/{master-report,mobile-master-report,media-report}.json`.

Installed-Chrome browser suite passes 22/22, one worker, desktop/mobile, covering
pipeline-film, home, evidence-motion and intake. Both uninterrupted 26-second
loops select WebM, sample all nine beats and wrap once with zero page errors.
Traces contain 777/778 callbacks. Viewport switching preserves position/pause;
controls, reduced motion, offscreen/hidden suspension, poster/retry and synthetic
intake cases pass. Visibility is exercised deterministically in headless Chrome.

Initial browser attempts had sandbox startup, reused preview-server ownership
and overbroad media interception failures. A clean CI=1 run and media-resource-only
route repair produced 22/22 passes. Screenshot review then found “briefto” on
mobile; explicit JSX whitespace fixes it. The existing layout/rendition case
passes 2/2 after that copy-only fix, and final lint/build pass afterward.
[[docs/issues/BUG-010 - Mobile film description joins words]] and
[[docs/issues/BUG-011 - Media failure test blocks Vite imports]] record the faults.

## Limits and checks not run
The fast proposition/report beats demonstrate the process, with pause available
for reading every word. WebM smooths fine grain and has faint dark-gradient tonal
steps; the 4K MP4 retains more texture. No blocking clipping or essential-text
loss was found in inspected samples. Physical devices, Safari and production
deployment were not tested. User aesthetic acceptance remains open. Backend
legal-engine/provider tests were not run because this task changes authored
media/embedding, not those engines; no live provider request was made.

## Handoff and next step
D006 is verified locally and the revised video is delivered for user review.
No render/encode processes remain. Test-owned 8000/8001/5173/5174 servers were
cleaned up; local Studio 3010 remains available at `/PipelineFilm`. Prior exports
remain in `apps/video/out/revisions/v1`. No commit, push or deployment.
The broadened background change required full exports rather than a partial splice.
No engineering blocker remains for D006. Await user visual feedback; T033 is the
next ordered product task and was not started.

## Related
[[docs/sessions/2026-10-06 - Programmatic video production]] |
[[docs/feedback/FB-011 - Richer programmatic film direction]] |
[[docs/issues/BUG-008 - Authority transition overlaps source cards]] |
[[apps/video/README]] | [[apps/web/src/features/home/README]]

[[docs/sessions/Index]] | [[TODO]]
