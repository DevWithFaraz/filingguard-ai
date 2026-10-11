---
type: session
status: completed
date: 2026-09-29
tags: [sessions, frontend, design, motion]
---
# Glass homepage and evidence motion

## Scope and implementation
D002 responds to [[docs/feedback/FB-006 - Glass and stronger 3D]]. User requested
implementation, not more work-order prompts. A Sol-medium worker authored the
isolated hero overlay; the main agent integrated, refined and tested it.

The homepage has dark glass navigation, a CSS-white logo, 24px composer corners,
12px primary controls, Avalance choreography, scroll reveals, focus/drag/hover
feedback and a focus-difference toggle. The supplied image is retained but subdued.
Text blocks animate as units, avoiding heading/body overlap.

Three.js and its types were installed with the npm lockfile. HeroBackdrop lazily
loads curled edge papers/ribbons; EvidenceExperience lazily loads selectable
filing, authority and difference stages. Both have bounded, on-demand rendering,
resolution limits, resource cleanup, visibility handling and reduced motion.
The study is illustrative and explicitly labelled, with corresponding DOM text;
it is not a legal engine or provider result. Private intake is unchanged.

## Verification
Full Chrome suite: 20 desktop/mobile tests passed, including real Text/PDF/Demo
preparation, ownership and deletion. Final contrast/spacing refinements passed
10 focused homepage/motion tests; a further two-test responsive screenshot pass
passed after initializing scroll sections before capture. Frontend unit suite:
17 passed. TypeScript, ESLint and production build passed.
Final initial-paper framing adjustment passed all eight motion tests again, with
pixel bounds asserted for all three study poses on desktop and phone.

Pixel assertions cover nonblank canvases, paper framing, changed pixels after
stage selection and mouse input, and a transparent hero center. Tests cover
reduced motion, WebGL unavailability, keyboard stages, repeated navigation and
no duplicate study canvases. Samples include 320/360/390/768/1024/1366/1440/1920px
widths and compact heights. Desktop/tablet/phone screenshots were inspected;
images remain ignored in `.runtime`.

An initial browser attempt was blocked by the approval service's usage limit.
After user-requested continuation, approval and verification succeeded. A Windows
TS/TSX naming conflict caused a local integration build/browser failure; distinct
component/helper names fixed it. The stale-import run was stopped, and the clean
rerun passed. See [[docs/issues/BUG-006 - Case-insensitive hero import collision]].

## Limits and next work
Vite warns about the lazy Three.js chunk: approximately 528kB minified / 132kB
gzip. Main JS is approximately 454kB / 152kB gzip. The supplied background remains
1.9MB and logo 392kB; later asset optimization is warranted. No Lighthouse,
screen-reader audit, physical-phone GPU benchmark or non-Chromium validation was
performed. Backend tests were not rerun because backend code is unchanged.

Preview: http://127.0.0.1:5174, disposable local API on port 8001. No commit,
push, hosted deployment, Neon migration, secret change or live-provider call.
User aesthetic review is next; T023 remains the next backend task. Video,
results-screen design and future widget/grid motion are not claimed complete.

[[docs/sessions/Index]], [[TODO]], [[Home]], [[design]],
[[apps/web/src/features/home/README]], [[docs/architecture/stack]].
