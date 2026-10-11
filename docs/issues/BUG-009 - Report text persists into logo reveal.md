---
type: issue
status: resolved-locally
date: 2026-10-07
tags: [issues, motion, video]
---
# Report text persists into logo reveal

## Symptom and impact
The desktop source preview at frame 724 exposed a small strip of report text
below the incoming logo card. This was an unintended overlapping reading layer
in the local D006 revision; no deployed incident is claimed.

## Reproduction
Inspect the report-to-logo transition at frames714–734 with the report content
still at full opacity. Expected: the paper can continue moving as a clean backing
layer while the logo enters. Actual: “equal. ≠ unequal.” remains visible below it.

## Evidence
The root and render reviewer inspected the pre-fix frame 724. That PNG was replaced
by the repaired capture, so the current `out/stills/frame-724.png` is regression
evidence rather than the original symptom. The observed repair is also recorded
in [[apps/video/brief/REVIEW]].

## Cause
`FilingSheet.tsx` kept report content visible while its paper shrank through the
logo entrance. The container's later fade did not clear the exposed text soon
enough. This was confirmed by source inspection and the frame 724 capture.

## Fix and regression check
Fade inner content during frames714–720 while preserving the moving paper layer.
Rerendered frame 724 has no exposed report text; frame 690 retains all settled
report rows/footer. Video typecheck passes. Decoded frame 724 in both desktop
formats has a clean paper tail with no exposed report text; frame 690 retains the
report footer. The full desktop browser loop also passes. Resolved locally;
[[apps/video/brief/REVIEW]] records the final evidence.

## Related
[[TODO|D006]] | [[apps/video/README]] |
[[docs/feedback/FB-011 - Richer programmatic film direction]] |
[[docs/sessions/2026-10-07 - Pipeline film visual revision]]

[[docs/issues/Index]]
