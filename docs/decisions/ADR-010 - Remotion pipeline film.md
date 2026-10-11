---
type: decision
status: accepted
date: 2026-10-06
tags: [decisions, frontend, motion, video]
---
# Remotion pipeline film

## Context
[[docs/feedback/FB-009 - Programmatic pipeline film]] asks for a branded motion
film of the review pipeline on the homepage. The homepage already runs GSAP and two
lazily loaded Three.js scenes ([[apps/web/src/features/home/README]]).

## Decision and alternatives
The user selected the delivery direction on October 6, 2026 after returning to
planning. The selected configuration is approximately 26 seconds, 16:9 widescreen,
silent, below the hero in "How it works", with the original PNG logo and sharper
rendering. Inter + JetBrains Mono remain the working typography default because
the user did not provide a new font choice. See
[[docs/feedback/FB-009 - Programmatic pipeline film]].

Author the film as code with Remotion 4 in a separate npm workspace, `apps/video`,
and deliver a rendered, muted, looping H.264 MP4 + VP9 WebM with a poster image to
the web app. Rejected for now: embedding `@remotion/player` live (vector-sharp, but
adds a third main-thread animation runtime beside GSAP/Three.js), Lottie/Rive (needs
After Effects/Rive authoring outside the repo), and image/video-model generation
(non-deterministic, hard to keep truthful and on-brand). The player remains an
option if a measured trace shows low cost.

Remotion licensing: free for individuals and companies with up to three people
(remotion.dev/license, as stated by the CLI during the user's experiment). The
project is a solo effort; re-check if the team grows.

## Consequences
Scene content is reviewable TypeScript using synthetic curated-fixture strings.
Render a 3840x2160 master from the vector scene at 2x in each dimension, with
2560x1440 desktop and 1920x1080 smaller-screen website derivatives. This is a
render specification, not a measured sharpness or playback result. Keep the
high-bitrate master out of the homepage; see [[apps/video/brief/BRIEF]] for the
size and readability budgets. Production still review showed that reducing the
desktop composition to phone width made evidence text too small. A separate
mobile composition retains the timing, palette and widescreen format with larger
comparison text. Its 1920x1080 master is encoded directly for mobile delivery.

Website media will be local build artifacts in `apps/web/src/assets/video`, so
the web build will not need Chromium/FFmpeg. Do not commit or push: the user's
local-only instruction remains in effect. Use a poster, a pause/play button and
a static reduced-motion presentation; stop playback while offscreen or hidden.

The user explicitly rejected the proposed "Ready for human review",
"Illustrative · synthetic sample" and "Flagged for redaction" film wording.
That instruction supersedes this note's earlier mandatory "Illustrative" overlay.
Use process headings and an evidence-report beat without those overlays.
Do not turn this process animation into a claim that unimplemented engines have
run or that a filing has been certified. The app's separate SRS requirements
and existing limits remain outside this video-copy change.

Detailed timing, motion and copy are owned by [[apps/video/brief/BEATS]]. The
previous 810-frame draft and old copy are now replaced by the aligned 780-frame
composition. Local font binaries and license notices make captures reproducible
without external font requests; see [[apps/video/public/fonts/README]].

October 7 production retains lossless PNG captures with native ANGLE on Windows
and concurrency 2. A local same-bundle benchmark found JPEG100 only about15%
faster for frames 336/756; the gain did not justify changing capture format.
The richer whole-film revision requires full rerenders because its background
changes throughout the timeline. Prior output is preserved in hash-verified
revision storage. Evidence and limits belong to
[[docs/sessions/2026-10-07 - Pipeline film visual revision]].

## Verification boundary
Rendering stills/MP4 and homepage browser checks verify the media and embed,
not legal-engine behavior, aesthetic acceptance or physical-device performance.

[[docs/decisions/Index]] | [[apps/video/README]] | [[docs/architecture/stack]] | [[TODO]]
