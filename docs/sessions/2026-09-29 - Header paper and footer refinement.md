---
type: session
status: completed
date: 2026-09-29
tags: [design, frontend]
---
# Header paper and footer refinement
D003 implements [[docs/feedback/FB-007 - Original logo and clean paper]]. Removed
the logo's white CSS filter, expanded the header edge to edge with zero corner
radius, and switched to light translucent glass with blur and an opaque fallback.
Expanded the footer with the original logo, sample/privacy/top navigation and
existing API status/settings controls. Responsive phone layout stacks the footer.

The hero now uses rigid rectangular pages with a subtle backing sheet, restrained
tilts and existing bounded pointer parallax. Removed the sinusoidal deformation,
metallic ribbons and connecting curves. Matte material, filmic tone mapping and
softer lights retain visible document lines. Evidence study and intake unchanged.

Typecheck, ESLint, production build and all 17 frontend unit tests passed. The
first 10-test desktop/phone visual run passed. Final lighting passed all eight
WebGL/motion tests; new exact-width assertions then exposed harmless mobile
subpixel rounding (359.999969 versus 360). Changed the assertion to 0.01px
tolerance, without changing layout. Header/logo/footer regression rerun recorded
in TODO. Screenshots inspected for logo colors, paper appearance and footer layout.
Existing asynchronous Three.js chunk warning remains (~523kB / 130kB gzip).

Local preview stays http://127.0.0.1:5174. No deployment, commit, secret changes,
backend changes or provider calls. Physical-device GPU, screen-reader and
non-Chromium checks were not run. User visual feedback is next; T023 remains the
next backend task. Supersedes the D002 header/logo/ribbon choices, not its history.

[[docs/sessions/Index]], [[Home]], [[TODO]], [[design]],
[[apps/web/src/features/home/README]].
