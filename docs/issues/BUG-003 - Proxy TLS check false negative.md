---
type: issue
status: resolved
date: 2026-09-27
tags: [issues, database]
---
# Proxy TLS check false negative

Observed: the initial database probe successfully queried Neon but rejected TLS
based on pg_stat_ssl. That view describes the server-side backend connection,
not necessarily our client-to-proxy transport. A proxy-related distinction is
the likely explanation; the provider's internal connection was not investigated.

Fix: inspect psycopg's underlying PGconn.ssl_in_use for our client connection.
Preserve the required sslmode setting. Retest confirmed client TLS and a successful
read-only query; Ruff passed. No TLS requirement was disabled to pass the check.
This was a probe bug, not an observed leak or database credential failure.

[Client SSL status](https://www.postgresql.org/docs/18/libpq-status.html)
and [psycopg connection wrapper](https://www.psycopg.org/psycopg3/docs/api/connections.html).

Related: [[docs/issues/Index]], [[TODO]] (T008),
[[docs/sessions/2026-09-27 - Neon connection verification]].
