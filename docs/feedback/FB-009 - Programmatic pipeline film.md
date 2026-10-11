---
type: feedback
status: revision-pending
date: 2026-10-06
tags: [feedback, design, motion, video]
---
# Programmatic pipeline film

## Source
User request on October 6, 2026, paraphrased: generate a code-driven motion-graphics
video of FilingGuard AI's pipeline/workflow using the project palette and logo, to
play on the homepage on arrival. The user supplied a programmatic-video tutorial
transcript, their Remotion experiments and nine illustrative reference frames
(upload, text deconstruction, verification, quote forensics, PII, risk map, score,
brand reveal). These are inspiration and data, not approved copy.

On October 6, 2026, the user explicitly instructed:
> "im still planning so record each and everything in the docs even these questions ...
> i will return and say programmatic video and ai have to continue and ask me these
> questions again (record that too in docs)"

## Need and impact
A visitor should grasp the evidence pipeline quickly. The reference frames include
"ASSURANCE GRANTED", a 98% score and redaction/protection language that conflict
with [[design]] (no approval theatre or fake percentages) and SRS 15.3 disclaimers.
The user wants complete control over design, placement, length, and messaging choices
before final rendering or homepage integration.

## Resumption Protocol (fulfilled October 6, 2026)
When the user returns and says:
`programmatic video`
The AI assistant must immediately resume this planning thread, acknowledge the state,
and ask the user the **6 Design Questions** below again for their decision.
The user returned with that phrase, the questions were re-presented, and the
answers below now supersede the earlier proposals. Do not re-ask answered choices.

## Original 6 Design Questions (historical proposals)

### 1. Video Length & Aspect Ratio
- **Option A (Recommended):** ~26-second 16:9 widescreen (gives each of the 9 pipeline stages ~2.5–3 seconds to be clearly readable).
- **Option B:** Fast-paced 15-second cut.
- **Option C:** 16:9 widescreen plus a 9:16 vertical cut for social media (X/Reels/TikTok).

### 2. Website Delivery Method
- **Option A (Recommended):** Pre-rendered video file (`.mp4` / `.webm`) in a `<video autoplay muted loop playsinline>` tag with pause control and reduced-motion fallback poster. Hardware-accelerated, lightweight, and won't compete with the Three.js hero scene for browser CPU.
- **Option B:** Live React vector `<Player />` component from Remotion. Runs live code directly in the browser—infinitely sharp at any zoom level, but executes live React animation continuously.

### 3. Placement on the Home Page
- **Option A (Recommended):** In the "How It Works" section just below the fold. This preserves the filing composer at the top as immediately usable on arrival, and users scroll down to see the animated engine pipeline.
- **Option B:** In the hero viewport alongside the composer.

### 4. Audio & Sound Design
- **Option A (Recommended for website):** Silent visual loop (clean, professional, doesn't blast sound unexpectedly at landing page visitors).
- **Option B:** UI sound design (subtle whooshes, clicks, and a tech synth bed).
- **Option C:** Full voiceover narration (explaining the product).

### 5. Logo & Typography
- **Logo:** High-res transparent PNG (`filingguard-logo.png`) on frosted brand card, vs. SVG vector asset if provided by user.
- **Fonts:** Currently using `Inter` + `JetBrains Mono` (OFL). User to confirm whether `GC Avalance` permission covers video distribution before applying to display titles.

### 6. Video Copy & Safety Disclaimers
- Mockup reference showed *"ASSURANCE GRANTED · 98%"*.
- Proposed replacement: **"READY FOR HUMAN REVIEW"** (with transparent score breakdown: 2 Critical Findings, 3 Warnings, 5 Passed Checks), strictly obeying SRS 15.3 disclaimers and `design.md` anti-approval rules.

## Choices supplied on resumption

User responses on October 6, 2026, paraphrased:

- Approximately 26 seconds, 16:9 widescreen.
- Rendered MP4/WebM, with "doube sharp res or somthing" requested.
- A "How it works" section below the hero.
- Silent loop.
- Only the existing PNG logo is available.
- Do not use the proposed "Ready for human review", "Illustrative · synthetic
  sample", or "Flagged for redaction" wording in the film. The user's response
  was: "nah dont worry about it you dont need to be careful so dont use these
  words okay".

No new font choice was supplied. Retain the existing Inter + JetBrains Mono
direction rather than treating site-specific Avalance permission as a new video
font decision. Preserve the earlier instruction not to commit or push.

## Response and planning specification

The selected configuration is recorded in
[[docs/decisions/ADR-010 - Remotion pipeline film]]. A genuine 3840x2160 master
is the proposed interpretation of the sharpness request: render the 1920x1080
vector composition at 2x in each dimension, rather than upscaling a finished
1080p video. Plan 2560x1440 desktop and 1920x1080 smaller-screen website encodes;
actual media size, readability and playback must determine the final encodes.

The proposed copy uses concise process titles, with "Evidence report" before the
brand reveal. The rejected phrases will not appear as film overlays. This removes
the earlier mandatory film-label proposal; it does not assert that the animation
is a recording of currently running legal engines. Product requirements outside
the film have not been changed by this response.

[[apps/video/brief/BRIEF]] and [[apps/video/brief/BEATS]] contain the reviewable
brief and proposed 26-second sequence. Configuration choices are accepted;
the detailed storyboard and aesthetic result have not yet been accepted.
The user subsequently said "start now", authorizing scene assembly, rendering
and the selected homepage integration. The composition and embed are now
implemented; masters and website exports pass metadata/size checks. The user's
first-output Authority-card feedback and remaining checks are preserved in
[[docs/feedback/FB-010 - Readable authority card in pipeline film]] and
[[docs/sessions/2026-10-06 - Programmatic video production]].

During production the user questioned the diff badge's large removed-line count.
The explanation identified rewrites of draft scene layouts and superseded score/
assurance copy. All nine film beats remain; no backend, API, intake or review
feature was removed by this film work.

## Historical scaffold inspection (before production)
- Workspace created: `@filingguard/video` in `apps/video` using Remotion 4.
- Harness files:
  - `apps/video/brief/BRAND.md`: exact palette (`#0E0620`, `#3E0F8D`, `#9564DD`, `#E4DA72`, `#F4F0FB`), type rules.
  - `apps/video/brief/STYLE.md`: "one container never cuts", explosive bezier easing.
- `apps/video/src/brand.ts`: existing beat timeline mapping (0–810 frames,
  27 seconds); not yet aligned with the new 780-frame plan.
  - `apps/video/src/components/chrome.tsx`: background, HUD, animated CI pipeline rail.
  - `apps/video/src/components/FilingSheet.tsx`: morphing filing sheet container.
- `apps/video/src/scenes/`: seven drafted scene files, with parsing and privacy
  content also represented in shared components; not a completed nine-beat film.
- Root composition, entry point, rendering/encoding scripts and rendered media
  are absent in the inspected workspace. Existing draft code still contains old
  wording and must be aligned before rendering.
- The next planning step is review of the detailed beat plan, followed by scene
  assembly, rendering and homepage integration within D006.

[[TODO]] | [[docs/feedback/Index]] | [[docs/decisions/ADR-010 - Remotion pipeline film]] | [[docs/sessions/2026-10-06 - Programmatic video choices and beat plan]]
