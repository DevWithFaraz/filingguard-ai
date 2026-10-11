# intake

P0: paste/PDF/sample input, court selection, AI-used input and validation. T019.

Status: private document preparation implemented behind backend opt-in. T016 DemoReview loads the fixed reviewed
sample with explicit demo mode, not_run execution and delegated AI review. It renders
all 18 expectations, selected filing/source excerpts, snapshot fingerprints and
review conditions. Reset unmounts selection and its transient query; no analysis
or private document is created/deleted. Network/contract errors show unavailable
and expose retry, never cached favorable results. Actual browser transport is tested
on desktop/mobile. It remains distinct from creating a private demo document.

IntakeComposer provides Text/PDF/Demo modes, display-only document names, client
feedback (server limits remain authoritative), AI-used metadata, preparation/busy/
fallback states. Court metadata is explicitly unconfigured for live input or
synthetic for demo; no verified real-court profile is configured. Demo permits
selection of the synthetic/unconfigured court and AI-use flag. Exact curated
samples execute freshly computed citation/claim/quote checks using cached public
opinions; configured model review remains separate. PreparedView labels this
source mode and offers Reset demo, which deletes the private analysis/output.
PreparedView displays extraction/page warnings and exact paragraph spans; it hides
expired content, polls stage status every second while active (backing off on
errors and stopping on terminal/unmount), shows masked findings, provides a fresh
attempt for terminal live reviews, displays the saved execution status and supports confirmation before
owner-scoped deletion. Activity
loads summaries only. No filing text is saved in local/sessionStorage.

`lib/api/intake.ts` issues a lazy anonymous tab session and stores only bearer/expiry
in sessionStorage. Requests use no-store, omit cookies, abort on navigation/timeout,
and do not retry POST automatically. 401 clears the invalid token. Private query
data is transient, with gcTime=0 after unmount. PDF filenames are encoded headers,
not URL parameters. This requires XSS controls and HTTPS at deployment; tab cloning
or copying a bearer can share access, so this is not an account/device identity.

Real desktop/mobile Playwright checks cover text/PDF/demo, reload, isolation,
fallback, Activity and deletion against disposable local SQLite. The first supplied
background/Avalance/GSAP homepage is implemented locally, with IntakeComposer
embedded in [[apps/web/src/features/home/README]]. Reviewed samples use `/demo`;
reset returns home and unmounts transient sample state. The private execution/reset
journey is distinct from this read-only expectation preview. Provider outages and
throttling retain explicit unavailability without cached expected verdicts.
See [[README]], [[docs/product/UI direction]],
[[docs/decisions/ADR-007 - Private preparation boundary]].

Keep the feature's components, query hooks and tests here.
Use shared API types/client from src/lib/api. Display backend statuses faithfully;
do not duplicate legal analysis or scoring logic in the browser.

## D007 first-page redesign (October 10, 2026)

`PreparedView` now owns a dedicated document shell and scoped `prepared.css`.
The router supplies the matched analysis ID outside the older sidebar shell.
Homepage logo, background and display font carry into glass navigation and the
purple hero; homepage components/styles are unchanged. Prepare/review/results
steps, home/activity/settings links and document/check anchors provide wayfinding.
The next-action card follows actual server status: start, active progress, then
terminal results; results are not offered before the attempt ends. Preparation
details and masked findings expand on demand. Extraction, expiry, warnings,
retry, fresh live attempt, ownership and delete/reset behavior remain intact.
Arrival/press feedback respects reduced motion; the toolbar supports reduced
transparency. This is one page for aesthetic review, not a completed all-page
redesign or full accessibility audit. See [[docs/sessions/2026-10-10 - Document workspace redesign]].

## D007 continuation

The earlier dedicated shell is now extracted to shared `WorkflowShell`, mounted
by App around all non-home routes. PreparedView keeps its reviewed layout and
private behavior. Activity uses the saved `execution_status` instead of a fixed
not-run label, with paragraph count, expiry, refresh and preparation shortcut.
Capability failures remain unavailable instead of claiming an empty successful
session. DemoReview shares the hero/card language and moves keyboard focus to
selected evidence with a brief motion-respecting reveal. Expectations remain
distinct from freshly executed demo findings. See
[[docs/sessions/2026-10-10 - Remaining workflow pages redesign]],
[[docs/issues/BUG-018 - Activity labels completed reviews as not run]].

T050 audit (October 11): the prepared paragraph preview is a named keyboard focus
target so arrow/PageDown scrolling works without a mouse. Small labels now meet
the measured contrast check. Desktop/mobile sequential keyboard execution,
evidence selection, graph list, export, Activity and reset pass alongside
WCAG-tagged axe scans of loading/terminal/public/empty/error semantics. Physical
screen-reader/device testing remains separate. See
[[docs/issues/BUG-019 - Low contrast labels and inaccessible document scroll]].
