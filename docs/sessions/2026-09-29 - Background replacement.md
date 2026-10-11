---
type: session
status: complete
date: 2026-09-29
tags: [sessions, frontend]
---
# Background replacement

## Task and changes
D005: user reported a pixelated/blurry background and supplied Downloads/background.jpg.
Old bitmap was 1672x941, rendered with cover scaling and opacity .38 beneath
a 52% dark overlay. There was no blur filter on the image itself. Enlargement can
soften detail; double fading lowered contrast. Glass panels retain intentional blur.
Replaced the import and intrinsic dimensions with unchanged 3888x2592 JPG,
removed image opacity reduction and retained readability overlay. Paper scene unchanged.
Asset hash/provenance: [[apps/web/src/assets/README]].

## Verification
Production build passed, with existing shared Three.js chunk-size warning.
Desktop homepage test passed. Mobile initially timed out during concurrent build;
standalone retry passed in 17.3 seconds, without increasing the timeout.
Added browser assertions for natural dimensions, full opacity and no image filter.
Desktop/mobile screenshots inspected. Unit tests and full motion suite not rerun
for this asset/CSS change; no renderer logic changed. Not deployed.

## Next
Subsequent user-requested header trial: blended existing lavender into #e4da72,
retaining glass blur and a solid-browser fallback gradient. Aesthetic approval
pending; isolated to two header CSS rules for easy reversal.
Desktop browser check passed; mobile passed on retry after a navigation-context
interruption in the first run. Desktop screenshot inspected. Build not rerun
for this CSS-only trial; visual acceptance remains with the user.

User visual review at http://127.0.0.1:5174/. Backend T023 remains next.
[[TODO]] | [[apps/web/src/features/home/README]] | [[docs/sessions/Index]]
