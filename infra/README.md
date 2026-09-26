# Infrastructure

Compose provides local PostgreSQL only. Use the root `.env` explicitly with
`docker compose --env-file .env -f infra/compose.yaml up -d db`.

Selected deployment: Vercel static UI, Railway FastAPI and PostgreSQL. Configure
accounts/plans, secrets, exact origins, HTTPS and migrations in T008/T057. Use one
API worker/replica while analyses run in-process; recovery must mark interrupted
work honestly. Add DB readiness separately from process liveness. Keep uploads
private and ephemeral; persist report evidence in PostgreSQL.

Frontend entry points/build and production deploy config remain to be added. No
containers or cloud resources have been started/provisioned by this scaffold.
