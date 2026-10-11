# Programmatic pipeline film

Task: [[TODO|D006]]. User choices and production authorization are recorded in
[[docs/feedback/FB-009 - Programmatic pipeline film]] and
[[docs/decisions/ADR-010 - Remotion pipeline film]].

This separate Remotion workspace owns the authored process animation and media
production. The web homepage consumes rendered files; it does not execute
the Remotion Player. Legal engines remain owned by the API modules.

## Planning files

- [[apps/video/brief/BRIEF]]: delivery, resolution, asset and homepage plan.
- [[apps/video/brief/BEATS]]: proposed nine-beat, 26-second timing and copy.
- [[apps/video/brief/BRAND]]: palette, typography and original PNG treatment.
- [[apps/video/brief/STYLE]]: continuous-sheet motion grammar.
- [[apps/video/brief/CRITIQUE]]: still, motion and delivery review criteria.

## Composition and production

`src/index.ts` registers two 780-frame, 30 fps, 1920x1080 compositions:
`PipelineFilm` and `PipelineFilmMobile`. Desktop is rendered at scale 2 for a
3840x2160 master. Mobile has its own larger-text 1920x1080 composition with the
same timing, rather than shrinking desktop evidence panels. Local Inter and
JetBrains Mono FontFace assets load before capture; rendering needs no external
font request. Provenance and exact license notices live in
[[apps/video/public/fonts/README]]. The original PNG remains unchanged.

Run from the repository root:

```powershell
npm run typecheck --workspace @filingguard/video
npm run still --workspace @filingguard/video
npm run still:mobile --workspace @filingguard/video
npm run render --workspace @filingguard/video
npm run render:mobile --workspace @filingguard/video
npm run encode --workspace @filingguard/video
npm run verify --workspace @filingguard/video
npm run inspect:encodes --workspace @filingguard/video
```

Scripts use installed Chrome and Remotion's bundled FFmpeg/ffprobe.
`REMOTION_BROWSER_EXECUTABLE` can select another Chrome executable.
Windows defaults to native ANGLE after a same-frame benchmark; other platforms
default to software `swangle`. `REMOTION_GL` explicitly selects either renderer.
Ignored `out` owns masters,
bundles and review stills. `render:smoke` checks the toolchain, not the full film.

`encode` validates both masters and writes H.264 MP4/VP9 WebM desktop
(2560x1440) and mobile (1920x1080) files plus a WebP poster into
`apps/web/src/assets/video`. It checks the byte budgets in
[[apps/video/brief/BRIEF]]. `verify` writes `out/media-report.json`;
`inspect:encodes` extracts quotation and brand frames from all four website files.
Both revised masters and website files have passed metadata/size checks. The
October 7 revision replaces tiny Authority-card copy with a native citation list
and enriches both compositions with layered paper/glass and a structured evidence
workbench background. Revised stills, full exports and 44 decoded web frames were
reviewed; internal scores are 8–9. Homepage checks pass22 browser cases plus 2 focused
checks after a mobile copy correction,20 unit tests, typecheck/lint/final build.
[[apps/video/brief/REVIEW]] records evidence and quality limits, including minor
WebM grain smoothing and brisk reading windows. The prior exports are preserved under ignored
`out/revisions/v1`, with 34 copied files checked against their original SHA256s.
Current results belong to
[[docs/sessions/2026-10-07 - Pipeline film visual revision]].

## Boundaries

Use only curated fixture material from [[data/demo/curated-v1/README]] for the
animation. Do not call CourtListener/Groq to manufacture scene content or modify
the source fixture. The movie shows the designed workflow; authoring/rendering
does not verify backend legal-engine behavior.

All changes remain local. Do not commit or push. Track live task status only in
[[TODO]]; the user resumed the revision and expanded its visual scope on October 7.

[[apps/web/src/features/home/README]] |
[[docs/sessions/2026-10-06 - Programmatic video choices and beat plan]]
