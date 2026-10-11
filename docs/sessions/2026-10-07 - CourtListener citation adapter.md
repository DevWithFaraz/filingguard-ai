---
type: session
status: completed-locally
date: 2026-10-07
tags: [sessions, citations, courtlistener, providers]
---
# CourtListener citation adapter

## Task and scope
[[TODO|T033]]. Implement the CourtListener adapter with token handling, normalized identities and bounded error mapping. Return verified/not-found/invalid/ambiguous/unavailable separately. Ensure timeout/429/5xx never becomes not-found. All work remains strictly local, with no commit or push.

## Changes
- **Schemas:** Authored `CourtListenerCluster` and `CourtListenerLookupResult` in `apps/api/src/filingguard/integrations/courtlistener/schemas.py`, including limitation constants explaining database coverage and ambiguity review requirements.
- **Adapter:** Created `CourtListenerAdapter` in `apps/api/src/filingguard/integrations/courtlistener/adapter.py` over `BoundedProviderClient`:
  - Token handling: accepts token or resolves from `Settings().courtlistener_api_token`. Validates token boundaries and non-printable characters. Missing/blank tokens return `CitationStatus.UNAVAILABLE` with `reason="missing_token"`. Token is redacted from `repr()` and result records.
  - Query normalization: input validated up to 500 characters; whitespace trimmed; malformed/empty input returns `CitationStatus.INVALID`.
  - Normalized identities: maps CourtListener cluster to `CourtListenerCluster` with ID, case name, normalized citation, court code, year extracted from filing date, opinion references, and canonical source URL.
  - Bounded error mapping: HTTP 200 with 1 cluster -> `verified`; HTTP 200 with >1 cluster or HTTP 300 -> `ambiguous`; HTTP 400 -> `invalid`; HTTP 404 or empty clusters/results -> `not_found`.
  - Invariant preservation: timeouts, 429 rate limits, 5xx server errors, connection drops, budget exhaustion, and deadlines map to `unavailable` and never collapse into `not_found`.
- **Settings:** Added `courtlistener_api_token` optional field to `Settings` in `apps/api/src/filingguard/core/config.py`.
- **Test isolation:** Added `cache_dir = ".runtime/pytest_cache"` and `addopts = "--basetemp=.runtime/pytest_temp"` to `apps/api/pyproject.toml` to prevent Windows permission conflicts on OS temporary directories.
- **Module documentation:** Updated `apps/api/src/filingguard/integrations/courtlistener/README.md`.

## Verification
- **Unit test suite:** 23 tests in `apps/api/tests/unit/test_courtlistener_adapter.py` pass in 0.12s via `httpx.MockTransport`, verifying single-cluster resolution, multiple-cluster ambiguity, status 300 ambiguity, status 400 invalidity, status 404 not-found, empty clusters, network timeout, rate limiting (429), server errors (500/502/503/504), connection errors, budget exhaustion, deadline expiration, missing tokens, token redaction, input bounds, and context manager lifecycle.
- **Code standards:** `node scripts/api.mjs run ruff check .` passed with zero errors across the backend.
- **Provider spending:** Zero live API requests made or credits spent during testing.
- **Checks not run:** Live network requests against `courtlistener.com` were not run during this task (mock transport used); opinion retrieval belongs to T034; database persistence of authorities belongs to T034/T035.

## Blockers and next step
No blockers. T033 is verified locally. Next task is T034: retrieve opinion text and metadata for resolved authorities.

## Related
[[apps/api/src/filingguard/integrations/courtlistener/README]] |
[[apps/api/src/filingguard/integrations/providers/README]] |
[[apps/api/src/filingguard/modules/citations/README]] |
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]] |
[[docs/sessions/Index]] | [[TODO]]
