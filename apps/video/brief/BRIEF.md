# FilingGuard AI pipeline film brief

Task: [[TODO|D006]]. Prepared October 6, 2026.
Configuration choices were supplied by the user; the detailed storyboard below
was authorized for production by "start now". This document specifies delivery
requirements; measured results belong to the production session and media report.
See [[docs/feedback/FB-009 - Programmatic pipeline film]].

## Film in one line

A single legal brief becomes extracted text, connected authorities, a quotation
comparison, a claim-source relationship, privacy/rule markers, an evidence graph
and a report, then resolves into the original FilingGuard AI logo.

## Selected configuration

- 26 seconds, 16:9 widescreen, 30 fps, 780 frames.
- Pre-rendered H.264 MP4 and VP9 WebM with a poster.
- Silent: no music, voiceover or sound-effect track.
- Below the hero in the homepage's "How it works" section.
- Original transparent PNG logo, in its original colors and aspect ratio.
- Inter for display/UI and JetBrains Mono for citations/technical details remain
  the existing working default. No new Avalance video-font choice was supplied.
- Concise process titles rather than the rejected overlay phrases. The planned
  penultimate title is "Evidence report"; the finale is "CI/CD for court filings".

## Resolution and sharpness plan

Author the scene with a 1920x1080 layout and render it at 2x in each dimension,
producing a genuine 3840x2160 master. Text, SVG lines and CSS shapes are rasterized
at that output size; do not upscale an already encoded 1080p file.

Website derivatives are 2560x1440 for desktop and 1920x1080 for smaller
screens. For a band up to 1280 CSS pixels wide, the desktop rendition supplies
two source pixels per CSS pixel. The high-bitrate 4K master remains a local
production output instead of the default homepage download. The mobile rendition
uses a separate composition with larger comparison text and simpler labels;
extra pixels alone do not solve small text at phone widths.

The copied logo is 2172x724. Cap its layout width at 900 pixels (1800 pixels in
the 2x master), preserving enough source pixels for that placement. Animating
surrounding paths and the complete logo does not require an SVG replacement.

Proposed budgets: each desktop website encode <=12 MiB, each smaller-screen
encode <=8 MiB, poster <=350 KiB. These are targets, not measured results.
Tune bitrate/encoding against inspected stills and playback; do not meet a byte
target by making the quotation comparison unreadable.

## Visual and motion direction

Use the existing deep ink, royal purple, lilac, pale yellow and paper palette in
[[apps/video/brief/BRAND]]. Match the homepage's glass surfaces and depth while
keeping source text legible. The October 7 revision adds a lit evidence workbench,
structured filing contours, a perspective floor, layered paper and beveled source
glass; [[docs/feedback/FB-011 - Richer programmatic film direction]] records why.
One filing sheet persists through the first six
beats, folds into the graph, then returns as a report. Paths converge around the
unchanged PNG for the final reveal. No unrelated stock footage is needed.

The nine-frame reference sheet informs composition and depth, not exact labels,
scores or implied guarantees. Titles and timing are in [[apps/video/brief/BEATS]].

## Content plan

Use curated filing strings and cached public opinions from
[[data/demo/curated-v1/README]]. Preserve source identity for quotation/claim
comparisons. This is authored motion, not a live app capture or current provider
execution. No provider request is needed to produce the film.

The film overlays will omit the three rejected phrases recorded in FB-009.
Use action/process names and direct evidence comparisons. The report beat avoids
an invented integrity percentage and arbitrary finding totals; it shows where
the reader can inspect the document passage and linked source instead.

## Planned homepage behavior

Place the film below the first viewport with a "How it works" heading and concise
context. Keep the intake composer immediately usable. Use muted looping inline
playback with a visible pause/play button and a real poster. Start only while the
band is in view; suspend offscreen and hidden-page playback. Reduced motion shows
the poster until the user deliberately starts playback. Preserve a useful static
summary if playback fails, with keyboard-accessible controls.

The silent film needs equivalent process text in the page; no empty audio-caption
track is planned. Existing app-level limits and intake controls are unaffected.

## Production and review boundary

First review this brief and [[apps/video/brief/BEATS]], then align the existing
drafts, assemble the composition, render key stills, and inspect them with
[[apps/video/brief/CRITIQUE]]. Follow with the master and website encodes, poster,
homepage integration and appropriate desktop/mobile/reduced-motion checks.

Configuration acceptance is separate from storyboard/aesthetic acceptance. No
user aesthetic acceptance is implied by implementation or internal review.
Scene assembly, media production and homepage integration are verified locally;
[[apps/video/brief/REVIEW]] and
[[docs/sessions/2026-10-07 - Pipeline film visual revision]] record the checks and
limits. User aesthetic acceptance remains open. Preserve the user's
no-commit/no-push instruction.

[[apps/video/README]] | [[docs/decisions/ADR-010 - Remotion pipeline film]] |
[[apps/web/src/features/home/README]] | [[TODO]]
