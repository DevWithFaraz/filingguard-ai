# Film critique and delivery criteria

Task: [[TODO|D006]]. Apply after real stills and clips are rendered.
No scores or pass claims are recorded in this planning document.

## Visual critique

Inspect the proposed still frames in [[apps/video/brief/BEATS]], plus every
transition and the loop seam. Rate each dimension from 1 to 10, with a specific
observation and fix for any dimension below 8. These are design judgments, not
backend tests or proof of the user's aesthetic acceptance.

- Brand: original logo, palette and type treatment match the intended direction.
- Hierarchy: one focal object and title; supporting text does not compete.
- Readability: titles and evidence comparison remain clear at the displayed size.
- Composition: safe margins, clear panel separation and no unintended clipping.
- Continuity: the filing sheet, source panels and graph transition coherently.
- Motion: intentional entrances, settled reading windows and a clean loop seam.
- Evidence: filing/source text stays correctly paired; no invented score or result.
- Copy: agreed process titles, no rejected overlays, no stale draft tagline.

The still review target is every dimension >=8. Record actual inspected frames,
observations, changes and the final round; do not assign scores to unseen output.

## Delivery checks

Verify media metadata: 26 seconds, 16:9, 30 fps, no audio track; master dimensions
3840x2160 and website rendition dimensions as specified in BRIEF.md. Measure
actual byte sizes against the proposed budgets. Inspect PNG edges, fine paths,
gradients and small comparison text after encoding, not just before compression.

Inspect complete motion playback at the actual homepage display size. Stills
alone cannot establish pacing, compression stability or seamless looping.

After integration, run the appropriate frontend typecheck, lint, tests and build,
then desktop/mobile browser checks for playback, pause/play, reduced motion,
poster fallback, offscreen/hidden behavior, keyboard controls and intact intake.
Record checks actually run and their limitations. User aesthetic review and
physical-device performance remain separate from automated browser results.

[[apps/video/brief/BRIEF]] | [[apps/video/brief/BEATS]] |
[[apps/video/README]] | [[TODO]]
