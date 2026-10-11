---
type: session
status: active
date: 2026-10-06
tags: [sessions, design, motion, video]
---
# Programmatic video planning handoff

## Task and scope
D006 programmatic pipeline film design and planning.
The user requested a code-driven motion graphics video showcasing the FilingGuard AI
pipeline (upload, parsing, CourtListener verification, quote forensics, proposition
support, privacy/rules, Claim-Authority Graph, integrity score, and brand reveal).
The user explicitly paused execution to plan and instructed:
> "im still planning so record each and everything in the docs even these questions ...
> i will return and say programmatic video and ai have to continue and ask me these
> questions again (record that too in docs)"

## Recorded Context and Resumption Instruction
When the user returns and says:
`programmatic video`
The AI must continue this task by re-presenting the **6 Design Questions** recorded
in [[docs/feedback/FB-009 - Programmatic pipeline film]] so the user can choose their
preferred configuration.

## The 6 Questions to Re-Ask Upon Resumption:
1. **Video Length & Aspect Ratio**:
   - A: ~26-second 16:9 widescreen loop (~2.5–3s per stage) [Recommended]
   - B: 15-second fast cut
   - C: 16:9 widescreen + 9:16 vertical cut for social
2. **Website Delivery Method**:
   - A: Pre-rendered video file (`.mp4`/`.webm`) with `<video muted loop playsinline>` + pause button + poster [Recommended]
   - B: Live `@remotion/player` vector component in browser DOM
3. **Placement on Home Page**:
   - A: Below the hero fold in "How It Works" (preserves composer accessibility) [Recommended]
   - B: Directly in hero viewport beside the composer
4. **Audio & Sound**:
   - A: Silent motion graphics loop [Recommended for web]
   - B: UI sound effects & synth bed
   - C: Full AI voiceover narration
5. **Logo & Typography**:
   - Logo: High-res transparent PNG (`filingguard-logo.png`) vs SVG vector
   - Fonts: `Inter` + `JetBrains Mono` vs applying `GC Avalance` to display titles
6. **Safety & Disclaimers**:
   - Replace reference's "ASSURANCE GRANTED · 98%" with **"READY FOR HUMAN REVIEW"** (with 0–100 score & category breakdown), complying with SRS §15.3 and [[design]].

## Changes made so far:
- Recorded [[docs/feedback/FB-009 - Programmatic pipeline film]] and [[docs/decisions/ADR-010 - Remotion pipeline film]].
- Added task D006 to [[TODO]].
- Registered `@filingguard/video` workspace in root `package.json`.
- Created harness specifications in `apps/video/brief/BRAND.md` and `STYLE.md`.
- Drafted brand constants, timeline curves, and shared UI in `apps/video/src/`.
- Drafted beat scene components in `apps/video/src/scenes/`.

## Checks run / not run
- Run: npm install for `@filingguard/video`, asset copying, directory creation.
- Not run: video rendering, still snapshot exports, homepage video embed, browser tests.
- Execution is intentionally held at the planning phase per user instruction.

## Next step
Awaiting user message containing `programmatic video`. Upon receiving it, re-ask the
6 questions and proceed according to the user's choices.

## Related
[[docs/feedback/FB-009 - Programmatic pipeline film]],
[[docs/decisions/ADR-010 - Remotion pipeline film]],
[[apps/video/README]],
[[TODO]],
[[Home]].
