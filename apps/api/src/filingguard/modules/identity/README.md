# identity

Optional local identity claiming for the bounded T208 slice. Anonymous tab-bearer
sessions remain the default. This is not production authentication, OAuth, email
accounts, saved matters, or multi-user collaboration.

A claim stores a unique lowercase username and a PBKDF2-SHA256 secret hash, bound
to the caller's current `owner_hash`. Analyses stay keyed by that hash. Logging in
issues a second opaque bearer whose SHA-256 is stored in `identity_sessions` and
resolved to the claimed owner. The original anonymous bearer still works until it
expires. Secrets are never stored in plaintext. CORS stays credential-less; tokens
use the existing `Authorization: Bearer` pattern, not cookies.

`POST /api/v1/identities` requires the current tab bearer. `POST /api/v1/identities/login`
requires an allowed Origin like session issuance. `GET /api/v1/identities/me` reports
the bound username or 404. Foreign owners still 404 on analysis reads. Missing or
expired bearers still 401 at the intake guard.

Local Alembic `0007_local_identities` persists the tables. Hosted Neon is not
migrated.

Related: [[TODO]] T208, [[docs/decisions/ADR-016 - Optional local identity claim]],
[[docs/decisions/ADR-007 - Private preparation boundary]],
[[apps/api/src/filingguard/db/models/README]].
