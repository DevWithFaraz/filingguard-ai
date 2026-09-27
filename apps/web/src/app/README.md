# App composition

Own the router, query provider, global error boundary and app shell. Planned routes:
`/` intake, `/analyses/:id` progress/results, `/analyses/:id/graph` and
`/analyses/:id/report`. Keep business decisions in backend modules. Entry points
and screens started in T006. The shell now has Review, Activity and Settings
routes, a global error boundary and a TanStack Query health check (30-second
refresh, bounded request timeout). Only liveness is connected; intake is disabled.
Results/graph/report routes remain planned, not implemented.
