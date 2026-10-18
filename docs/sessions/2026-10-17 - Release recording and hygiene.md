---
type: session
status: verified
date: 2026-10-17
tags: [sessions, release, hygiene, verification]
---
# Release recording and hygiene

## Task and scope
User requested execution of [[TODO]] `T062` to complete release hygiene, verify
live endpoints, document known limitations and unresolved P1/P2 backlog, and record
the release commit and tag for the reproducible MVP.

## Changes
- Ran `scripts/check_hosted_release.mjs` against the live hosted services on Render
  (`https://filingguard-ai.onrender.com` and `https://filingguard-api.onrender.com`).
  Verified health (200), capabilities (200), readiness (200 with all subchecks
  verified true: `intake_enabled`, `private_storage`, `cleanup`, `exact_origins`,
  `database_schema`, `provider_configuration`), strict CORS origin enforcement (forbidden
  origin receives no allow header), and direct SPA route navigation (`/activity`, `/settings`).
- Created Git release tag `v0.1.0-mvp` anchored to deployment commit `5b379934eef192b005fe45da9b0a1dcf1f6188e4`
  and verified application release revision `325451ada388dc908b7a28c9d2b8dd8362a52338`.
- Authored [[docs/delivery/Release record - v0.1.0-mvp]] documenting release identifiers,
  live endpoints, working MVP capabilities, explicit limitations (confidential use gated
  by T212/T213, provisional scores, reference-only court rules, ephemeral free-tier limits,
  no OCR), and the unresolved P1/P2 backlog.
- Updated [[docs/delivery/README]] to link the release record.
- Checked off [[TODO]] `T062` with verified acceptance criteria and updated live status in [[Home]].

## Verification
- `node scripts/check_hosted_release.mjs` — exited 0; all 10 endpoint, readiness and CORS checks passed.
- `git tag -l -n` — verified tag `v0.1.0-mvp` pointing to `5b37993`.
- `npm test -- --run` in `apps/web` — 30 passed in 21.91s across 5 test files.
- `uv --directory apps/api run --locked pytest tests/unit/test_court_rule_source_registry.py tests/integration/test_intake.py` — 11 passed.

## Blockers and next step
No blockers for P0 release hygiene. P0 is now fully closed.
Next ordered work in [[TODO]]:
1. **Phase B (P1 Universal Review)**: Start `T102` (Rich lineage and explanations, `FR-205`, `FR-224/225`) or `T101` (Legal Red-Team Mode, `FR-240`–`FR-245`).
2. **Phase C (Court Profiles)**: Prior to `T106`, determine one specific target filing context and complete requirement matrix before activating a real court profile.
3. Real client confidential filings remain strictly gated by `T212`/`T213`.

## Related
[[TODO]] `T062`, `T102`, `T101`, `T106`, `T212`, `T213`;
[[docs/delivery/Release record - v0.1.0-mvp]];
[[docs/delivery/Deployment guide]];
[[docs/product/FilingGuard product direction]];
[[docs/sessions/2026-10-14 - Filing-centric direction and court-source foundation]].

[[docs/sessions/Index]] | [[TODO]]
