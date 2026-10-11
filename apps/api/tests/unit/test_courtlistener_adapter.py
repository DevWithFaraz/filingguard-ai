"""Unit tests for CourtListener adapter and bounded error mapping (T033)."""

import time

import httpx
import pytest

from filingguard.integrations.courtlistener import CourtListenerAdapter
from filingguard.integrations.courtlistener.schemas import NOT_FOUND_LIMITATION
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.integrations.providers.transport import ProviderPolicy
from filingguard.modules.analyses.schemas import CitationStatus

TOKEN = "test-courtlistener-token-abc123xyz"
CITATION = "576 U.S. 644"


def make_budget(
    timeout: float = 30.0, max_attempts: int = 60, attempts_used: int = 0
) -> ProviderBudget:
    return ProviderBudget(
        deadline=time.monotonic() + timeout,
        max_attempts=max_attempts,
        attempts_used=attempts_used,
    )


def test_verified_citation_single_cluster() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/rest/v4/citation-lookup/"
        assert request.headers["authorization"] == f"Token {TOKEN}"
        return httpx.Response(
            200,
            json=[
                {
                    "status": 200,
                    "normalized_citations": ["576 U.S. 644"],
                    "clusters": [
                        {
                            "id": 2812209,
                            "case_name": "Obergefell v. Hodges",
                            "citation": "576 U.S. 644",
                            "court": "https://www.courtlistener.com/api/rest/v4/courts/scotus/",
                            "date_filed": "2015-06-26",
                            "sub_opinions": [
                                "https://www.courtlistener.com/api/rest/v4/opinions/2812209/"
                            ],
                            "absolute_url": "/opinion/2812209/obergefell-v-hodges/",
                        }
                    ],
                }
            ],
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )
    result = adapter.lookup_citation(CITATION)

    assert result.status == CitationStatus.VERIFIED
    assert result.query_text == CITATION
    assert result.normalized_citation == "576 U.S. 644"
    assert result.provider_status == 200
    assert result.cluster is not None
    assert result.cluster.id == 2812209
    assert result.cluster.case_name == "Obergefell v. Hodges"
    assert result.cluster.court == "scotus"
    assert result.cluster.year == 2015
    assert result.cluster.opinion_ids == [2812209]
    assert (
        result.cluster.source_url
        == "https://www.courtlistener.com/opinion/2812209/obergefell-v-hodges/"
    )
    assert result.limitation is None


def test_ambiguous_citation_multiple_clusters() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "status": 200,
                    "normalized_citations": ["123 F.3d 456"],
                    "clusters": [
                        {
                            "id": 1001,
                            "case_name": "First Case v. Party",
                            "court": "ca2",
                            "date_filed": "1997-01-01",
                        },
                        {
                            "id": 1002,
                            "case_name": "Second Case v. Party",
                            "court": "ca9",
                            "date_filed": "1997-05-01",
                        },
                    ],
                }
            ],
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )
    result = adapter.lookup_citation("123 F.3d 456")

    assert result.status == CitationStatus.AMBIGUOUS
    assert result.cluster is None
    assert len(result.clusters) == 2
    assert result.clusters[0].id == 1001
    assert result.clusters[1].id == 1002
    assert result.reason == "multiple_clusters_matched"
    assert result.limitation is not None


def test_ambiguous_citation_status_300() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "status": 300,
                    "normalized_citations": ["100 U.S. 100"],
                    "clusters": [
                        {"id": 2001, "case_name": "Case A"},
                        {"id": 2002, "case_name": "Case B"},
                    ],
                }
            ],
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )
    result = adapter.lookup_citation("100 U.S. 100")

    assert result.status == CitationStatus.AMBIGUOUS
    assert result.provider_status == 300
    assert result.reason == "ambiguous_citation"


def test_invalid_citation_status_400() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[{"status": 400, "normalized_citations": []}],
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )
    result = adapter.lookup_citation("not a real citation format")

    assert result.status == CitationStatus.INVALID
    assert result.provider_status == 400
    assert result.reason == "invalid_citation_syntax"


def test_not_found_status_404() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "status": 404,
                    "normalized_citations": ["999 U.S. 999"],
                    "clusters": [],
                }
            ],
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )
    result = adapter.lookup_citation("999 U.S. 999")

    assert result.status == CitationStatus.NOT_FOUND
    assert result.provider_status == 404
    assert result.reason == "not_found_in_courtlistener_database"
    assert result.limitation == NOT_FOUND_LIMITATION
    assert "conclusively prove" in result.limitation


def test_not_found_empty_clusters_on_200() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[{"status": 200, "clusters": [], "normalized_citations": ["888 U.S. 888"]}],
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )
    result = adapter.lookup_citation("888 U.S. 888")

    assert result.status == CitationStatus.NOT_FOUND
    assert result.reason == "no_clusters_matched"
    assert result.limitation == NOT_FOUND_LIMITATION


def test_not_found_empty_response_list() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )
    result = adapter.lookup_citation("Some Unrecognized Citation Text")

    assert result.status == CitationStatus.NOT_FOUND
    assert result.reason == "no_citations_detected"


def test_timeout_never_becomes_not_found() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Socket read timed out")

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        policy=ProviderPolicy(courtlistener_retries=0),
        transport=httpx.MockTransport(handler),
    )
    result = adapter.lookup_citation(CITATION)

    # Core invariant: network timeout must NEVER become not_found
    assert result.status != CitationStatus.NOT_FOUND
    assert result.status == CitationStatus.UNAVAILABLE
    assert result.reason == "timeout"


def test_rate_limit_429_never_becomes_not_found() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "60"})

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        policy=ProviderPolicy(courtlistener_retries=0),
        transport=httpx.MockTransport(handler),
    )
    result = adapter.lookup_citation(CITATION)

    # Core invariant: 429 rate limit must NEVER become not_found
    assert result.status != CitationStatus.NOT_FOUND
    assert result.status == CitationStatus.UNAVAILABLE
    assert result.reason == "rate_limited"


@pytest.mark.parametrize("status_code", [500, 502, 503, 504])
def test_server_error_5xx_never_becomes_not_found(status_code: int) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code)

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        policy=ProviderPolicy(courtlistener_retries=0),
        transport=httpx.MockTransport(handler),
    )
    result = adapter.lookup_citation(CITATION)

    # Core invariant: 5xx server error must NEVER become not_found
    assert result.status != CitationStatus.NOT_FOUND
    assert result.status == CitationStatus.UNAVAILABLE
    assert result.reason == "http_failure"


def test_network_failure_never_becomes_not_found() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        policy=ProviderPolicy(courtlistener_retries=0),
        transport=httpx.MockTransport(handler),
    )
    result = adapter.lookup_citation(CITATION)

    # Core invariant: connection failure must NEVER become not_found
    assert result.status != CitationStatus.NOT_FOUND
    assert result.status == CitationStatus.UNAVAILABLE
    assert result.reason == "network_failure"


def test_request_budget_exhausted_never_becomes_not_found() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    budget = make_budget(max_attempts=5, attempts_used=5)
    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=budget,
        transport=httpx.MockTransport(handler),
    )
    result = adapter.lookup_citation(CITATION)

    assert result.status != CitationStatus.NOT_FOUND
    assert result.status == CitationStatus.UNAVAILABLE
    assert result.reason == "request_budget_exhausted"


def test_deadline_exceeded_never_becomes_not_found() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    # Budget with deadline in the past
    budget = ProviderBudget(deadline=time.monotonic() - 1.0)
    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=budget,
        transport=httpx.MockTransport(handler),
    )
    result = adapter.lookup_citation(CITATION)

    assert result.status != CitationStatus.NOT_FOUND
    assert result.status == CitationStatus.UNAVAILABLE
    assert result.reason == "deadline_exceeded"


def test_missing_or_blank_token_returns_unavailable() -> None:
    adapter = CourtListenerAdapter(token="")
    result = adapter.lookup_citation(CITATION)

    assert result.status != CitationStatus.NOT_FOUND
    assert result.status == CitationStatus.UNAVAILABLE
    assert result.reason == "missing_token"


def test_token_never_in_repr_or_result() -> None:
    secret_token = "ultra-secret-test-key-998877"
    adapter = CourtListenerAdapter(
        token=secret_token,
        budget=make_budget(),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=[])),
    )
    repr_str = repr(adapter)
    assert secret_token not in repr_str

    result = adapter.lookup_citation(CITATION)
    json_str = result.model_dump_json()
    assert secret_token not in json_str


@pytest.mark.parametrize("bad_input", ["", "   ", "\t\n"])
def test_empty_or_whitespace_input_returns_invalid(bad_input: str) -> None:
    adapter = CourtListenerAdapter(token=TOKEN)
    result = adapter.lookup_citation(bad_input)

    assert result.status == CitationStatus.INVALID
    assert result.reason == "empty_citation"


def test_oversized_input_returns_invalid() -> None:
    oversized = "A" * 501
    adapter = CourtListenerAdapter(token=TOKEN)
    result = adapter.lookup_citation(oversized)

    assert result.status == CitationStatus.INVALID
    assert result.reason == "citation_too_long"


def test_context_manager_clean_lifecycle() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"status": 404, "clusters": []}])

    with CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    ) as adapter:
        result = adapter.lookup_citation("999 U.S. 999")
        assert result.status == CitationStatus.NOT_FOUND

    # After exiting context manager, client is closed
    assert adapter._client is None


def test_clean_opinion_html_strips_scripts_and_styles() -> None:
    from filingguard.integrations.courtlistener import clean_opinion_html

    html = (
        "<html><head><script>alert('malicious')</script>"
        "<style>body { color: red; }</style></head>"
        "<body><h1>Heading</h1><p>First paragraph &amp; quotes: &quot;hello&quot;.</p>"
        "<div>Second line &lt;tag&gt;</div></body></html>"
    )
    cleaned = clean_opinion_html(html)
    assert "alert" not in cleaned
    assert "color: red" not in cleaned
    assert "Heading" in cleaned
    assert "First paragraph & quotes: \"hello\"." in cleaned
    assert "Second line <tag>" in cleaned


def test_get_opinion_plain_text() -> None:
    import hashlib

    text = "We hold that same-sex couples may exercise the fundamental right to marry."

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/rest/v4/opinions/2812209/"
        return httpx.Response(
            200,
            json={
                "id": 2812209,
                "cluster_id": 2812209,
                "type": "010combined",
                "plain_text": text,
                "html_with_citations": "",
                "absolute_url": "/opinion/2812209/obergefell-v-hodges/",
            },
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )
    opinion = adapter.get_opinion(2812209)

    assert opinion.id == 2812209
    assert opinion.opinion_type == "010combined"
    assert opinion.opinion_text_available is True
    assert opinion.text == text
    assert opinion.text_field == "plain_text"
    assert opinion.text_conversion == "identity-v1"
    assert opinion.text_sha256 == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert len(opinion.text_sha256) == 64
    assert opinion.missing_text is False


def test_get_opinion_html_with_citations() -> None:
    import hashlib

    html = (
        "<opinion type=\"majority\">"
        "<p>Separate educational facilities are inherently unequal.</p>"
        "</opinion>"
    )


    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/rest/v4/opinions/105221/"
        return httpx.Response(
            200,
            json={
                "id": 105221,
                "cluster_id": 105221,
                "type": "010combined",
                "plain_text": "",
                "html_with_citations": html,
                "absolute_url": "/opinion/105221/brown-v-board-of-education/",
            },
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )
    opinion = adapter.get_opinion(105221)

    assert opinion.id == 105221
    assert opinion.opinion_text_available is True
    assert "Separate educational facilities are inherently unequal." in opinion.text
    assert opinion.text_field == "html_with_citations"
    assert opinion.text_conversion == "htmlparser-block-boundaries-v1"
    assert opinion.text_sha256 == hashlib.sha256(opinion.text.encode("utf-8")).hexdigest()
    assert len(opinion.text_sha256) == 64
    assert opinion.raw_sha256 == hashlib.sha256(html.encode("utf-8")).hexdigest()
    assert opinion.missing_text is False


def test_get_opinion_distinguishes_missing_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": 99999,
                "cluster_id": 99999,
                "type": "010combined",
                "plain_text": "",
                "html_with_citations": "   \n\t  ",
                "html": "",
            },
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )
    opinion = adapter.get_opinion(99999)

    assert opinion.id == 99999
    assert opinion.opinion_text_available is False
    assert opinion.text is None
    assert opinion.text_sha256 is None
    assert opinion.missing_text is True


def test_get_opinion_network_failure_never_becomes_missing_text() -> None:
    from filingguard.integrations.providers.runtime import ProviderUnavailable

    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        policy=ProviderPolicy(courtlistener_retries=0),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(ProviderUnavailable) as exc_info:
        adapter.get_opinion(105221)

    assert exc_info.value.code in {"network_failure", "connection_error"}


def test_resolve_cluster_opinion_prioritizes_combined_over_dissent_bug_004() -> None:
    """Miranda bug BUG-004: sub_opinions has 040dissent first; adapter must select lead/combined."""
    from filingguard.integrations.courtlistener.schemas import CourtListenerCluster

    cluster = CourtListenerCluster(
        id=107252,
        case_name="Miranda v. Arizona",
        citation="384 U.S. 436",
        court="scotus",
        year=1966,
        sub_opinions=[
            "https://www.courtlistener.com/api/rest/v4/opinions/9423235/",
            "https://www.courtlistener.com/api/rest/v4/opinions/107252/",
        ],
        opinion_ids=[9423235, 107252],
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/rest/v4/opinions/9423235/":
            return httpx.Response(
                200,
                json={
                    "id": 9423235,
                    "cluster_id": 107252,
                    "type": "040dissent",
                    "plain_text": "Justice White, with whom Justice Harlan joins, dissenting.",
                },
            )
        elif request.url.path == "/api/rest/v4/opinions/107252/":
            return httpx.Response(
                200,
                json={
                    "id": 107252,
                    "cluster_id": 107252,
                    "type": "010combined",
                    "plain_text": "Mr. Chief Justice Warren delivered the opinion of the Court.",
                },
            )
        return httpx.Response(404)

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )
    opinion = adapter.resolve_cluster_opinion(cluster)

    assert opinion is not None
    assert opinion.id == 107252
    assert opinion.opinion_type == "010combined"
    assert "delivered the opinion of the Court" in opinion.text
    assert "dissenting" not in opinion.text


def test_resolve_cluster_opinion_dissent_only_fails_closed_bug_004() -> None:
    """When only dissents exist, adapter fails closed and NEVER uses dissent as holding."""
    from filingguard.integrations.courtlistener.schemas import CourtListenerCluster

    cluster = CourtListenerCluster(
        id=55555,
        case_name="Dissent Only Case",
        citation="100 U.S. 100",
        opinion_ids=[99901],
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": 99901,
                "cluster_id": 55555,
                "type": "040dissent",
                "plain_text": "I respectfully dissent.",
            },
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )
    opinion = adapter.resolve_cluster_opinion(cluster)
    assert opinion is None

    # resolve_authority marks opinion text unavailable rather than using dissent
    resolved = adapter.resolve_authority(cluster)
    assert resolved.opinion_text_available is False
    assert resolved.opinion_text is None
    assert resolved.source_sha256 is None
    assert resolved.source_metadata["missing_text"] is True
    assert resolved.source_metadata["reason"] == "dissent_or_concurrence_only"


def test_resolve_authority_provenance_and_fields() -> None:
    from filingguard.integrations.courtlistener.schemas import CourtListenerCluster

    cluster = CourtListenerCluster(
        id=105221,
        case_name="Brown v. Board of Education",
        citation="347 U.S. 483",
        court="scotus",
        year=1954,
        opinion_ids=[105221],
        source_url="https://www.courtlistener.com/opinion/105221/brown-v-board-of-education/",
    )

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": 105221,
                "cluster_id": 105221,
                "type": "010combined",
                "plain_text": "Separate educational facilities are inherently unequal.",
            },
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )
    resolved = adapter.resolve_authority(cluster)

    assert resolved.cluster_id == 105221
    assert resolved.opinion_id == 105221
    assert resolved.case_name == "Brown v. Board of Education"
    assert resolved.citation == "347 U.S. 483"
    assert resolved.court == "scotus"
    assert resolved.year == 1954
    assert resolved.source_url == "https://www.courtlistener.com/opinion/105221/brown-v-board-of-education/"
    assert resolved.opinion_text_available is True
    assert resolved.opinion_text == "Separate educational facilities are inherently unequal."
    assert len(resolved.source_sha256) == 64
    assert resolved.retrieved_at is not None
    assert resolved.source_metadata["provenance"] == "courtlistener_api_v4"
    assert resolved.source_metadata["attribution"] == (
        "Public US judicial opinion, retrieved from CourtListener / Free Law Project"
    )
    assert resolved.source_metadata["missing_text"] is False
    assert resolved.source_metadata["characters"] == len(resolved.opinion_text)


def test_verify_and_resolve_flow() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/rest/v4/citation-lookup/":
            return httpx.Response(
                200,
                json=[
                    {
                        "status": 200,
                        "normalized_citations": ["347 U.S. 483"],
                        "clusters": [
                            {
                                "id": 105221,
                                "case_name": "Brown v. Board of Education",
                                "citation": "347 U.S. 483",
                                "court": "scotus",
                                "date_filed": "1954-05-17",
                                "opinion_ids": [105221],
                                "sub_opinions": [105221],
                                "absolute_url": "/opinion/105221/brown-v-board-of-education/",
                            }
                        ],
                    }
                ],
            )
        elif request.url.path == "/api/rest/v4/opinions/105221/":
            return httpx.Response(
                200,
                json={
                    "id": 105221,
                    "cluster_id": 105221,
                    "type": "010combined",
                    "plain_text": (
                        "In the field of public education, separate but equal has no place."
                    ),
                },
            )
        return httpx.Response(404)

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )
    lookup, resolved = adapter.verify_and_resolve("347 U.S. 483")

    assert lookup.status == CitationStatus.VERIFIED
    assert resolved is not None
    assert resolved.case_name == "Brown v. Board of Education"
    assert resolved.opinion_text_available is True
    assert "separate but equal has no place" in resolved.opinion_text


def test_create_authority_record_service_helper() -> None:
    from uuid import uuid4

    from filingguard.integrations.courtlistener.schemas import CourtListenerResolvedAuthority
    from filingguard.modules.citations.service import create_authority_record


    analysis_id = uuid4()
    resolved = CourtListenerResolvedAuthority(
        cluster_id=105221,
        opinion_id=105221,
        case_name="Brown v. Board of Education",
        citation="347 U.S. 483",
        court="scotus",
        year=1954,
        source_url="https://example.invalid/opinion/105221",
        opinion_text_available=True,
        opinion_text="Holding text",
        source_sha256="a" * 64,
        source_metadata={"missing_text": False},
    )
    record = create_authority_record(analysis_id, resolved)

    assert record.analysis_id == analysis_id
    assert record.source == "courtlistener"
    assert record.external_id == "105221"
    assert record.case_name == "Brown v. Board of Education"
    assert record.citation == "347 U.S. 483"
    assert record.opinion_text_available is True
    assert record.opinion_text == "Holding text"
    assert record.source_sha256 == "a" * 64
    assert len(record.source_sha256) == 64


def test_lookup_cache_hits_and_avoids_repeated_http_requests() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(
            200,
            json=[
                {
                    "status": 200,
                    "normalized_citations": ["576 U.S. 644"],
                    "clusters": [
                        {
                            "id": 2812209,
                            "case_name": "Obergefell v. Hodges",
                            "citation": "576 U.S. 644",
                            "court": "scotus",
                            "date_filed": "2015-06-26",
                            "sub_opinions": [2812209],
                        }
                    ],
                }
            ],
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )

    res1 = adapter.lookup_citation("576 U.S. 644")
    assert res1.status == CitationStatus.VERIFIED
    assert request_count == 1
    assert adapter.cache.lookup_misses == 1
    assert adapter.cache.lookup_hits == 0

    res2 = adapter.lookup_citation("576 U.S. 644")
    assert res2.status == CitationStatus.VERIFIED
    assert res2.cluster.case_name == "Obergefell v. Hodges"
    assert request_count == 1  # No second HTTP request!
    assert adapter.cache.lookup_hits == 1


def test_lookup_cache_collapses_whitespace() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(
            200,
            json=[
                {
                    "status": 200,
                    "normalized_citations": ["576 U.S. 644"],
                    "clusters": [
                        {
                            "id": 2812209,
                            "case_name": "Obergefell v. Hodges",
                            "citation": "576 U.S. 644",
                            "sub_opinions": [2812209],
                        }
                    ],
                }
            ],
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )

    adapter.lookup_citation("576 U.S. 644")
    assert request_count == 1

    # Query with irregular spacing hits the cache
    res2 = adapter.lookup_citation("576   U.S.   644")
    assert res2.status == CitationStatus.VERIFIED
    assert request_count == 1
    assert adapter.cache.lookup_hits == 1


def test_lookup_cache_by_normalized_citation() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(
            200,
            json=[
                {
                    "status": 200,
                    "normalized_citations": ["576 U.S. 644"],
                    "clusters": [
                        {
                            "id": 2812209,
                            "case_name": "Obergefell v. Hodges",
                            "citation": "576 U.S. 644",
                            "sub_opinions": [2812209],
                        }
                    ],
                }
            ],
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )

    # First lookup using full unnormalized query string
    adapter.lookup_citation("Obergefell v. Hodges, 576 U.S. 644")
    assert request_count == 1

    # Subsequent lookup using the canonical normalized citation hits the cache
    res2 = adapter.lookup_citation("576 U.S. 644")
    assert res2.status == CitationStatus.VERIFIED
    assert request_count == 1
    assert adapter.cache.lookup_hits == 1


def test_lookup_cache_stores_not_found_and_invalid() -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if "unknown" in str(request.read()):
            return httpx.Response(
                200,
                json=[{"status": 404, "normalized_citations": [], "clusters": []}],
            )
        return httpx.Response(
            200,
            json=[{"status": 400, "normalized_citations": [], "clusters": []}],
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )

    # Not found cached
    nf1 = adapter.lookup_citation("unknown 999")
    assert nf1.status == CitationStatus.NOT_FOUND
    assert len(requests) == 1

    nf2 = adapter.lookup_citation("unknown 999")
    assert nf2.status == CitationStatus.NOT_FOUND
    assert len(requests) == 1
    assert adapter.cache.lookup_hits == 1

    # Invalid cached
    inv1 = adapter.lookup_citation("bad syntax")
    assert inv1.status == CitationStatus.INVALID
    assert len(requests) == 2

    inv2 = adapter.lookup_citation("bad syntax")
    assert inv2.status == CitationStatus.INVALID
    assert len(requests) == 2
    assert adapter.cache.lookup_hits == 2


def test_opinion_cache_avoids_repeated_http_requests() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        assert request.url.path == "/api/rest/v4/opinions/2812209/"
        return httpx.Response(
            200,
            json={
                "id": 2812209,
                "type": "010combined",
                "plain_text": "The Fourteenth Amendment requires a State to license a marriage...",
            },
        )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )

    op1 = adapter.get_opinion(2812209)
    assert op1.opinion_text_available is True
    assert request_count == 1
    assert adapter.cache.opinion_misses == 1
    assert adapter.cache.opinion_hits == 0

    op2 = adapter.get_opinion(2812209)
    assert op2.opinion_text_available is True
    assert op2.text == op1.text
    assert request_count == 1  # Cached!
    assert adapter.cache.opinion_hits == 1


def test_resolve_authority_cache() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(
            200,
            json={
                "id": 105221,
                "type": "010combined",
                "plain_text": "Separate educational facilities are inherently unequal.",
            },
        )

    from filingguard.integrations.courtlistener.schemas import CourtListenerCluster

    cluster = CourtListenerCluster(
        id=105221,
        case_name="Brown v. Board of Education",
        citation="347 U.S. 483",
        court="scotus",
        year=1954,
        opinion_ids=[105221],
    )

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )

    auth1 = adapter.resolve_authority(cluster)
    assert auth1.opinion_text_available is True
    assert request_count == 1
    assert adapter.cache.authority_misses == 1
    assert adapter.cache.authority_hits == 0

    auth2 = adapter.resolve_authority(cluster)
    assert auth2.cluster_id == 105221
    assert auth2.opinion_text == auth1.opinion_text
    assert request_count == 1  # 0 additional requests
    assert adapter.cache.authority_hits == 1


def test_verify_and_resolve_cached_end_to_end() -> None:
    lookup_calls = 0
    opinion_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal lookup_calls, opinion_calls
        if "/citation-lookup/" in request.url.path:
            lookup_calls += 1
            return httpx.Response(
                200,
                json=[
                    {
                        "status": 200,
                        "normalized_citations": ["347 U.S. 483"],
                        "clusters": [
                            {
                                "id": 105221,
                                "case_name": "Brown v. Board of Education",
                                "citation": "347 U.S. 483",
                                "court": "scotus",
                                "year": 1954,
                                "sub_opinions": [105221],
                            }
                        ],
                    }
                ],
            )
        elif "/opinions/" in request.url.path:
            opinion_calls += 1
            return httpx.Response(
                200,
                json={
                    "id": 105221,
                    "type": "010combined",
                    "plain_text": "Separate educational facilities are inherently unequal.",
                },
            )
        return httpx.Response(404)

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
    )

    # First verification: 1 lookup + 1 opinion = 2 HTTP calls
    lookup1, auth1 = adapter.verify_and_resolve("347 U.S. 483")
    assert lookup1.status == CitationStatus.VERIFIED
    assert auth1 is not None
    assert lookup_calls == 1
    assert opinion_calls == 1

    # Second verification: Both lookup and opinion are served from cache!
    lookup2, auth2 = adapter.verify_and_resolve("347 U.S. 483")
    assert lookup2.status == CitationStatus.VERIFIED
    assert auth2 is not None
    assert auth2.cluster_id == auth1.cluster_id
    assert lookup_calls == 1  # 0 additional lookups
    assert opinion_calls == 1  # 0 additional opinion fetches
    assert adapter.cache.lookup_hits == 1
    assert adapter.cache.authority_hits == 1


def test_shared_cache_between_adapters() -> None:
    from filingguard.integrations.courtlistener import CourtListenerCache

    shared_cache = CourtListenerCache()
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json=[
                {
                    "status": 200,
                    "normalized_citations": ["347 U.S. 483"],
                    "clusters": [{"id": 105221, "case_name": "Brown", "sub_opinions": [105221]}],
                }
            ],
        )

    adapter1 = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
        cache=shared_cache,
    )
    res1 = adapter1.lookup_citation("347 U.S. 483")
    assert res1.status == CitationStatus.VERIFIED
    assert calls == 1

    # Adapter 2 shares the same cache instance
    adapter2 = CourtListenerAdapter(
        token=TOKEN,
        budget=make_budget(),
        transport=httpx.MockTransport(handler),
        cache=shared_cache,
    )
    res2 = adapter2.lookup_citation("347 U.S. 483")
    assert res2.status == CitationStatus.VERIFIED
    assert calls == 1  # No second HTTP call!
    assert shared_cache.lookup_hits == 1


def test_cache_clear_resets_cache() -> None:
    from filingguard.integrations.courtlistener import CourtListenerCache, CourtListenerLookupResult

    cache = CourtListenerCache()
    res = CourtListenerLookupResult(
        status=CitationStatus.VERIFIED,
        query_text="347 U.S. 483",
        normalized_citation="347 U.S. 483",
    )
    cache.set_lookup("347 U.S. 483", res)
    assert cache.get_lookup("347 U.S. 483") is not None
    assert cache.lookup_hits == 1
    assert len(cache.lookups) == 1

    cache.clear()
    assert len(cache.lookups) == 0
    assert cache.lookup_hits == 0
    assert cache.lookup_misses == 0
    assert cache.get_lookup("347 U.S. 483") is None
