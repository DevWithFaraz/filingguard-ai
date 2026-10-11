# Project utilities

Place cross-project development/release helpers here as needed. API-specific
OpenAPI export is under `apps/api/scripts`. Do not store credentials in scripts.

`api.mjs` runs uv in the backend directory with an ignored project-local cache.
Root npm commands use it so they do not depend on the user's global cache state.
`setup:api` uses the committed lockfile; running checks must not update dependencies.
The wrapper creates the ignored backend runtime directory before launching uv,
so pytest's configured temporary parent exists on a fresh checkout.

`export_browser_notices.mjs` preserves license files from the installed browser
dependency closure in the public notice artifact. `export_api_notices.py` preserves
installed Python dependency metadata and license files. Both operate locally with
no provider calls. Run after locked installs and review outputs; see
[[docs/delivery/Third-party notices]].
