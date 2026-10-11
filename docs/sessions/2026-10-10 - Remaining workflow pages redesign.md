---
type: session
status: completed
date: 2026-10-10
tags: [sessions, frontend, design, navigation]
---
# Remaining workflow pages redesign

## Task and scope

[[TODO]] D007. The user authorized all remaining non-home pages after the first
prepared-document page, explicitly invoking the installed apple-design skill.
Solo work. No homepage component/style edits, commits, pushes, deployments,
migrations or live source/model requests.

## Changes

All non-home routes share WorkflowShell: homepage logo/background/display font,
glass toolbar, active home/sample/activity/settings navigation, new-document
shortcut and privacy/service footer. Route transitions focus main and reset
scroll; section anchors retain the current private view. Brief route/press/detail
feedback honors reduced motion; toolbar supports reduced transparency.

Results use the three-step workflow and overview/findings/source-checks/graph/
report shortcuts. Selected findings focus and bring stored evidence into view;
the keyboard graph equivalent and saved Markdown/HTML exports remain intact.
Loading/unavailable states offer recovery. Sample expectations have themed filing,
scenario and evidence sections with keyboard focus after selection. Activity
uses saved status instead of a fixed not-run label (BUG-018), expiry and refresh.
Settings distinguish unavailable capabilities from disabled services and expose
actual limits. The new privacy/limits page explains current tab ownership,
masking/retention and development limits without changing backend behavior.
Missing-page and fatal states offer home/reload recovery.

## Verification

- 30 frontend tests pass; typecheck, lint and final production build pass.
  The existing large-bundle warning remains; this does not satisfy T055.
- Eight desktop/mobile browser cases pass across separate fresh disposable API/
  frontend runs, preserving session quotas and the user's preview:
  public-page design 2/2 (17.3s), private intake 2/2 (40.4s), saved results 2/2
  (30.5s), offline curated acceptance 2/2 (30.9s).
- Public checks cover real capability recovery after an intercepted failure,
  current nav, route focus, sample keyboard selection, fingerprints, privacy/
  not-found recovery, normal/reduced-motion styles and 320/768/1440 widths.
- Intake covers text/PDF/demo, original spans, reload, outsider denial, Activity,
  delete, malformed-PDF fallback and extraction details. Its initial run stopped
  at an ambiguous New document test locator after adding the persistent header
  shortcut; scoped main-action locator passes without removing either action.
- Results compare saved categories, evidence/hashes/spans and graph equivalents,
  test section shortcuts, masked exports/HTML escaping, owner denial, deletion
  and actual `partial` Activity status. Curated journey covers fresh execution,
  results gating, source/quote outcomes, export and demo reset with model off.
- Screenshot review: desktop/mobile settings/sample, desktop empty/saved Activity,
  mobile privacy, desktop not-found and desktop/mobile results top. Browser width
  assertions cover both private results and public responsive layouts. Artifacts:
  `.runtime/playwright-workflow-{public,results,intake}` and
  `.runtime/playwright-curated`. These are ignored local evidence, not vault assets.
- Diff whitespace check passes. Frontend preview 5174 is reachable. No backend
  suite rerun for this frontend-only change; no full screen-reader/contrast audit,
  physical-device performance, live model acceptance or hosted checks performed.

## Blockers and next step

D007's local implementation/check criteria pass. User visual feedback may refine
the design; no unmeasured aesthetic approval is claimed. Continue separate T050
accessibility, T055 performance and remaining acceptance/release gates according
to [[TODO]]. T052 genuine-model acceptance still has its recorded free-tier gate.
Local review starts at `http://127.0.0.1:5174/`; sample/activity/settings/privacy
are direct routes, while private document/results access belongs to the current
tab. Reports and graphs are integrated in results, not unfinished standalone pages.

## Related

[[docs/sessions/Index]] | [[TODO]] | [[docs/product/UI direction]] |
[[docs/feedback/FB-012 - Match workflow pages to homepage theme]] |
[[apps/web/src/components/layout/README]] | [[apps/web/src/app/README]] |
[[apps/web/src/features/intake/README]] | [[apps/web/src/features/analyses/README]] |
[[apps/web/src/features/reports/README]] | [[tests/e2e/README]] |
[[docs/issues/BUG-018 - Activity labels completed reviews as not run]]
