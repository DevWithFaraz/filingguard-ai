"""Unit tests for outbound citation lookup deduplication and occurrence retention (T035).

Verifies that repeated citation mentions share a single outbound authority lookup,
that public source responses are cached, and that every original filing location
remains distinct and inspectable.
"""

from uuid import uuid4

import httpx

from filingguard.db.models import Analysis, Citation
from filingguard.integrations.courtlistener import CourtListenerAdapter
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.execution import ReviewSegment
from filingguard.modules.analyses.schemas import StageName, StageStatus
from filingguard.modules.citations.runner import verified_citation_stage
from filingguard.modules.citations.service import verify_citations_for_analysis

TOKEN = "test-token-dedup-xyz"


def make_test_budget() -> ProviderBudget:
    import time
    return ProviderBudget(deadline=time.monotonic() + 30.0, max_attempts=60)


def test_repeats_share_one_authority_lookup_and_retain_all_occurrences() -> None:
    lookup_calls: list[str] = []
    opinion_calls: list[int] = []

    def mock_courtlistener_handler(request: httpx.Request) -> httpx.Response:
        url_path = request.url.path
        if "/citation-lookup/" in url_path:
            body = request.read().decode("utf-8")
            lookup_calls.append(body)
            if "347 U.S. 483" in body:
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
            elif "376 U.S. 254" in body:
                return httpx.Response(
                    200,
                    json=[
                        {
                            "status": 200,
                            "normalized_citations": ["376 U.S. 254"],
                            "clusters": [
                                {
                                    "id": 106761,
                                    "case_name": "New York Times Co. v. Sullivan",
                                    "citation": "376 U.S. 254",
                                    "court": "scotus",
                                    "year": 1964,
                                    "sub_opinions": [106761],
                                }
                            ],
                        }
                    ],
                )
            elif "999 Fake 123" in body:
                return httpx.Response(
                    200,
                    json=[{"status": 404, "normalized_citations": [], "clusters": []}],
                )
            return httpx.Response(200, json=[])

        elif "/opinions/" in url_path:
            import re
            m = re.search(r"/opinions/(\d+)/", url_path)
            op_id = int(m.group(1)) if m else 0
            opinion_calls.append(op_id)
            if op_id == 105221:
                return httpx.Response(
                    200,
                    json={
                        "id": 105221,
                        "type": "010combined",
                        "plain_text": "Separate educational facilities are inherently unequal.",
                    },
                )
            elif op_id == 106761:
                return httpx.Response(
                    200,
                    json={
                        "id": 106761,
                        "type": "010combined",
                        "plain_text": (
                            "Debate on public issues should be uninhibited, robust, and wide-open."
                        ),
                    },
                )

        return httpx.Response(404)

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_test_budget(),
        transport=httpx.MockTransport(mock_courtlistener_handler),
    )

    analysis_id = uuid4()
    seg_1, seg_2, seg_3, seg_4 = uuid4(), uuid4(), uuid4(), uuid4()

    # 5 citations: 2 repeats of Brown, 1 Sullivan, 2 repeats of Fake Citation
    cit_brown_1 = Citation(
        id=uuid4(),
        analysis_id=analysis_id,
        raw_text="347 U.S. 483",
        normalized_text="347 U.S. 483",
        segment_id=seg_1,
        page_number=1,
        start_offset=10,
        end_offset=22,
        extraction_metadata={
            "parser_version": "2.7.8",
            "kind": "full_case",
            "support": "recognized",
        },
    )
    cit_brown_2 = Citation(
        id=uuid4(),
        analysis_id=analysis_id,
        raw_text="347 U.S. 483",
        normalized_text="347 U.S. 483",
        segment_id=seg_2,
        page_number=2,
        start_offset=150,
        end_offset=162,
        extraction_metadata={
            "parser_version": "2.7.8",
            "kind": "full_case",
            "support": "recognized",
        },
    )
    cit_sullivan = Citation(
        id=uuid4(),
        analysis_id=analysis_id,
        raw_text="376 U.S. 254",
        normalized_text="376 U.S. 254",
        segment_id=seg_3,
        page_number=3,
        start_offset=300,
        end_offset=312,
        extraction_metadata={
            "parser_version": "2.7.8",
            "kind": "full_case",
            "support": "recognized",
        },
    )
    cit_fake_1 = Citation(
        id=uuid4(),
        analysis_id=analysis_id,
        raw_text="999 Fake 123",
        normalized_text=None,
        segment_id=seg_4,
        page_number=4,
        start_offset=450,
        end_offset=462,
        extraction_metadata={
            "parser_version": "2.7.8",
            "kind": "reporter_candidate",
            "support": "unsupported",
        },
    )
    cit_fake_2 = Citation(
        id=uuid4(),
        analysis_id=analysis_id,
        raw_text="999 Fake 123",
        normalized_text=None,
        segment_id=seg_4,
        page_number=4,
        start_offset=500,
        end_offset=512,
        extraction_metadata={
            "parser_version": "2.7.8",
            "kind": "reporter_candidate",
            "support": "unsupported",
        },
    )

    all_citations = [cit_brown_1, cit_brown_2, cit_sullivan, cit_fake_1, cit_fake_2]

    verified_citations, authorities = verify_citations_for_analysis(
        analysis_id, all_citations, adapter
    )

    # 1. Outbound lookups deduplicated!
    # "347 U.S. 483" looked up exactly ONCE
    brown_lookups = [c for c in lookup_calls if "347 U.S. 483" in c]
    assert len(brown_lookups) == 1, f"Expected 1 Brown lookup, got {len(brown_lookups)}"

    # Brown opinion fetched exactly ONCE
    brown_opinions = [o for o in opinion_calls if o == 105221]
    assert len(brown_opinions) == 1, f"Expected 1 Brown opinion fetch, got {len(brown_opinions)}"

    # "376 U.S. 254" looked up and opinion fetched exactly ONCE
    assert len([c for c in lookup_calls if "376 U.S. 254" in c]) == 1
    assert len([o for o in opinion_calls if o == 106761]) == 1

    # Unsupported reporter candidates remain unrun and never leave the filing boundary.
    fake_lookups = [c for c in lookup_calls if "999 Fake 123" in c]
    assert len(fake_lookups) == 0

    # Recognized citations share two lookups and two opinion fetches.
    assert len(lookup_calls) == 2
    assert len(opinion_calls) == 2

    # 2. All 5 occurrences retained and distinct!
    assert len(verified_citations) == 5
    assert {c.id for c in verified_citations} == {
        cit_brown_1.id,
        cit_brown_2.id,
        cit_sullivan.id,
        cit_fake_1.id,
        cit_fake_2.id,
    }

    # 3. Inspectable locations preserved!
    assert verified_citations[0].start_offset == 10
    assert verified_citations[0].end_offset == 22
    assert verified_citations[0].page_number == 1

    assert verified_citations[1].start_offset == 150
    assert verified_citations[1].end_offset == 162
    assert verified_citations[1].page_number == 2

    assert verified_citations[3].start_offset == 450
    assert verified_citations[4].start_offset == 500

    # 4. Repeats share one authority lookup and one Authority record!
    assert len(authorities) == 2  # Only Brown and Sullivan, no duplicates!
    brown_auth = next(a for a in authorities if a.external_id == "105221")
    sullivan_auth = next(a for a in authorities if a.external_id == "106761")

    assert verified_citations[0].authority_id == brown_auth.id
    assert verified_citations[1].authority_id == brown_auth.id
    assert verified_citations[0].verification_status == "verified"
    assert verified_citations[1].verification_status == "verified"

    assert verified_citations[2].authority_id == sullivan_auth.id
    assert verified_citations[2].verification_status == "verified"

    # Unsupported candidates cannot assert a provider not-found verdict.
    assert verified_citations[3].verification_status == "not_run"
    assert verified_citations[3].authority_id is None
    assert verified_citations[4].verification_status == "not_run"
    assert verified_citations[4].authority_id is None


def test_parallel_citations_to_same_cluster_share_single_authority() -> None:
    calls = 0

    def mock_courtlistener_handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        url_path = request.url.path
        if "/citation-lookup/" in url_path:
            # Both "347 U.S. 483" and "74 S. Ct. 686" map to the same cluster 105221
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
        elif "/opinions/" in url_path:
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
        budget=make_test_budget(),
        transport=httpx.MockTransport(mock_courtlistener_handler),
    )

    analysis_id = uuid4()
    cit_official = Citation(
        id=uuid4(),
        analysis_id=analysis_id,
        raw_text="347 U.S. 483",
        normalized_text="347 U.S. 483",
        segment_id=uuid4(),
        page_number=1,
        start_offset=0,
        end_offset=12,
        extraction_metadata={"kind": "full_case", "support": "recognized"},
    )
    cit_parallel = Citation(
        id=uuid4(),
        analysis_id=analysis_id,
        raw_text="74 S. Ct. 686",
        normalized_text="74 S. Ct. 686",
        segment_id=uuid4(),
        page_number=1,
        start_offset=20,
        end_offset=33,
        extraction_metadata={"kind": "full_case", "support": "recognized"},
    )

    verified_citations, authorities = verify_citations_for_analysis(
        analysis_id, [cit_official, cit_parallel], adapter
    )

    # Exactly 1 Authority record created in DB models, satisfying UniqueConstraint
    assert len(authorities) == 1
    shared_auth = authorities[0]
    assert shared_auth.external_id == "105221"

    # Both citations share the same authority_id
    assert verified_citations[0].authority_id == shared_auth.id
    assert verified_citations[1].authority_id == shared_auth.id
    assert verified_citations[0].verification_status == "verified"
    assert verified_citations[1].verification_status == "verified"


def test_unresolved_references_skipped_without_outbound_lookups() -> None:
    calls = 0

    def mock_courtlistener_handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=[])

    adapter = CourtListenerAdapter(
        token=TOKEN,
        budget=make_test_budget(),
        transport=httpx.MockTransport(mock_courtlistener_handler),
    )

    analysis_id = uuid4()
    cit_id = Citation(
        id=uuid4(),
        analysis_id=analysis_id,
        raw_text="Id. at 485",
        normalized_text=None,
        segment_id=uuid4(),
        page_number=1,
        start_offset=0,
        end_offset=10,
        extraction_metadata={"kind": "id", "support": "unresolved_reference"},
    )

    verified, authorities = verify_citations_for_analysis(
        analysis_id, [cit_id], adapter
    )

    assert len(verified) == 1
    assert verified[0].verification_status == "not_run"
    assert verified[0].authority_id is None
    assert len(authorities) == 0
    assert calls == 0  # Zero outbound calls!


def test_verified_citation_stage_runner_e2e() -> None:
    call_counts: dict[str, int] = {"lookup": 0, "opinion": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if "/citation-lookup/" in request.url.path:
            call_counts["lookup"] += 1
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
            call_counts["opinion"] += 1
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
        budget=make_test_budget(),
        transport=httpx.MockTransport(handler),
    )

    from filingguard.modules.documents.extraction import extract_text

    text = (
        "In Brown v. Board of Education, 347 U.S. 483 (1954), the Court ruled.\n\n"
        "Later in the argument, 347 U.S. 483 was cited again."
    )
    extracted_doc = extract_text(text)

    analysis = Analysis(
        id=uuid4(),
        document_name="Test doc",
        document_sha256=extracted_doc.input_sha256,
        document_snapshot=extracted_doc.model_dump(mode="json"),
        mode="live",
        status="running",
        court_profile_id="unverified",
        ai_used=False,
        stage_states={},
    )
    analysis.review_segments = tuple(
        ReviewSegment(id=uuid4(), start=p.start, end=p.end, page_number=p.page_number)
        for p in extracted_doc.paragraphs
    )

    budget = make_test_budget()
    stage_result = verified_citation_stage(analysis, budget, adapter=adapter)

    # 1. StageResult validation passes!
    stage_result.validate(StageName.CITATIONS)
    assert stage_result.status == StageStatus.COMPLETED
    assert stage_result.coverage.eligible == 2
    assert stage_result.coverage.evaluated == 2

    # 2. Outbound lookups deduplicated!
    assert call_counts["lookup"] == 1
    assert call_counts["opinion"] == 1

    # 3. Records contains 1 Authority + 2 Citations
    assert len(stage_result.records) == 3
    auth_records = [r for r in stage_result.records if type(r).__name__ == "Authority"]
    cit_records = [r for r in stage_result.records if type(r).__name__ == "Citation"]

    assert len(auth_records) == 1
    assert len(cit_records) == 2

    # 4. Both citations share the single Authority record ID
    assert cit_records[0].authority_id == auth_records[0].id
    assert cit_records[1].authority_id == auth_records[0].id
    assert cit_records[0].verification_status == "verified"
    assert cit_records[1].verification_status == "verified"

    # 5. Original locations remain distinct and inspectable
    assert cit_records[0].start_offset != cit_records[1].start_offset
    assert cit_records[0].raw_text == text[cit_records[0].start_offset : cit_records[0].end_offset]
    assert cit_records[1].raw_text == text[cit_records[1].start_offset : cit_records[1].end_offset]

    # 6. Cache tracking metadata verified (FR-046)
    verif_0 = cit_records[0].extraction_metadata["verification"]
    verif_1 = cit_records[1].extraction_metadata["verification"]
    assert verif_0["cached"] is False
    assert verif_0["cache_hit"] is False
    assert verif_0["cache_version"] == "courtlistener-cache-v1"
    assert verif_1["cached"] is True
    assert verif_1["cache_hit"] is True
    assert verif_1["cache_version"] == "courtlistener-cache-v1"
