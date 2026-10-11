---
type: session
status: planning
date: 2026-10-06
tags: [sessions, design, motion, video]
---
# Programmatic video choices and beat plan

## Task and scope

D006 planning resumed after the user returned with "programmatic video" and
answered the six questions in
[[docs/feedback/FB-009 - Programmatic pipeline film]]. This handoff follows
[[docs/sessions/2026-10-06 - Programmatic video planning handoff]], which remains
a historical record of the earlier pause.

## Changes

Recorded 26-second widescreen, sharper rendered MP4/WebM, silent below-hero
playback and the existing PNG. Recorded the user's rejection of the three
proposed copy/disclaimer phrases. Kept Inter + JetBrains Mono as the working
default because no new font choice was supplied. No commit or push is authorized.

Updated ADR-010 and the planned motion copy. Added [[apps/video/README]] and
[[apps/video/brief/BRIEF]], [[apps/video/brief/BEATS]],
[[apps/video/brief/CRITIQUE]]. The proposed sequence totals 780 frames at 30 fps.
It uses an evidence-report beat before the brand reveal. Specified a 4K master
and smaller website derivatives with proposed size/readability budgets.
Updated Home navigation, TODO's current task/work log and the sessions index.
Linked the planned film from the canonical design, UI and stack notes so their
earlier recording direction does not diverge from the selected delivery.

## Verification

Read the core vault guidance, relevant requirements/design/module notes, fixture
provenance and current scaffold. Inspected seven scene files and shared parsing/
privacy components; found the existing 810-frame draft and superseded copy.
No root composition, entry point, rendering/encoding scripts or final media are
present in the inspected video workspace.

Documentation link targets and the proposed frame ranges/still positions were
checked locally. No scene implementation, video rendering, application tests,
frontend build or homepage browser checks were run: this update is planning only.
No live provider request, deployment, commit or push occurred.

## Blockers and next step

Configuration choices are recorded; detailed storyboard/aesthetic acceptance is
still pending. Review [[apps/video/brief/BRIEF]] and [[apps/video/brief/BEATS]]
before resuming scene work. Then align draft copy/timing, assemble the composition
and rendering harness, inspect actual stills, produce media and integrate the
homepage band. D006 stays unchecked; T033 remains the next backend task.

## Related

[[docs/feedback/FB-009 - Programmatic pipeline film]] |
[[docs/decisions/ADR-010 - Remotion pipeline film]] |
[[apps/video/README]] | [[apps/web/src/features/home/README]] |
[[docs/sessions/Index]] | [[TODO]] | [[Home]]
