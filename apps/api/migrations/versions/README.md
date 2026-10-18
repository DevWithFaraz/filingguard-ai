# Migration versions

T010 initializes Alembic configuration and adds the first schema revision. Do not
use runtime `create_all` instead of migrations in deployments. Verify upgrades on
a fresh database and the previous revision. Current linear head is
`0004_citation_extraction`: 0001 creates scoped analysis/evidence tables, 0002 adds
opaque file references, 0003 adds anonymous session hashes and document snapshots,
and 0004 adds independent citation extraction provenance. Upgrades/downgrades and
PostgreSQL offline SQL are covered by the migration controls. Hosted application
is deliberate, never performed by startup or readiness. The October 11 Neon
read-only preflight found an empty public schema. After target confirmation and
explicit user approval, the production Neon database was upgraded transactionally
to `0004_citation_extraction`. All 10 application tables and column sets match;
independent read-only revision verification passes. See [[docs/delivery/Deployment guide]] and
[[docs/sessions/2026-10-11 - Closed intake hosted checks]].
