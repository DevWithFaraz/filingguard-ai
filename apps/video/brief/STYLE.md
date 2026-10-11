# Motion grammar, components and gotchas

Related: [[apps/video/brief/BRIEF]], [[apps/video/brief/BEATS]],
[[apps/video/brief/CRITIQUE]], [[docs/feedback/FB-009 - Programmatic pipeline film]].
October 7 revision: [[docs/feedback/FB-011 - Richer programmatic film direction]].
The first exports were too plain for the user; the treatment below is implemented
and reviewed on revised output in [[apps/video/brief/REVIEW]].

## Style
- **Lit evidence workbench.** Filing contours, a perspective floor and bundled
  evidence paths create background structure. Layered paper and beveled glass
  give panels depth, while the unchanged PNG sits in a layered brand card.
  Keep structured motion tied to intake, scanning, citation links or findings.
- Essential Authority-card text is authored for its displayed width; never
  shrink the complete document into tiny unreadable copy. Animate geometry and
  keep comparison text settled and flat during reading windows.
- **One container never cuts.** A single `FilingSheet` persists from intake to
  graph. Between beats it changes position, size, radius and fill; its content
  swaps behind a short (<=8 frame) cross-fade. The sheet finally collapses into a
  graph node; the graph's yellow nodes fly into the logo's node positions.
- Ease in: `bezier(0.16, 1, 0.3, 1)`. Ease out: `bezier(0.7, 0, 0.84, 0)`.
- Text enters with a 24px rise + mask; exits with fade (no blur > 6px).
- Shots 2.2-3.4 s across 780 frames at 30 fps. Each beat has one focal object
  (right) and one caption (left); see BEATS.md for exact boundaries.
- A persistent CI-style pipeline rail at the bottom lights stages as they run;
  this is the "CI/CD for court filings" motif.
- Loop: first and last 12 frames are the empty background with HUD only.

## Components (`src/components`)
Background, Hud (brand chip and pipeline rail), Caption,
FilingSheet (morphing container), Chip, StatusPill (icon + label), plus
scene-local cards. Scenes live in `src/scenes`, one file per beat.

## Gotchas
- Strings come from `data/demo/curated-v1` (synthetic filing + public opinions).
  Do not invent cases, quotes, identifiers or statistics.
- Use the concise process titles in BEATS.md. Per the user's current instruction,
  omit the three rejected phrases recorded in FB-009 from the film overlays.
- The result beat shows an evidence report, source links and finding locations.
  Do not invent a score, a live-provider status or a certification seal.
- "Not found" is never "fake": the unresolved citation says "Unresolved - review".
- The privacy beat is titled "Privacy & court rules". Show detection markers and
  masked display text, without a promise that the submitted file was modified.
- Status is never color-only. Yellow is never a status.
- Keep key text 100px inside the frame edges; minimum on-screen text 22px except
  decorative document texture.
- CSS transitions/animations do not render in Remotion; drive all motion from
  `useCurrentFrame()`.
