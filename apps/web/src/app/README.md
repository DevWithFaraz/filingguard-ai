# App composition

Own the router, query provider, global error boundary and app shell. Planned routes:
`/` intake, `/analyses/:id` progress/results, `/analyses/:id/graph` and
`/analyses/:id/report`. Keep business decisions in backend modules. Entry points
and screens started in T006. The shell now has Review, Activity and Settings
routes, a global error boundary and a TanStack Query health check (30-second
refresh, bounded request timeout). Only liveness is connected; intake is disabled.
Results/graph/report routes remain planned, not implemented.

October 10, 2026 update: the earlier scaffold status above is historical.
Private preparation and saved results/graph/report inspection are implemented
locally. `/analyses/:id` now renders its own scoped document workspace shell
for D007's first-page review; other non-home routes retain the existing shell.
The dedicated branch must remain inside a matching `Route` so `useParams`
receives the analysis ID. `/` still renders the unchanged homepage.
See [[apps/web/src/features/intake/README]], [[apps/web/src/features/analyses/README]],
[[docs/sessions/2026-10-10 - Document workspace redesign]].

Later October 10 update: `WorkflowShell` now surrounds all non-home matched
routes, including prepared documents. The dedicated first-page branch has been
removed to avoid duplicate shells. `WorkspaceInfo.tsx` owns server-reflecting
settings and privacy/limits; unknown capabilities remain unknown with retry.
Not-found and fatal states offer recovery paths. Results keep graph and report
inspection integrated rather than inventing unfinished standalone routes.
Route navigation focuses main; in-page anchors preserve the current private view.
See [[docs/sessions/2026-10-10 - Remaining workflow pages redesign]].
