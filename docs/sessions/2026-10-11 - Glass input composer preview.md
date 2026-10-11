---
type: session
status: verified-local-preview
date: 2026-10-11
tags: [sessions, design, materials]
---
# Glass input composer preview

## Scope and changes
User asked to remember the existing UI direction during remaining development and
preview glassmorphism on the homepage rounded input box. Worked solo using the
installed apple-design skill. D008 in [[TODO]] owns completion; no aesthetic
approval is assumed. Continuing theme, clear steps, timely/quick navigation and
accessible motion are now persistent guidance in [[AGENTS]] and
[[docs/product/UI direction]]. Feedback:
[[docs/feedback/FB-013 - Glass composer and continuing UI scope]].

`home.css` changes the composer only: lilac translucent gradient, 28px blur,
light-catching edge, shadow depth and darker secondary text. Layout, image/font
assets, form state, submission behavior and existing animation remain intact.
One blurred layer avoids stacking frosted rows; controls retain solid treatments.
Opaque defaults and reduced-transparency/contrast/forced-color rules are authored.
Module ownership: [[apps/web/src/features/home/README]].

## Checks and limits
Fresh isolated desktop/mobile sequential keyboard and WCAG-tagged axe journeys
pass 2/2. Production build/typecheck passes; pre-existing bundle-size warnings
remain. Text/PDF/Demo switching was inspected through keyboard interaction in the
in-app browser, without submission. An isolated Chromium development probe verifies
actual normal blur and opaque/blur-free increased-contrast and reduced-transparency
media states. No horizontal overflow at 1440x1000 or 390x844. Desktop/mobile
screenshots inspected and retained under ignored `.runtime/glass-composer/` with
`receipt.json` and reproduction probe `verify.mjs`. No raw filing/provider data.
The browser viewport override was reset; the review tab is marked as a deliverable.

No new API behavior, provider request, hosted rollout, physical-device performance
or physical screen-reader acceptance was tested or claimed. Automated axe checks
do not certify every possible background/pixel contrast combination. Existing
homepage assets/layout remain the reference for later work.

## Next
User visual review at http://127.0.0.1:5174/. Adjust this material from actual
feedback; do not infer approval or redesign the rest of home. T057 hosting-access
blocker remains as recorded in
[[docs/sessions/2026-10-11 - Accessibility performance and release gates]].

[[docs/sessions/Index]] | [[TODO]]
