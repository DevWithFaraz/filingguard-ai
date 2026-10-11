---
type: issue
status: resolved
date: 2026-10-10
tags: [issues, frontend, activity]
---
# Activity labels completed reviews as not run

## Symptom and reproduction

Prepare and run a synthetic review, then open Activity. The previous component
rendered `Prepared | Legal analysis not run` for every document, including a
saved partial or completed attempt. This contradicted the server status and
made workflow navigation misleading.

## Evidence and cause

`ActivityView.tsx` used a fixed text span and ignored the validated summary's
`execution_status`. The public transport already returns that saved status;
no new API or classification is needed.

## Fix and regression check

Activity now shows the saved status, using `Prepared · checks not run` only for
`not_run`. The final desktop/mobile `results.spec.ts` journey runs a real local
synthetic review, opens Activity and asserts `partial` with no old not-run label.
Both cases pass, with saved-status screenshots in
`.runtime/playwright-workflow-results/*/activity-saved.png`.

## Related

[[docs/issues/Index]] | [[TODO]] D007 |
[[apps/web/src/features/intake/README]] |
[[docs/sessions/2026-10-10 - Remaining workflow pages redesign]]
