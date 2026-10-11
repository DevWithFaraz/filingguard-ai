---
type: session
status: handoff
date: 2026-09-27
tags: [deployment, database]
---
# Neon connection verification

T008 in [[TODO]]. User created Render/Neon accounts, selected PostgreSQL 17 and
saved a direct Neon connection string in ignored apps/api/.env.
Added scripts/check_database.py with 15-second connection and 10-second statement
timeouts, read-only transaction, allowed Neon host/driver/TLS validation, no pooling
and sanitized metadata/errors. No URL, password or raw provider response was printed.

Verified: connection passed; PostgreSQL reported 17.11 (8a81ecb); driver confirmed
TLS active; endpoint not pooled. Backend Ruff lint passed. No schema/data changes
were made, no migrations or unit suite run in this session, and production DB
integration remains T010. Initial sandbox network check failed; approved retry
connected. An initial probe incorrectly used pg_stat_ssl to verify client TLS;
corrected to driver-side ssl_in_use. See the linked resolved issue.

Next: create Render free Python Web Service from the pushed GitHub repo, then
static frontend and exact CORS/API origins. T008 is still incomplete; no public
service or repeatable deployment has been verified. Final UI planning stays deferred.

Related: [[docs/sessions/Index]], [[docs/delivery/Deployment guide]],
[[docs/issues/BUG-003 - Proxy TLS check false negative]].
