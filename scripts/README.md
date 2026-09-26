# Project utilities

Place cross-project development/release helpers here as needed. API-specific
OpenAPI export is under `apps/api/scripts`. Do not store credentials in scripts.

`api.mjs` runs uv in the backend directory with an ignored project-local cache.
Root npm commands use it so they do not depend on the user's global cache state.
`setup:api` uses the committed lockfile; running checks must not update dependencies.
