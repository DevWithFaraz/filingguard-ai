---
type: issue
status: resolved
date: 2026-10-11
tags: [issues, accessibility]
---
# Low contrast labels and inaccessible document scroll

Desktop/mobile WCAG-tagged axe scans found small labels below 4.5:1 on the home,
prepared-document, results empty-detail and settings views. The prepared text
scroll region also lacked a keyboard focus target. These were observed failures,
not a claim that every accessibility issue can be detected automatically.

Reproduction: run the accessibility suite in
`apps/web/playwright.workflow.config.ts` with `FILINGGUARD_WORKFLOW_SUITE=accessibility`.
Original measured text ratios were 3.93–4.45:1. The scrollable paragraph list
reported `scrollable-region-focusable` on both viewports.

The fix slightly darkens the affected light-background labels, lightens the dark
scene counter, and adds a named Tab target to the prepared paragraph list.
Homepage layout, animation and art direction are preserved.

Regression evidence: both desktop and mobile complete the sequential Tab/Enter
workflow from home through preparation, execution, finding evidence, graph list,
Markdown export, Activity and reset. Scans of those states plus settings, privacy,
empty Activity, sample, not-found and sample-unavailable pass without axe violations.
Screen-reader roles/live-region semantics are checked; physical NVDA/VoiceOver
testing was not performed.

Related: [[TODO]] T050, [[apps/web/src/features/intake/README]],
[[apps/web/src/features/analyses/README]], [[apps/web/src/features/home/README]],
[[docs/sessions/2026-10-11 - Accessibility performance and release gates]],
[[docs/issues/Index]].
