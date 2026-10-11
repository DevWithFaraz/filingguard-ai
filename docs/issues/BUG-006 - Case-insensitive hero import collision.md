---
type: issue
status: resolved
date: 2026-09-29
tags: [frontend, windows, build]
---
# Case-insensitive hero import collision

The local integration used `HeroScene.tsx` beside `heroScene.ts`. On Windows,
the extensionless component import resolved to the renderer helper, causing
TS2305/TS1261 and a failed browser module import.

Renamed files to `HeroBackdrop.tsx` and `heroDepthScene.ts` and updated imports.
Distinct stems also removed stale Vite resolution after a helper-only rename.
Production build and the clean 20-test browser suite passed. Local defect only;
no deployed incident occurred.

[[docs/issues/Index]], [[apps/web/src/features/home/README]],
[[docs/sessions/2026-09-29 - Glass homepage and evidence motion]], [[TODO]].
