---
type: issue
status: resolved-locally
date: 2026-10-06
tags: [issues, motion, video]
---
# Authority transition overlaps source cards

## Symptom and impact
Decoded desktop master frame180 shows filing text behind source-card text as
the filing shrinks and source cards enter. This affects the first desktop film
revision's readability. It was observed locally; no deployment is claimed.

## Reproduction and evidence
Inspect the retained first-version `apps/video/out/master-review/frame-180.png`
(6 seconds), or seek the backup under `out/revisions/v1/apps/video/out` to that
frame. Expected: the filing clears the source panels
before their content becomes readable. Actual: both layers occupy the panel area.
The master-review manifest records the decoded output. Transition180 was visually
inspected by the evidence reviewer.

## Cause and implemented fix
The sheet geometry settles at frame 192, while source cards enter earlier. Check
the entrance opacity/order in `AuthoritiesScene.tsx` alongside `FilingSheet.tsx`.
The October 7 source revision delays the first source surfaces to frame 195, after
the sheet settles at 192; all source rows are visible by 218. Native-sized citation
anchors replace the scaled document in this beat. Typecheck passes. New
transition stills and both compressed formats at 180/192/210/240 show the sheet
clearing source surfaces before entry, with no overlap. Continuous desktop
playback passes in the 22-case browser suite. Resolved locally; evidence:
[[apps/video/brief/REVIEW]] and
[[docs/sessions/2026-10-07 - Pipeline film visual revision]].

## Related
[[TODO|D006]] | [[apps/video/README]] |
[[docs/feedback/FB-010 - Readable authority card in pipeline film]] |
[[docs/sessions/2026-10-06 - Programmatic video production]]

[[docs/issues/Index]]
