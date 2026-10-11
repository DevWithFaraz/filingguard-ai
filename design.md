---
type: design
status: in-progress
date: 2026-09-28
tags: [design, frontend, motion]
---
# FilingGuard AI - Experience and Motion Brief

## Intent and status
Create a distinctive, highly polished and engaging product experience: memorable
first impression, useful interaction, precise typography and excellent visual
hierarchy. Award-caliber is an aspiration, not a claim or guarantee of awards.
The user authorizes choosing tools/methods to elevate the redesign, including
GSAP, Three.js or Motion. The first homepage composition and GSAP/CSS motion pass
was implemented locally, then expanded into glass navigation, rounded controls,
Three.js hero depth and a selectable evidence study in D002. D006's authored
video and homepage embed are implemented with delivery checks underway; detailed
widget/grid motion and results-screen design remain proposed.
See [[docs/sessions/2026-09-29 - Glass homepage and evidence motion]].
Requirements/tasks remain [[FilingGuard_AI_SRS]] and [[TODO]].

[[docs/product/UI direction]] owns existing references, supplied assets, font
permission provenance, routes and approved composer scope. This note owns the
expanded motion/art-direction brief; do not create divergent asset/feature claims.
The user's detailed widget/grid/page-motion ideas are still to come and can refine
these proposals. The user accepted the initial homepage direction; final product
art direction, results-screen design and larger narrative motion remain pending.

## Direction
The visual story is evidence becoming inspectable, not an AI magically approving
a filing. Pair an expressive image-backed home experience with a quiet, dense,
neutral review workspace. Purple/lilac brand accents and the supplied legal image
provide character; yellow is restrained emphasis, not success or severity.
Use charcoal, white/light gray and distinct accessible status colors outside the
hero. Status always has a label/icon; unknown is never styled like verified.

Give the first viewport three clear levels: FilingGuard-AI display title, brief
literal pre-filing-review context, then the actual Text/PDF/Demo composer. Keep
brand title over the supplied full-bleed bitmap, not inside a decorative card.
The central translucent composer is a genuine tool, with a stable frame, readable
surface and opaque fallback. Do not bury the main workflow behind a landing CTA.
Leave the next section visibly beginning at the fold on phone/tablet/desktop.

GC Avalance is for the brand/display only, under the user's reported creator
permission; retain licensing evidence before distribution. Keep evidence/body
text in the existing readable UI font. Use explicit breakpoint sizes, no viewport
font scaling or negative letter spacing. Prototype 64-80px desktop and 32-40px
mobile brand type, then verify longest-word fit with the actual font. Long titles
wrap deliberately; compact panels never inherit hero-sized headings.

## Tool Selection
Choose GSAP + @gsap/react + ScrollTrigger as the primary choreography stack, with
scoped useGSAP cleanup, timelines and responsive/reduced-motion matchMedia. Native
CSS handles simple hover/press/focus transitions. No need for an additional Motion
(formerly Framer Motion) dependency initially; introduce it only for a demonstrated
layout/presence problem that GSAP/CSS cannot solve cleanly. Never let two libraries
animate the same properties. Keep the current React/Vite application, not a new
Framer-hosted site or framework migration.

Use Three.js for a purposeful optional signature scene in the workflow section:
an unframed, full-width document-to-evidence assembly. It can add spatial depth to
the narrative, but must not replace actual 2D evidence.
Lazy-load it after the usable composer and compare against a lightweight DOM
prototype first. Retain it only if the measured visual/interaction benefit warrants
GPU/bundle cost. No gratuitous spinning scales/gavel, particle clouds, gradient
orbs or endless background motion. React Flow remains the actual claim-authority
graph engine; Three.js does not take over domain logic.

September 29 user refinement: the supplied background is flexible, not the whole
composition. A second transparent Three.js layer is now allowed over it, with
curled paper/ribbon forms constrained to the edges. The image is subdued rather
than replaced. The header uses dark glass and a CSS-white treatment of the logo;
the original image file is unchanged. Composer corners are 24px and primary
controls 12px, explicitly following the user's request for rounder shapes.
Avalance remains the display face; heading pieces have a coordinated masked
entrance. Both scenes are nonessential and have static fallbacks. D002 validation
does not establish an award, comprehensive accessibility compliance or mobile GPU
performance on physical devices. See [[docs/feedback/FB-006 - Glass and stronger 3D]].

GSAP's React hook provides scoped cleanup, and matchMedia supports reverting
breakpoint/reduced-motion setups. Use these patterns rather than unscoped global
tweens. [GSAP React](https://gsap.com/resources/React/),
[matchMedia](https://gsap.com/docs/v3/GSAP/gsap.matchMedia()/).

## Signature Sequence
September 29 follow-up (D003): the latest user preference supersedes D002's dark,
floating rounded header and white logo treatment. Use an edge-to-edge square
header with light frosted glass and original logo colors. The footer also uses
the original asset. Hero sheets are now rigid planes with layered backing pages;
remove twisting ribbons and deformation while retaining restrained parallax.
See [[docs/feedback/FB-007 - Original logo and clean paper]].

1. **Arrival:** logo/title/supporting content compose in one short coordinated
   timeline, roughly 600-900ms total. Composer is usable immediately, including
   keyboard focus. Do not hide content while waiting for images/fonts/animation.
2. **Composer:** active mode indicator moves between Text/PDF/Demo without moving
   controls. On valid drag-over, border/target responds; selection resolves into
   stable filename/size/remove controls. Invalid files get an immediate clear
   message, not theatrical shaking or a fake success check.
3. **Evidence assembly:** scroll advances an illustrative sample document into
   citation occurrences, source passages and linked claims. DOM labels and an
   accessible ordered list carry the same explanation. Optional Three.js depth
   presents these relationships unframed, with click/keyboard step controls and
   pointer response limited to a small nonessential range. Use public/synthetic
   examples only and label them; never depict actual verification before engines run.
4. **Evidence lens:** select an actual sample quotation to reveal the corresponding
   source text and changed word, preserving exact text and source attribution.
   This can be more distinctive than generic entrance effects. Comparison stays
   readable, selectable and available without hover or animation.
5. **Walkthrough:** D006 implements an authored process film below the hero,
   superseding the earlier future-recording direction. See
   [[apps/video/brief/BRIEF]] and [[docs/decisions/ADR-010 - Remotion pipeline film]]
   for the selected silent loop, controls, poster and reduced-motion behavior.
   Use concise context beside the film and stack on mobile, where the film uses
   larger evidence text. End with retention/limits and a clear return to the
   composer.

A desktop narrative can use one short bounded pinned sequence if testing shows it
helps. Never pin the composer, trap scrolling or require a tour to upload. Mobile
uses ordinary vertical flow, no horizontal scroll simulation or long pinning.

## Micro-Interactions
- Buttons: instant focus indicator, 120-180ms hover feedback, 80-120ms press
  response; no moving hit targets, cursor replacement or delayed click handlers.
- Mode tabs: 180-240ms selection transition; icon/text remains in stable tracks.
- Evidence rows: focused/selected accent and 160-220ms detail transition; preserve
  scroll position, keyboard focus and text selection. Never animate every word.
- Findings filters: maintain counts and list stability; animate only changed,
  visible items. Empty/unavailable states appear immediately with recovery action.
- Progress: animate only real stage changes. No timed fake percentages, optimistic
  verified states, counter-up user statistics or pulse suggesting work after failure.
- Graph: selection emphasizes relevant links while others remain legible; equivalent
  keyboard list and reduced-motion transitions expose the same stored evidence.
- Deletion/export/retry: precise pending/confirmed/error states; animations never
  substitute for server success or suppress errors. Do not replay POST on effects.

The user's forthcoming widget/grid-motion ideas refine this vocabulary. Repeated
item layouts may use a purposeful grid, but do not turn every section into floating
cards or nest cards. Use full-width bands/unframed sections, radius <=8px for truly
framed tools/items unless a deliberate approved design system requires otherwise.

## Workspace Hierarchy
Results prioritize coverage and critical review signals, then finding filters/list,
then an evidence detail pane. Use restrained headings, predictable commands and
compact spacing; original excerpt and source passage remain the visual center.
Distinguish preparation, running, partial, unavailable and completed states.
Current preparation must still say legal analysis not run. Graph/report controls
only become active when real services exist; teams/Q&A are not implied by visuals.
Activity is private temporary session history, not an account archive.

## Responsive, Accessibility and Performance Gates
Test 360/390px phones, 768/1024px tablets, 1440px and wide desktop. Inspect real
bitmap crops, font loading, long filenames/headings, multiline buttons and keyboard
focus. No incoherent overlap or page-wide overflow. Minimum 44px touch targets,
WCAG AA contrast, labelled controls and native scroll remain non-negotiable.
Visible text should be product/document content, not instructions about its styling,
animation, shortcuts or feature implementation.

Reduced motion renders all substantive information immediately, disables parallax/
scrub/pinning/3D continuous movement and preserves useful instant state feedback.
Pause offscreen/hidden-tab animation; prefer transforms/opacity, batch reads/writes
and avoid animating blur or layout-heavy geometry. Refresh scroll positions after
actual image/font/layout changes, not every frame. Clean up on route changes.

Three.js must have a DOM/static fallback for unavailable/lost graphics contexts,
controlled render resolution, bounded scene complexity and resource disposal.
Budget <=16.7ms/frame desktop and <=33ms/frame representative mobile as targets,
not measured promises; simplify/remove the scene if real traces fail. Camera aspect
must follow canvas size. Resource lifetime/resolution guidance:
[Three.js responsive design](https://threejs.org/manual/pages/responsive.html),
[cleanup](https://threejs.org/manual/pages/cleanup.html).

Before accepting a 3D implementation, Playwright screenshots plus canvas-pixel
checks must confirm nonblank, correctly framed rendering and real movement/
interaction at desktop/mobile sizes. Check fallbacks, asset errors, reduced motion,
keyboard/touch operation, route-unmount cleanup and slow-device performance.
No library alone qualifies a design as award-worthy; visual/interaction quality
must be reviewed with the user against actual screenshots and behavior.

## Delivery Order
September 29 D004 refinement supersedes D003's rigid hero sheets: use restrained
S-curves with different left/right silhouettes, cursor tilt and independent hover
lift. The main heading uses genuine Avalance SemiBold to open its counters; the
footer gives the original logo precedence over a smaller tagline and aligns its
navigation. See [[docs/feedback/FB-008 - Asymmetric curved papers]].

First refine static hierarchy, responsive composition and asset typography; then
add the GSAP entrance/composer interactions; then sample evidence choreography;
finally prototype and evaluate optional Three.js. Keep the backend/access workflow
intact throughout. Formal task status stays only in [[TODO]], not this brief.

[[docs/product/UI direction]], [[docs/product/Features]],
[[docs/feedback/FB-005 - Distinctive interactive redesign]],
[[docs/architecture/stack]], [[Home]].
