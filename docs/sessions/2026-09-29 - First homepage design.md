---
type: session
status: completed
date: 2026-09-29
tags: [sessions, frontend, design, motion]
---
# First homepage design

## Task and scope
User said start in response to the proposed homepage/composer design, responsive
review and initial motion pass before T023. D001 in [[TODO]] records this work.
The first pass is implemented and locally inspected; user aesthetic feedback is
pending. T023 was not started while preparing this reviewable design milestone.

## Changes
New HomePage/home.css replaces the root sidebar screen with full-width navigation,
the supplied purple PNG background, Avalance Bold title and a translucent working
Text/PDF/Demo composer. Inner review routes retain their functional workspace.
The reviewed sample has its own `/demo` route and resets back home. Added curated
quote comparison and privacy/limits sections; no invented verification results.

Installed GSAP and @gsap/react with the npm lockfile. Scoped hooks provide a short
entrance timeline and source-panel transitions; CSS handles mode indicator and
button/drag feedback. Reduced motion reverts/skips transforms and transitions.
Mobile menu supports Escape/focus return. Small/short viewport rules preserve
content fit and a visible beginning of the following section. Supplied assets are
unchanged; font copied with the previously user-reported creator permission.

## Verification
17 frontend unit tests passed. Full real Chrome suite: 12 desktop/mobile tests
passed, including real Text/PDF/Demo preparation, owner isolation, reload,
Activity/deletion, unavailable-service behavior and sample/reset navigation.
After final compact/touch-target CSS changes, both focused homepage tests passed
again. Typecheck, ESLint and production build passed; no backend changes were made.

Browser checks covered 320/360/390/768/1024/1366/1440/1920px widths, including
320x667 and 1366x768. Tests verify loaded assets/font, no page overflow, visible
next-section beginning, source-switch draft retention, menu keyboard handling,
reduced motion and no page errors. Desktop/tablet/mobile screenshots were visually
inspected. Private/synthetic E2E data stays in the ignored runtime directory.

The jsdom environment initially lacked matchMedia; added a minimal test shim.
Actual motion preferences are exercised in Chrome. A first filtered test command
was parsed incorrectly through nested npm scripts; reran directly in the web
workspace. These were local verification issues, not deployed incidents.

## Preview and remaining work
Local preview: http://127.0.0.1:5174, with the disposable SQLite API on port 8001.
Hidden launchers: API PID 21640, Vite PID 23412. Use public/synthetic material.
No new deployment, commit/push, provider call or Neon migration was performed.

Review this first composition with the user, then refine from feedback and resume
T023 pipeline orchestration. Larger scroll narrative, optional Three.js, video and
the user's detailed widget/grid ideas remain planned. Screenshots verify sampled
layout behavior, not all browser/accessibility/performance requirements. No WebGL
scene or real-device performance benchmark exists in this pass.

## Related
[[docs/sessions/Index]], [[TODO]], [[design]], [[docs/product/UI direction]],
[[apps/web/src/features/home/README]], [[apps/web/src/features/intake/README]],
[[apps/web/src/assets/README]], [[docs/architecture/stack]].
