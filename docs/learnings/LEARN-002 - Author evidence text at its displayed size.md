---
type: learning
status: observed
date: 2026-10-07
tags: [learnings, frontend, video, typography]
---
# Author evidence text at its displayed size

## Observation
In the first D006 desktop film, a complete 820px document was scaled into a 330px
Authority card. Its 25px case names became approximately 10px in the 1920px scene.
The user found that white-card text unreadable. Extra export resolution preserved
the small letters sharply, but did not make their displayed size larger.

The revision retains the moving paper container while switching this beat to a
focused list with native 32px names and 24px citations. Fresh source frames 210/240
show readable anchors and accurately aligned source connectors. The separate
mobile composition uses simplified panels and larger evidence text.

## Evidence
[[docs/feedback/FB-010 - Readable authority card in pipeline film]] records the
direct user feedback; [[apps/video/brief/REVIEW]] records the inspected revised
frames. Geometry and type live in `src/components/FilingSheet.tsx` under
[[apps/video/README]]. Current delivery checks are recorded in
[[docs/sessions/2026-10-07 - Pipeline film visual revision]].

## Reusable practice
For essential animated evidence, choose typography and content density for the
settled display width. Share row geometry with connectors so their endpoints
remain accurate after the content changes. Inspect the real homepage/phone size
and decoded files as well as full-resolution authoring stills.

## Applicability and limits
This applies when evidence is authored as editable DOM/SVG/code and a document
container changes size. It does not establish an appropriate minimum for every
font, viewport or scanned document. Recheck reading time, actual CSS display
width, font metrics, contrast and encoding before reusing the approach elsewhere.
The source-frame observation does not establish user aesthetic acceptance or
physical-device playback performance; final delivery results remain separate.

## Related
[[TODO|D006]] | [[apps/video/brief/BRAND]] |
[[docs/decisions/ADR-010 - Remotion pipeline film]]

[[docs/learnings/Index]]
