# HTTP routes

Implemented: health (liveness), readiness, capabilities, court-profile metadata,
reviewed demo preview, anonymous sessions, private text/PDF/demo preparation,
analysis status/run/rerun, saved findings/citations/results/evidence/graph/reports
and deletion. Private routes enforce origin/session ownership and no-store.
Provider requests and classifications belong to contained module runners.

`/api/v1/ready` returns 503 until intake, private storage, cleanup, exact origins,
current Alembic heads and configured credentials for enabled providers are ready.
It reads existing runtime/database state without migrating or calling providers.
Successful readiness does not certify provider availability, legal accuracy,
POSIX containment or hosted end-to-end acceptance. `/health` remains liveness.
Related: [[TODO]] T057, [[docs/delivery/Deployment guide]].
