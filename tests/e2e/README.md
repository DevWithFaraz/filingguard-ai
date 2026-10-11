# End-to-end acceptance

Curated source acceptance uses a separate fresh preview/config, preserving normal
session quotas and separating genuine provider calls from offline CI:

```powershell
npm exec --workspace @filingguard/web -- playwright test --config playwright.curated.config.ts
```

This desktop/mobile run verifies eleven SRS 18.2 controls with semantic review
disabled. Explicit `$env:FILINGGUARD_LIVE_DEMO='1'` enables one desktop journey
using the configured free-credit model and at most five attempts per analysis.
October 11's final genuine-model journey passes all twelve controls with three
actual requests, independent verdicts and exact bound evidence. The test compares
the four normal proposition expectations; forced outage scenarios are separate
worker controls. Earlier throttling failures remain historical evidence. Do not
use repeated live runs as automatic retries. Remove the flag before offline runs.
See [[docs/sessions/2026-10-11 - Accessibility performance and release gates]].

T007 configures Playwright; T052 exercises sample -> intake -> progress -> findings
-> graph -> evidence -> report. Test keyboard flow, desktop/mobile layout, provider
failure and two-session isolation. Use deterministic demo fixtures for CI. Run a
separate deployed live smoke test before submission.

Implemented shell checks in shell.spec.ts cover live health, disabled intake,
keyboard skip navigation, routes, desktop/mobile width, failure and retry.
Playwright starts local API/UI processes and stops those it owns after testing.
`intake.spec.ts` covers private text/PDF preparation, original Unicode spans,
masked findings, reload, owner isolation, activity, deletion, malformed PDFs and
synthetic demo admission. `results.spec.ts` follows a local review through two
findings and masked stored evidence to authenticated Markdown/HTML export. It
compares category values and the equivalent graph list against saved API results,
checks keyboard activation, status announcements, width, download names, escaped
HTML, owner isolation and deletion. Desktop/mobile screenshots are retained under
the ignored `.runtime/playwright-results` directory.

These tests run disposable local synthetic filings with external engines disabled.
They verify application behavior, not live provider classifications or the full
SRS legal demo acceptance. Provider/worker failure cases live in API integration
tests; deployed source verification and physical-device/assistive-technology
acceptance remain separate gates.

The private preview retains the production guard: session issuance allows five
requests per peer per minute. Running intake and results journeys together can
exceed that allowance because isolation checks create additional browser sessions.
Use separate fresh preview runs for `results.spec.ts` and
`intake.spec.ts shell.spec.ts`; do not relax the guard for acceptance tests.
On October 10 the combined run passed 11/12 cases; mobile results preparation
received the expected 429 at session issuance after earlier isolation scenarios.
This is not a successful combined run. The results-only rerun passed both cases
in 35.4 seconds with the unchanged guard. Playwright recreates its output folder
on each run; final screenshots were preserved in `.runtime/review-ui-2026-10-10`.
The final separate intake/shell run passed all ten cases in one minute. In total,
twelve scoped browser cases passed across these two isolated runs. Both desktop
and mobile saved-result layouts and graphs were inspected with no horizontal
overflow. Neither command establishes full legal acceptance or physical-device
performance. The earlier stale UI-copy assertions now match the current disabled
Prepare document button and explicit disabled semantic-review stage.

## Workflow redesign checks

October 11 release CI: `npm run test:e2e` runs only shell/home/film/evidence-motion
checks. Its private preview uses fresh 8002/5175 servers, preserving the user's
8001/5174 preview. It also owns fresh shell servers on 8000/5173; occupied test
ports fail rather than reusing another session. Intake/results/public/accessibility/
performance journeys run as five separate invocations of the workflow config.
CI executes each with fresh servers/rate buckets, without provider credentials
or relaxing production admission limits. The genuine-model curated config remains
separate and opt-in. All browser failure artifacts are included in CI uploads.

`playwright.workflow.config.ts` starts fresh disposable servers on 8002/5175,
preserving the review preview on 8001/5174. Run separate invocations with
`FILINGGUARD_WORKFLOW_SUITE=public`, `results`, then `intake` (default public).
Each invocation recreates its own session/rate buckets; production guards remain
unchanged. Public-page checks cover service unavailable/retry, current nav,
route focus, sample selection/evidence, details, privacy/not-found recovery,
normal/reduced motion and 320/768/1440 widths. Results verifies section anchors
and actual saved status in Activity alongside evidence/graph/export/ownership.
The original private test base URL remains 5174 unless this config sets the
explicit `FILINGGUARD_E2E_BASE_URL` override. Artifacts are retained under
`.runtime/playwright-workflow-{public,results,intake}`.

The `accessibility` suite follows sequential Tab/Enter/Space navigation through
preparation, results, evidence, graph list, export, Activity and reset, and runs
WCAG-tagged axe scans across normal/empty/error routes. It verifies accessible
semantics, not physical NVDA/VoiceOver behavior. The `performance` suite measures
three model-disabled reviews per desktop/mobile project and a separate maximum
text-input journey. Maximum PDF/over-limit checks use the actual extraction worker
via `apps/api/scripts/verify_input_limits.py`. Live timing is retained by the
separate explicitly opted-in curated run. Each suite writes a JSON receipt under
`.runtime/workflow-{suite}-results.json`; curated output is `.runtime/curated-results.json`.
These reports include bounded attachments and are ignored local artifacts.
