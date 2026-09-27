# Infrastructure

Compose provides local PostgreSQL only. Use the root `.env` explicitly with
`docker compose --env-file .env -f infra/compose.yaml up -d db`.

Original deployment target: Vercel/Railway. Free Render/Neon is now proposed;
see [[docs/delivery/Deployment guide]] and root render.yaml. Configure
accounts/plans, secrets, exact origins, HTTPS and migrations in T008/T057. Use one
API worker/replica while analyses run in-process; recovery must mark interrupted
work honestly. Add DB readiness separately from process liveness. Keep uploads
private and ephemeral; persist report evidence in PostgreSQL.

Frontend entry points/build and a Render deployment manifest now exist. No
cloud resource or database has been verified yet; configuration is not deployment.
