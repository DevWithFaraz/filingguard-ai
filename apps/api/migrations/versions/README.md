# Migration versions

T010 initializes Alembic configuration and adds the first schema revision. Do not
use runtime `create_all` instead of migrations in deployments. Verify upgrades on
a fresh database and the previous revision. Current linear head is
`0007_local_identities`: 0001 creates scoped analysis/evidence tables, 0002 adds
opaque file references, 0003 adds anonymous session hashes and document snapshots,
0004 adds independent citation extraction provenance, 0005 allows
`table_of_authorities` finding types, 0006 stores claim correction history JSON
without rewriting original extraction, and 0007 adds optional local identity
records bound to an anonymous `owner_hash`. Hosted Neon remains at
`0004_citation_extraction` until an explicit upgrade is approved. Upgrades/downgrades and PostgreSQL offline
SQL are covered by the migration controls. Hosted application is deliberate, never
performed by startup or readiness. The October 11 Neon production database remains
at `0004_citation_extraction` until an explicit upgrade is approved. See
[[docs/delivery/Deployment guide]] and
[[docs/sessions/2026-10-11 - Closed intake hosted checks]].
