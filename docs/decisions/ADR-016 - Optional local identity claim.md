---
type: decision
status: accepted
date: 2026-10-19
tags: [decisions, security, identity, t208]
---
# ADR-016 - Optional local identity claim

## Context
T208 asks for authentication, saved matters/history and production authorization.
The bounded slice needs a way to recover the current anonymous `owner_hash` after
the tab bearer is stored under a local identity, without OAuth, email, cookies
across hosts, or changing default anonymous intake.

Anonymous ownership remains SHA-256 of a 256-bit tab bearer persisted only as
`AnonymousSession.owner_hash`. Analyses are keyed by that hash. A new random
login token cannot be hashed into the original owner unless lookup is added.

## Decision and alternatives
Keep anonymous issuance as the default. Add optional `local_identities` that bind
a unique lowercase username and PBKDF2-SHA256 secret hash to the caller's current
`owner_hash`. Login issues a separate opaque bearer whose SHA-256 is stored in
`identity_sessions` and resolved to the claimed owner. CORS stays credential-less
(`allow_credentials=False`); tokens stay in `Authorization: Bearer`.

Rejected:
- httpOnly cookies: ADR-007 disables credentialed CORS and ambient cross-host cookies.
- Replacing `owner_hash` derivation for anonymous tokens: would break existing sessions.
- Storing the raw tab token under the identity: contradicts “persist only SHA-256”.
- OAuth/email/matters: out of this slice.

## Consequences
Recovery works only while the analysis retention window is live. Identity login
does not extend analysis expiry, create matters, or share access. Local Alembic
`0007_local_identities` is SQLite-first; hosted Neon stays at `0004` until an
explicit production migration is approved. Token theft still shares the owner.

## Evidence and verification
Local integration tests cover anonymous use without claiming, claim-then-login
listing, cross-identity 404, and invalid/expired identity bearers (401 at the
intake guard, matching existing session expiry). Hosted migration and UI storage
of the recovery token are not done.

## Related
[[TODO]] T208 · [[apps/api/src/filingguard/modules/identity/README]] ·
[[docs/decisions/ADR-007 - Private preparation boundary]]

[[docs/decisions/Index]]
