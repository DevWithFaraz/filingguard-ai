# courtlistener adapter

Priority: P0. Tasks: T033-T036 in [[TODO]].

Citation lookup, opinion retrieval, identity mapping, timeouts/retries and provider error mapping. Record source URLs/timestamps/hashes. Distinguish not-found from unavailable. Use approved hosts rather than arbitrary URLs found in a filing.

## Implemented citation lookup (T033)

`CourtListenerAdapter` in `adapter.py` and schemas in `schemas.py` implement the bounded citation verification adapter over `BoundedProviderClient`.

- **Token handling:** Accepts a token explicitly or resolves `Settings().courtlistener_api_token`. Validates token boundaries and non-printable characters. Missing or blank token fails safely as `CitationStatus.UNAVAILABLE` with `reason="missing_token"`. Token credentials are never recorded in `repr()`, error messages, or result structures.
- **Normalized identities:** `lookup_citation(citation_text: str)` queries `POST /api/rest/v4/citation-lookup/`. When CourtListener returns an unambiguous single cluster (`status == 200` and `len(clusters) == 1`), the result is classified as `CitationStatus.VERIFIED`, populating `CourtListenerCluster` with cluster ID, case name, normalized citation, parsed court code, filing year, sub-opinion references, and canonical source URL.
- **Ambiguous and invalid classifications:** Returns `CitationStatus.AMBIGUOUS` when multiple clusters are returned (`status == 200` with multiple clusters, or `status == 300`). Returns `CitationStatus.INVALID` when CourtListener rejects syntax (`status == 400`) or input is malformed/empty.
- **Unresolved citations & database coverage:** Returns `CitationStatus.NOT_FOUND` only when CourtListener explicitly reports no records (`status == 404`, `status == 200` with 0 clusters, or empty citation array). Includes explicit limitation stating that absence in CourtListener coverage does not conclusively prove fabrication.
- **Bounded error mapping (Critical invariant):** Network timeouts (`timeout`), rate limits (`rate_limited` / 429), server errors (`http_failure` / 5xx), connection drops (`network_failure`), deadline exceeded (`deadline_exceeded`), and budget exhaustion (`request_budget_exhausted`) are mapped directly to `CitationStatus.UNAVAILABLE`. They **never** collapse into `not_found`.
- **Budgets and retries:** Uses `ProviderBudget` and `ProviderPolicy` (at most 1 retry for selected transient failures, 20s timeout, max 2 concurrent requests, max 128 KiB request and 4 MiB response).
- **Testing:** 23 unit tests in `tests/unit/test_courtlistener_adapter.py` verify all statuses, error mappings, secret redaction, and context manager lifecycle without spending live API credits.

## Implemented opinion text and authority retrieval (T034)

`CourtListenerAdapter` in `adapter.py` and schemas in `schemas.py` implement opinion text retrieval, provenance preservation, and opinion selection:

- **Opinion retrieval (`get_opinion`):** Queries `GET /api/rest/v4/opinions/{id}/` bounded by `ProviderBudget` and `ProviderPolicy`. Extracts text across the priority hierarchy (`plain_text`, `html_with_citations`, `html`, `html_lawbox`, `html_columbia`, `xml_harvard`).
- **HTML block boundary parser (`OpinionTextParser`, `clean_opinion_html`):** Extracts readable opinion text from HTML/XML, stripping `<script>` and `<style>` blocks and tags, unescaping entities, and converting block tags (`p`, `div`, `br`, headings, `li`) into line breaks (`htmlparser-block-boundaries-v1`). Plain text uses `identity-v1`.
- **Dissent skipping and opinion selection ([[docs/issues/BUG-004 - First opinion reference can be a dissent|BUG-004]]):** `resolve_cluster_opinion` orders cluster opinion candidates (cluster ID followed by sorted sub-opinion IDs). It selects lead/combined types (`010combined`, `020lead`, `015unamani`, `025plurality`, `majority`) and deliberately rejects dissents and concurrences (`040dissent`, `030concurrence`, `035concurrence_in_part`) as holding sources. If only dissents exist, it fails closed, returning `None`.
- **Distinguishing missing text:** When opinion text is unavailable, empty, or dissent-only, `opinion_text_available = False`, `opinion_text = None`, `source_sha256 = None`, and `source_metadata["missing_text"] = True`. When present, `opinion_text_available = True` and `source_sha256` is guaranteed to be 64 characters (SHA-256 hex digest), strictly satisfying database check constraints.
- **Authority resolution and stored results:** `resolve_authority` returns `CourtListenerResolvedAuthority` with case name, court, year, citation, source URL, opinion text, and provenance metadata (`cluster_id`, `opinion_id`, `provider_opinion_type`, `text_field`, `text_conversion`, `raw_sha256`, `characters`, `attribution`).
- **Persistence & API exposure:** `Authority` entity and `SafeAuthority` contract expose resolved data. `GET /api/v1/analyses/{id}/citations` populates `authorities` and links `SafeCitation.authority`.
- **Testing:** 33 unit tests in `tests/unit/test_courtlistener_adapter.py` and 17 integration tests in `tests/integration/test_citation_pipeline.py` verify opinion extraction, dissent selection, missing text distinction, and database persistence.

## Implemented lookup deduplication and response caching (T035)

- **Public source response caching (`CourtListenerCache`):** Adapter caches deterministic citation lookup results (`200` verified, `404` not found, `300` ambiguous, `400` invalid), retrieved opinions (`get_opinion`), and resolved authorities (`resolve_authority`) within an analysis or session. Queries normalize whitespace so minor text variations immediately hit the cache without outbound HTTP calls.
- **Occurrence preservation and authority sharing (`verify_citations_for_analysis`):** All original document citation occurrences are preserved with their distinct offsets, page numbers, paragraph segments, and extraction metadata. Repeated citations share the same outbound lookup and link to the same `Authority` entity row (`UniqueConstraint("analysis_id", "source", "external_id")`).
- **Inspectability:** Each occurrence location remains inspectable in `GET /api/v1/analyses/{id}/citations` and verified against the document snapshot.
- **Stage runner component:** `verified_citation_stage` constructs extraction and deduplicated verification results. It is not registered in the normal contained review workflow. Partial outputs and occurrence/record limits conflict with worker validation; see [[docs/issues/BUG-012 - Citation verification output conflicts with worker validation]].
- **Testing:** 42 unit tests in `test_courtlistener_adapter.py`, 4 unit tests in `test_citation_dedup.py`, and 19 integration tests in `test_citation_pipeline.py` verify cache hits, whitespace collapse, single authority row persistence, and occurrence inspectability.

## Still planned

- **T036:** End-to-end failure matrix, worker integration and coverage tests across the verification pipeline. Preserve lookup reasons and database-coverage limitations through stored API results, and test mixed/unavailable results before activating the runner.

Related: [[TODO]], [[apps/api/src/filingguard/integrations/providers/README]], [[apps/api/src/filingguard/modules/citations/README]], [[docs/issues/BUG-004 - First opinion reference can be a dissent]], [[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]], [[docs/decisions/ADR-009 - Local citation occurrences before source verification]].
