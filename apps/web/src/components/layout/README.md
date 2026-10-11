# Layout

Shared navigation, content frame and responsive evidence split panes belong here.
Keep dense review workflows readable on desktop and mobile without nested cards.

`WorkflowShell` now owns every non-home route: shared brand/glass toolbar, current
navigation, new-document shortcut, privacy/limits and service connection footer.
On route changes it resets scroll and focuses main; hash navigation keeps the
current screen mounted. `WorkflowHero` provides a shared page identity and next
step context. Styles are scoped under `.document-workspace`; homepage files and
styles are unchanged. Route, press, details and evidence arrival feedback honors
reduced motion; the toolbar has solid reduced-transparency support.
See [[docs/product/UI direction]], [[TODO]] D007 and
[[docs/sessions/2026-10-10 - Remaining workflow pages redesign]].
