---
type: session
status: completed-locally
date: 2026-10-07
tags: [sessions, citations, courtlistener, authorities, provenance]
---
# Opinion text retrieval and authority persistence

## Task and scope
[[TODO|T034]]. Retrieve opinion text and metadata for resolved authorities, preserving provenance and distinguishing missing text. Done when name, court, year, citation, source URL, and available source passages appear in stored results, and missing text is distinguished. All work remains strictly local, with no git commit or push.

## Changes
- **Schemas:** Authored `CourtListenerOpinion` and `CourtListenerResolvedAuthority` in `apps/api/src/filingguard/integrations/courtlistener/schemas.py`, recording cluster/opinion IDs, opinion type, text fields, conversion methods, content SHA-256 digests, availability flags, missing text indicators, and source metadata.
- **HTML parsing & text extraction:**
  - Implemented `OpinionTextParser(HTMLParser)` and `clean_opinion_html(html_content)` in `adapter.py` that strips `<script>` and `<style>` blocks and tags, unescapes HTML entities, and maps block tags (`p`, `div`, `br`, headings, `li`) into line breaks (`htmlparser-block-boundaries-v1`).
  - Text extraction priority hierarchy: `plain_text` (`identity-v1`), `html_with_citations`, `html`, `html_lawbox`, `html_columbia`, `xml_harvard`.
  - When text is present, computed 64-character SHA-256 hash satisfying database check constraints.
- **Opinion selection & dissent rejection ([[docs/issues/BUG-004 - First opinion reference can be a dissent|BUG-004]]):**
  - Implemented `resolve_cluster_opinion` in `CourtListenerAdapter`: orders candidate opinions (cluster ID first, followed by sorted opinion IDs).
  - Prioritizes lead/majority/combined opinion types (`010combined`, `020lead`, `015unamani`, `025plurality`, `majority`).
  - Deliberately rejects dissents and concurrences (`040dissent`, `030concurrence`, `035concurrence_in_part`) as holding sources. Fails closed (`None`) if only dissents exist.
- **Authority resolution:**
  - Added `get_opinion`, `resolve_authority`, and `verify_and_resolve` to `CourtListenerAdapter`.
  - Distinguishes missing text: sets `opinion_text_available = False`, `opinion_text = None`, `source_sha256 = None`, and `source_metadata["missing_text"] = True` with reason (`opinion_text_empty`, `dissent_or_concurrence_only`, `no_opinions_in_cluster`).
  - Captures full provenance: `cluster_id`, `opinion_id`, `provider_opinion_type`, `text_field`, `text_conversion`, `raw_sha256`, `characters`, and `attribution`.
- **Database & service integration:**
  - Added `create_authority_record(analysis_id, resolved)` in `apps/api/src/filingguard/modules/citations/service.py` to construct persistent `Authority` models.
  - Added `SafeAuthority` contract and updated `SafeCitation` (`authority_id`, `authority`) and `SafeCitationsResponse` (`authorities`) in `apps/api/src/filingguard/api/contracts.py`.
  - Updated `GET /api/v1/analyses/{analysis_id}/citations` in `apps/api/src/filingguard/api/routes/intake.py` to return stored authorities and link each citation to its resolved authority.
  - Exported updated OpenAPI specification to `contracts/openapi.json` and generated browser types in `apps/web/src/lib/api/schema.d.ts`.
- **Documentation:** Updated `TODO.md` (marked T034 complete) and `apps/api/src/filingguard/integrations/courtlistener/README.md`.

## Verification
- **Unit test suite:** 33 tests in `apps/api/tests/unit/test_courtlistener_adapter.py` pass in 0.74s via `httpx.MockTransport`, verifying HTML stripping, plain text and HTML opinion extraction, missing text distinction, network failure propagation without misclassification, BUG-004 lead opinion prioritization over dissents, dissent-only cluster fail-closed behavior, authority resolution fields/provenance, and verify-and-resolve end-to-end flow.
- **Integration test suite:** 17 tests in `apps/api/tests/integration/test_citation_pipeline.py` pass in 35s, including new tests verifying that stored `Authority` entities round-trip through the database, link to `Citation` records, and return complete authority details and missing text distinction in `GET /api/v1/analyses/{id}/citations`.
- **Full unit suite:** 390 passed, 2 skipped across all backend unit tests.
- **Frontend test suite:** 20 tests in `apps/web` pass via Vitest.
- **Typecheck & lint:** `tsc --noEmit` and `ruff check .` pass with zero errors.
- **Zero provider spending:** All tests use mock transport or offline fixtures; zero live API credits spent.
- **Checks not run:** Live network requests against `courtlistener.com` were not run (mock transport used); outbound lookup deduplication across filing repeats belongs to T035.

## Blockers and next step
No blockers. T034 is verified locally. Next task is T035: deduplicate outbound lookups while retaining all filing occurrences and caching public source responses within an analysis.

## Related
[[TODO]] |
[[apps/api/src/filingguard/integrations/courtlistener/README]] |
[[apps/api/src/filingguard/modules/citations/README]] |
[[docs/issues/BUG-004 - First opinion reference can be a dissent]] |
[[docs/sessions/2026-10-07 - CourtListener citation adapter]] |
[[docs/sessions/Index]]
