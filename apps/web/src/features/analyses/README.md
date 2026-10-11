# analyses

P0: saved dashboard, score/coverage, findings, evidence and graph. T046-T050.

`ResultsView.tsx` loads saved owner-scoped results through `lib/api/results.ts`,
sharing the intake bearer/session transport. It shows incomplete coverage and
unknown/provisional scores before findings, sorts critical findings first and
offers category/severity filters. Category signals use saved backend values and
coverage; unrun categories remain Unknown. The evidence detail panel loads stored excerpts,
source links, snapshot identity, Unicode offsets, method and model/prompt versions.
Source URLs are limited to credential-free HTTP(S); text renders through React.

React Flow consumes persisted graph nodes/relationships. It bounds the visual view
to the first 200 nodes and explicitly announces clipping; a keyboard accessible
list exposes every stored node and outgoing relationship. Only backend-provided
`finding_ids` connect graph selection to findings. There are no invented graph
relations, legal classifications or frontend score calculations.

Saved quotation results retain closest passages and string similarity as a signal
separate from legal support or equivalent meaning. Authenticated Markdown/HTML
report downloads request the saved backend report; no new classification runs.
Query data has zero cache retention after unmount and is not persisted to browser
storage. The prepared-document screen owns running-review progress and reruns.

Responsive scoped styles include visible focus, text status labels and reduced
motion. Unit tests in `results.test.tsx` exercise partial/unknown states, filters,
evidence lineage, graph/list selection, quote uncertainty, failed-query recovery,
saved report requests, category coverage and invalid response guards. Ten focused
component tests, TypeScript and scoped ESLint pass locally October 10. All 30 frontend
tests, full ESLint and production build also pass. The final desktop/mobile local
browser journey passed masked evidence, two findings, keyboard activation, saved
category/coverage agreement, graph/list node/status/relationship agreement,
authenticated exports, owner isolation and deletion (two cases in 35.4 seconds).
Both layouts and graph screenshots were inspected, with no horizontal overflow.
The separate intake/shell desktop/mobile regression passed all ten cases in one
minute. See [[tests/e2e/README]] for preview session quotas and run boundaries.
This synthetic local path does not verify live providers,
legal classification quality, physical devices or complete screen-reader operation.
React Flow is mocked in component tests.

Related: [[TODO]], [[apps/api/src/filingguard/modules/analyses/README]],
[[apps/web/src/features/reports/README]].

## D007 workflow redesign

Saved results share the homepage assets and WorkflowShell. The three-step path
returns to preparation/progress; section shortcuts target overview, findings,
source outcomes, relationships and report export. Loading/unavailable states
share the same design and recovery routes. Findings use a responsive list/detail
split; selection focuses and brings stored evidence into view, including graph
and deduction selections. Severity semantics, original spans, unknown signals,
limitations, saved values and authenticated reports are preserved. The keyboard
graph list remains equivalent to the visual graph. No new classifications or
provider requests are added by navigation/export. See
[[docs/sessions/2026-10-10 - Remaining workflow pages redesign]].
