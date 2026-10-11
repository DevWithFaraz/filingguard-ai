---
type: session
status: complete
date: 2026-10-07
tags: [sessions, citations, caching, integrations]
---
# Outbound citation deduplication and response caching

## Task and scope
Implemented [[TODO|T035]] under P0 / 7 Citation verification and source retrieval.
Deduplicate outbound lookups while retaining all filing occurrences; cache public source
responses within an analysis. Done when repeats share one authority lookup and each
original location remains inspectable.

## Changes
- **Public source cache (`CourtListenerCache`):**
  Added thread-safe/dictionary cache in `filingguard.integrations.courtlistener.adapter` with whitespace normalization (`normalize_key`), tracking hits/misses, and caching:
  - Deterministic citation lookup results (`200` verified, `404` not found, `300` ambiguous, `400` invalid).
  - Retrieved opinions (`get_opinion`).
  - Resolved cluster authorities (`resolve_authority`).
- **Adapter caching (`CourtListenerAdapter`):**
  Updated `CourtListenerAdapter` to accept an optional `cache` instance or initialize its own internal cache.
  Added module-level `set_default_transport` to allow seamless test mocking without touching live provider credits.
  Lookups, opinion queries, and authority resolution automatically check the cache before issuing HTTP calls and populate the cache on deterministic outcomes.
- **Analysis-level deduplication (`verify_citations_for_analysis`):**
  In `filingguard.modules.citations.service`, implemented `verify_citations_for_analysis`:
  - Retains all `Citation` occurrence instances with their exact locations (`start_offset`, `end_offset`, `page_number`, `segment_id`, `extraction_metadata`).
  - Groups queries by normalized citation string and cluster ID.
  - Ensures repeated mentions of the same citation execute exactly one outbound lookup and one opinion retrieval.
  - Ensures all occurrences of the same case link to the identical `Authority` entity row (`UniqueConstraint("analysis_id", "source", "external_id")`).
  - Handles parallel citations pointing to the same cluster by sharing the single `Authority` row.
  - Leaves unsupported short/reference citations (`unresolved_reference`) unrun without spurious lookups.
- **Stage runner integration (`verified_citation_stage`):**
  Added `verified_citation_stage` in `filingguard.modules.citations.runner`, combining local extraction with deduplicated verification and emitting `StageResult.status == StageStatus.COMPLETED` with evaluated coverage.
- **Documentation:**
  Updated `apps/api/src/filingguard/integrations/courtlistener/README.md` and `TODO.md`.

## Verification
- **Unit tests:**
  - 42 tests in `apps/api/tests/unit/test_courtlistener_adapter.py` passed in 1.22s (including 9 new cache tests).
  - 4 tests in `apps/api/tests/unit/test_citation_dedup.py` passed in 1.97s (verifying deduplicated lookups, occurrence retention, shared authority rows, and parallel citation handling).
  - Full backend unit tests: 403 passed, 2 skipped in 30.90s.
- **Integration tests:**
  - 19 tests in `apps/api/tests/integration/test_citation_pipeline.py` passed in 100.92s (including 2 new integration tests verifying HTTP endpoint responses and database counts).
- **Frontend tests:**
  - 20 vitest tests in `apps/web` passed in 7.22s.
- **Typechecks and Linting:**
  - `tsc --noEmit` in `apps/web` passed with 0 errors.
  - `ruff check apps/api` passed with 0 errors.
- **Zero API Spend:**
  - All tests used `httpx.MockTransport`; zero live CourtListener API credits spent.
- **Checks not run:**
  - Live CourtListener network requests (pending explicit user test token / staging verification).
  - No Git push or commits made per strict user instruction ("dont push anything").

## Blockers and next step
No blockers. Next task in [[TODO]] is **T036**:
Test verified, unresolved, malformed, ambiguous, duplicate and provider failure cases.
Done when unresolved findings explicitly state database coverage limitations and never
assert that a case is fabricated merely because absent.

## Related
- [[TODO]] (T035, T036)
- [[FilingGuard_AI_SRS#9.3 Citation Verification]] (FR-040 through FR-046)
- [[docs/decisions/ADR-009 - Local citation occurrences before source verification]]
- [[docs/sessions/2026-10-07 - Opinion text retrieval and authority persistence]]
- [[apps/api/src/filingguard/integrations/courtlistener/README]]
- [[apps/api/src/filingguard/modules/citations/README]]

[[docs/sessions/Index]] | [[TODO]]
