# Migration versions

T010 initializes Alembic configuration and adds the first schema revision. Do not
use runtime `create_all` instead of migrations in deployments. Verify upgrades on
a fresh database and the previous revision. There are no migrations to run yet.
