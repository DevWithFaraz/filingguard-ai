"""Local-only extraction, private reads and exact original-location regressions."""

import logging
import time
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from threading import Event
from uuid import UUID, uuid4

import httpx
import pytest
from review_workers import forged_citation
from sqlalchemy import func, select
from test_orchestrator import await_status, owner, prepare
from test_orchestrator import private_client as private_client

from filingguard.db.models import Analysis, Authority, Citation, DocumentSegment, Finding
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.execution import (
    ReviewSegment,
    StageResult,
    execute_stage,
    result_from_wire,
    result_to_wire,
    validate_citation_records,
)
from filingguard.modules.analyses.orchestrator import REVIEW_STAGES
from filingguard.modules.analyses.schemas import Coverage, StageName, StageStatus
from filingguard.modules.citations.runner import citation_stage
from filingguard.modules.documents.extraction import extract_text, segment
from filingguard.modules.documents.schemas import ExtractedDocument, PageSpan

FIXTURE = Path(__file__).resolve().parents[4] / "data/demo/curated-v1/filing.txt"


def citation_only(client, runner=citation_stage):
    client.app.state.review_runners = {
        stage: runner
        if stage == StageName.CITATIONS
        else StageResult(
            status=StageStatus.UNAVAILABLE, reason="Synthetic test stage not configured"
        )
        for stage in REVIEW_STAGES
    }


def run_and_read(client, auth, identity):
    route = f"/api/v1/analyses/{identity}"
    assert client.post(route + "/run", headers=auth).status_code == 202
    summary = await_status(client, auth, identity, "partial")
    response = client.get(route + "/citations", headers=auth)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    return summary, response.json()


def local_analysis(document):
    analysis = Analysis(
        id=uuid4(),
        document_name="Synthetic citation sample",
        document_sha256=document.input_sha256,
        document_snapshot=document.model_dump(mode="json"),
        mode="live",
        court_profile_id="unverified",
        ai_used=False,
        status="running",
        stage_states={},
    )
    analysis.review_segments = tuple(
        ReviewSegment(id=uuid4(), start=p.start, end=p.end, page_number=p.page_number)
        for p in document.paragraphs
    )
    return analysis


def test_curated_pipeline_keeps_all_occurrences_without_source_verdicts(private_client, caplog):
    client, text = private_client, FIXTURE.read_text(encoding="utf-8")
    auth = owner(client)
    identity = prepare(client, auth, text=text)
    # Exercise the normal privacy/court/citation registration, not a mock pipeline.
    with caplog.at_level(logging.INFO, logger="filingguard.modules.analyses.orchestrator"):
        summary, response = run_and_read(client, auth, identity)
    rows = response["citations"]
    assert len(rows) == response["detected_count"] == 5
    assert [r["masked_raw_text"] for r in rows].count("347 U.S. 483") == 2
    assert response["stage"]["status"] == "partial"
    assert response["stage"]["coverage"]["evaluated"] == 0
    assert response["stage"]["coverage"]["unavailable"] == 5
    assert "lookup has not run" in response["stage"]["reason"]
    assert all(r["verification_status"] == "not_run" for r in rows)
    assert all(r["extraction"]["method"] == "eyecite-local-v1" for r in rows)
    assert all(
        text[r["location"]["start"] : r["location"]["end"]] == r["masked_raw_text"] for r in rows
    )
    assert summary["overall_score"] is None and summary["risk_level"] is None
    assert "900-12-3456" not in caplog.text and "347 U.S. 483" not in caplog.text
    factory = client.app.state.analysis_runtime.get_lifecycle().repository._factory
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(Authority)) == 0
        segments = {s.id for s in session.scalars(select(DocumentSegment))}
        assert all(UUID(r["location"]["segment_id"]) in segments for r in rows)
        assert all(r.authority_id is None for r in session.scalars(select(Citation)))


def test_owner_reads_rerun_expiry_and_delete_cascade(private_client):
    client = private_client
    first, second = owner(client), owner(client)
    citation_only(client)
    identity = prepare(client, first, text="See 347 U.S. 483 twice; 347 U.S. 483.")
    route = f"/api/v1/analyses/{identity}"
    before = client.get(route + "/citations", headers=first).json()
    assert before["stage"]["status"] == "not_run" and before["citations"] == []
    _, original = run_and_read(client, first, identity)
    assert client.get(route + "/citations", headers=second).status_code == 404
    assert client.get(route + "/citations").status_code == 401
    clone = client.post(route + "/rerun", headers=first)
    assert clone.status_code == 201, clone.text
    clone_id = clone.json()["analysis_id"]
    _, rerun = run_and_read(client, first, clone_id)
    assert {r["id"] for r in original["citations"]}.isdisjoint(r["id"] for r in rerun["citations"])
    assert client.get(route + "/citations", headers=first).json() == original
    assert client.delete(route, headers=first).status_code == 200
    assert client.get(route + "/citations", headers=first).status_code == 404
    factory = client.app.state.analysis_runtime.get_lifecycle().repository._factory
    with factory.begin() as session:
        assert (
            session.scalar(
                select(func.count())
                .select_from(Citation)
                .where(Citation.analysis_id == UUID(identity))
            )
            == 0
        )
        session.get(Analysis, UUID(clone_id)).expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert client.get(f"/api/v1/analyses/{clone_id}/citations", headers=first).status_code == 404


def test_truncation_is_explicit_and_does_not_clip_occurrences(private_client):
    client, text = private_client, "; ".join(["347 U.S. 483"] * 205)
    auth = owner(client)
    citation_only(client)
    _, result = run_and_read(client, auth, prepare(client, auth, text=text))
    assert result["detected_count"] == 205 and len(result["citations"]) == 200
    assert result["stage"]["coverage"]["truncated"] is True
    assert "first 200" in result["stage"]["coverage"]["limitation"]
    assert all(r["masked_raw_text"] == "347 U.S. 483" for r in result["citations"])


def test_ambiguous_unsupported_and_short_references_survive_pipeline(private_client):
    client = private_client
    auth = owner(client)
    citation_only(client)
    text = "1 Wash. 1; 123 QQQ 456; 42 U.S.C. § 1983. Id. at 2."
    _, result = run_and_read(client, auth, prepare(client, auth, text=text))
    supports = {r["extraction"]["support"] for r in result["citations"]}
    assert supports == {"ambiguous", "unsupported", "unresolved_reference"}
    assert all(r["normalized_text"] is None for r in result["citations"])
    assert all(r["verification_status"] == "not_run" for r in result["citations"])


def test_masking_uses_whole_snapshot_and_omits_sensitive_normalization(private_client):
    client = private_client
    auth = owner(client)
    citation_only(client)
    _, result = run_and_read(client, auth, prepare(client, auth, text="See 900 F.2d 123-45-6789."))
    assert len(result["citations"]) == 1
    row = result["citations"][0]
    assert row["masked_raw_text"].endswith("***")
    assert row["normalized_text"] is None
    assert "123-45-6789" not in str(result)
    assert "Heuristic" in result["masking_limitation"]


def test_empty_extraction_is_not_a_clean_filing_claim(private_client):
    client = private_client
    auth = owner(client)
    citation_only(client)
    summary, result = run_and_read(client, auth, prepare(client, auth))
    assert result["citations"] == [] and result["detected_count"] == 0
    assert result["stage"]["status"] == "skipped"
    assert result["stage"]["applicable"] is False
    assert "supported formats" in result["stage"]["reason"]
    assert "may be missed" in result["limitation"]
    assert summary["status"] == "partial" and summary["overall_score"] is None


@pytest.mark.parametrize("pdf", [False, True])
def test_cross_boundary_occurrence_keeps_original_anchor_and_warnings(pdf):
    text = "😀\n347 U.S." + ("\f" if pdf else "\n\n") + "483."
    if pdf:
        boundary = text.index("\f")
        pages = [
            PageSpan(page_number=1, start=0, end=boundary),
            PageSpan(page_number=2, start=boundary + 1, end=len(text)),
        ]
        document = ExtractedDocument(
            text=text,
            input_sha256="0" * 64,
            text_sha256=sha256(text.encode()).hexdigest(),
            pages=pages,
            paragraphs=segment(text, pages),
            method="pypdf-bounded-v1",
        )
    else:
        document = extract_text(text)
    analysis = local_analysis(document)
    budget = ProviderBudget(deadline=time.monotonic() + 30, max_attempts=60)
    result = execute_stage(
        citation_stage,
        analysis,
        StageName.CITATIONS,
        budget,
        stage_seconds=30,
        stop=Event(),
        segments=analysis.review_segments,
    )
    assert budget.attempts_used == 0
    assert result.status == StageStatus.PARTIAL and len(result.records) == 1
    row = result.records[0]
    assert row.start_offset == text.index("347")
    assert row.raw_text == text[row.start_offset : row.end_offset]
    assert row.segment_id == analysis.review_segments[0].id
    assert row.page_number == (1 if pdf else None)
    assert row.extraction_metadata["warnings"] == (
        ["cross_segment", "cross_page"] if pdf else ["cross_segment"]
    )
    assert row.extraction_metadata["support"] == "unsupported"


@pytest.mark.parametrize("verdict", ["verified", "not_found", "invalid", "unavailable"])
def test_partial_extraction_rejects_source_verdicts(verdict):
    analysis = local_analysis(extract_text("347 U.S. 483"))
    result = citation_stage(analysis, ProviderBudget(deadline=time.monotonic() + 30))
    result.records[0].verification_status = verdict
    with pytest.raises(ValueError, match="source verdicts"):
        result.validate(StageName.CITATIONS)


def test_partial_path_does_not_allow_authorities_findings_or_other_stages():
    analysis = local_analysis(extract_text("347 U.S. 483"))
    result = citation_stage(analysis, ProviderBudget(deadline=time.monotonic() + 30))
    wire = result_to_wire(result)
    restored = result_from_wire(wire, analysis.id)
    restored.validate(StageName.CITATIONS)
    validate_citation_records(analysis, analysis.review_segments, restored.records)
    for row in (Authority(analysis_id=analysis.id), Finding(analysis_id=analysis.id)):
        with pytest.raises(ValueError, match="source verdicts"):
            replace(result, records=(row,)).validate(StageName.CITATIONS)
    with pytest.raises(ValueError, match="partial-result path"):
        result.validate(StageName.QUOTES)
    with pytest.raises(ValueError, match="partial-result path"):
        replace(result, status=StageStatus.UNAVAILABLE).validate(StageName.CITATIONS)
    with pytest.raises(ValueError, match="partial-result path"):
        replace(result, coverage=Coverage(eligible=1, evaluated=1)).validate(StageName.CITATIONS)
    result.records[0].authority_id = uuid4()
    with pytest.raises(ValueError, match="source verdicts"):
        result.validate(StageName.CITATIONS)


def test_parent_rejects_forged_worker_offsets_and_does_not_persist_them(private_client):
    client = private_client
    auth = owner(client)
    citation_only(client, forged_citation)
    _, result = run_and_read(client, auth, prepare(client, auth, text="347 U.S. 483"))
    assert result["stage"]["status"] == "unavailable"
    assert result["citations"] == []
    assert result["stage"]["reason"] == "Contained review worker unavailable"


def test_corrupt_persisted_segments_fail_closed(private_client):
    client = private_client
    auth = owner(client)
    citation_only(client)
    identity = prepare(client, auth, text="347 U.S. 483")
    factory = client.app.state.analysis_runtime.get_lifecycle().repository._factory
    with factory.begin() as session:
        session.scalar(select(DocumentSegment)).text = "Synthetic corrupt paragraph"
    _, result = run_and_read(client, auth, identity)
    assert result["stage"]["status"] == "failed"
    assert result["citations"] == []
    assert result["stage"]["reason"] == "Review stage failed"


def test_review_citations_returns_stored_authority_and_provenance(private_client):
    client = private_client
    auth = owner(client)
    identity = UUID(prepare(client, auth, text="347 U.S. 483"))
    repo = client.app.state.analysis_runtime.get_lifecycle().repository
    holding_text = "Separate educational facilities are inherently unequal."
    auth_id = uuid4()
    authority = Authority(
        id=auth_id,
        analysis_id=identity,
        source="courtlistener",
        external_id="105221",
        case_name="Brown v. Board of Education",
        citation="347 U.S. 483",
        court="Supreme Court of the United States",
        year=1954,
        source_url="https://www.courtlistener.com/api/rest/v4/opinions/105221/",
        opinion_text_available=True,
        opinion_text=holding_text,
        source_sha256=sha256(holding_text.encode("utf-8")).hexdigest(),
        retrieved_at=datetime.now(UTC),
        source_metadata={
            "cluster_id": 105221,
            "opinion_id": 105221,
            "provider_opinion_type": "010combined",
            "text_field": "html_with_citations",
            "text_conversion": "htmlparser-block-boundaries-v1",
            "missing_text": False,
            "provenance": "courtlistener_api_v4",
            "attribution": (
                "Public US judicial opinion, retrieved from CourtListener / Free Law Project"
            ),
        },
    )

    with repo._factory() as session:
        segment_id = session.scalar(
            select(DocumentSegment.id).where(DocumentSegment.analysis_id == identity)
        )

    citation_id = uuid4()
    citation = Citation(
        id=citation_id,
        analysis_id=identity,
        raw_text="347 U.S. 483",
        normalized_text="347 U.S. 483",
        segment_id=segment_id,
        authority_id=auth_id,
        start_offset=0,
        end_offset=12,
        page_number=1,
        verification_status="verified",
        extraction_metadata={
            "parser_version": "2.5.0",
            "kind": "full_case",
            "support": "recognized",
        },
    )

    owner_hash = sha256(auth["Authorization"][7:].encode()).hexdigest()
    with repo.stage_update(
        owner_hash,
        identity,
        stage="citations",
        status="completed",
        coverage=Coverage(eligible=1, evaluated=1),
    ) as writer:
        writer.add(authority, citation)

    response = client.get(f"/api/v1/analyses/{identity}/citations", headers=auth)
    assert response.status_code == 200
    data = response.json()

    assert len(data["authorities"]) == 1
    stored_auth = data["authorities"][0]
    assert stored_auth["id"] == str(auth_id)
    assert stored_auth["case_name"] == "Brown v. Board of Education"
    assert stored_auth["court"] == "Supreme Court of the United States"
    assert stored_auth["year"] == 1954
    assert stored_auth["citation"] == "347 U.S. 483"
    assert stored_auth["source_url"] == "https://www.courtlistener.com/api/rest/v4/opinions/105221/"
    assert stored_auth["opinion_text_available"] is True
    assert stored_auth["opinion_text"] == holding_text
    assert len(stored_auth["source_sha256"]) == 64
    assert stored_auth["source_metadata"]["provenance"] == "courtlistener_api_v4"
    assert stored_auth["source_metadata"]["missing_text"] is False

    assert len(data["citations"]) == 1
    item = data["citations"][0]
    assert item["id"] == str(citation_id)
    assert item["verification_status"] == "verified"
    assert item["authority_id"] == str(auth_id)
    assert item["authority"]["case_name"] == "Brown v. Board of Education"
    assert item["authority"]["opinion_text"] == holding_text


def test_review_citations_distinguishes_missing_text_authority(private_client):
    client = private_client
    auth = owner(client)
    identity = UUID(prepare(client, auth, text="347 U.S. 483"))
    repo = client.app.state.analysis_runtime.get_lifecycle().repository
    auth_id = uuid4()
    authority = Authority(
        id=auth_id,
        analysis_id=identity,
        source="courtlistener",
        external_id="99999",
        case_name="Unpublished Order",
        citation="347 U.S. 483",
        court="scotus",
        year=2020,
        source_url="https://www.courtlistener.com/opinion/99999/",
        opinion_text_available=False,
        opinion_text=None,
        source_sha256=None,
        retrieved_at=datetime.now(UTC),
        source_metadata={
            "cluster_id": 99999,
            "opinion_id": None,
            "missing_text": True,
            "reason": "opinion_text_empty",
            "provenance": "courtlistener_api_v4",
        },
    )

    with repo._factory() as session:
        segment_id = session.scalar(
            select(DocumentSegment.id).where(DocumentSegment.analysis_id == identity)
        )

    citation = Citation(
        id=uuid4(),
        analysis_id=identity,
        raw_text="347 U.S. 483",
        normalized_text="347 U.S. 483",
        segment_id=segment_id,
        authority_id=auth_id,
        start_offset=0,
        end_offset=12,
        page_number=1,
        verification_status="verified",
        extraction_metadata={
            "parser_version": "2.5.0",
            "kind": "full_case",
            "support": "recognized",
        },
    )

    owner_hash = sha256(auth["Authorization"][7:].encode()).hexdigest()
    with repo.stage_update(
        owner_hash,
        identity,
        stage="citations",
        status="completed",
        coverage=Coverage(eligible=1, evaluated=1),
    ) as writer:
        writer.add(authority, citation)

    response = client.get(f"/api/v1/analyses/{identity}/citations", headers=auth)
    assert response.status_code == 200
    data = response.json()

    assert len(data["authorities"]) == 1
    stored_auth = data["authorities"][0]
    assert stored_auth["opinion_text_available"] is False
    assert stored_auth["opinion_text"] is None
    assert stored_auth["source_sha256"] is None
    assert stored_auth["source_metadata"]["missing_text"] is True
    assert stored_auth["source_metadata"]["reason"] == "opinion_text_empty"


def test_pipeline_deduplicates_repeated_citations_and_shares_authority(private_client):
    client = private_client
    auth = owner(client)
    text = (
        "In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court ruled.\n\n"
        "Later in the brief, 347 U.S. 483 was cited a second time."
    )
    identity = UUID(prepare(client, auth, text=text))
    repo = client.app.state.analysis_runtime.get_lifecycle().repository

    lookup_calls = 0
    opinion_calls = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
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

    from filingguard.integrations.courtlistener import CourtListenerAdapter
    from filingguard.modules.analyses.execution import ReviewSegment, citation_anchor
    from filingguard.modules.citations.service import (
        extract_citations,
        verify_citations_for_analysis,
    )

    extraction = extract_citations(text)
    assert extraction.detected_count == 2  # Exactly 2 occurrences detected

    with repo._factory() as session:
        segments = session.scalars(
            select(DocumentSegment).where(DocumentSegment.analysis_id == identity)
        ).all()
        review_segs = tuple(
            ReviewSegment(
                id=s.id, start=s.start_offset, end=s.end_offset, page_number=s.page_number
            )
            for s in segments
        )

    records = []
    for item in extraction.occurrences:
        anchor, warnings = citation_anchor(review_segs, item.start, item.end)
        metadata = item.extraction.model_copy(update={"warnings": warnings})
        records.append(
            Citation(
                id=uuid4(),
                analysis_id=identity,
                raw_text=item.raw_text,
                normalized_text=item.normalized_text,
                segment_id=anchor.id,
                page_number=anchor.page_number,
                start_offset=item.start,
                end_offset=item.end,
                extraction_metadata=metadata.model_dump(mode="json"),
                verification_status="not_run",
                authority_id=None,
            )
        )

    adapter = CourtListenerAdapter(
        token="test-pipeline-token",
        budget=ProviderBudget(deadline=time.monotonic() + 30.0),
        transport=httpx.MockTransport(mock_handler),
    )

    verified_citations, authorities = verify_citations_for_analysis(identity, records, adapter)

    # Outbound lookups deduplicated!
    assert lookup_calls == 1
    assert opinion_calls == 1

    owner_hash = sha256(auth["Authorization"][7:].encode()).hexdigest()
    with repo.stage_update(
        owner_hash,
        identity,
        stage="citations",
        status="completed",
        coverage=Coverage(eligible=2, evaluated=2),
    ) as writer:
        writer.add(*(authorities + verified_citations))

    # Query via HTTP API endpoint
    response = client.get(f"/api/v1/analyses/{identity}/citations", headers=auth)
    assert response.status_code == 200
    data = response.json()

    # Verify deduplication in stored API response
    assert len(data["authorities"]) == 1
    assert len(data["citations"]) == 2

    shared_auth = data["authorities"][0]
    assert shared_auth["case_name"] == "Brown v. Board of Education"
    assert shared_auth["citation"] == "347 U.S. 483"
    assert shared_auth["opinion_text_available"] is True
    assert "Separate educational facilities are inherently unequal." in shared_auth["opinion_text"]

    c1 = data["citations"][0]
    c2 = data["citations"][1]

    # Both link to the same authority
    assert c1["authority_id"] == shared_auth["id"]
    assert c2["authority_id"] == shared_auth["id"]
    assert c1["authority"]["id"] == shared_auth["id"]
    assert c2["authority"]["id"] == shared_auth["id"]
    assert c1["verification_status"] == "verified"
    assert c2["verification_status"] == "verified"

    # Both original locations remain inspectable!
    assert c1["location"]["start"] == 32
    assert c1["location"]["end"] == 44
    assert c1["location"]["start"] != c2["location"]["start"]
    assert text[c1["location"]["start"] : c1["location"]["end"]] == "347 U.S. 483"
    assert text[c2["location"]["start"] : c2["location"]["end"]] == "347 U.S. 483"

    # Direct database check
    with repo._factory() as session:
        auth_count = session.scalar(
            select(func.count()).select_from(Authority).where(Authority.analysis_id == identity)
        )
        assert auth_count == 1
        cit_count = session.scalar(
            select(func.count()).select_from(Citation).where(Citation.analysis_id == identity)
        )
        assert cit_count == 2


def test_pipeline_caches_not_found_repeats_without_authority(private_client):
    client = private_client
    auth = owner(client)
    text = "First fake citation: 999 U.S. 123.\n\nSecond fake citation: 999 U.S. 123."
    identity = UUID(prepare(client, auth, text=text))
    repo = client.app.state.analysis_runtime.get_lifecycle().repository

    lookup_calls = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal lookup_calls
        if "/citation-lookup/" in request.url.path:
            lookup_calls += 1
            return httpx.Response(
                200,
                json=[{"status": 404, "normalized_citations": [], "clusters": []}],
            )
        return httpx.Response(404)

    from filingguard.integrations.courtlistener import CourtListenerAdapter
    from filingguard.modules.analyses.execution import ReviewSegment, citation_anchor
    from filingguard.modules.citations.service import (
        extract_citations,
        verify_citations_for_analysis,
    )

    extraction = extract_citations(text)
    assert extraction.detected_count == 2

    with repo._factory() as session:
        segments = session.scalars(
            select(DocumentSegment).where(DocumentSegment.analysis_id == identity)
        ).all()
        review_segs = tuple(
            ReviewSegment(
                id=s.id, start=s.start_offset, end=s.end_offset, page_number=s.page_number
            )
            for s in segments
        )

    records = []
    for item in extraction.occurrences:
        anchor, warnings = citation_anchor(review_segs, item.start, item.end)
        metadata = item.extraction.model_copy(update={"warnings": warnings})
        records.append(
            Citation(
                id=uuid4(),
                analysis_id=identity,
                raw_text=item.raw_text,
                normalized_text=item.normalized_text,
                segment_id=anchor.id,
                page_number=anchor.page_number,
                start_offset=item.start,
                end_offset=item.end,
                extraction_metadata=metadata.model_dump(mode="json"),
                verification_status="not_run",
                authority_id=None,
            )
        )

    adapter = CourtListenerAdapter(
        token="test-pipeline-token",
        budget=ProviderBudget(deadline=time.monotonic() + 30.0),
        transport=httpx.MockTransport(mock_handler),
    )

    verified_citations, authorities = verify_citations_for_analysis(identity, records, adapter)

    # Exactly 1 outbound call despite 2 occurrences!
    assert lookup_calls == 1
    assert len(authorities) == 0

    owner_hash = sha256(auth["Authorization"][7:].encode()).hexdigest()
    with repo.stage_update(
        owner_hash,
        identity,
        stage="citations",
        status="completed",
        coverage=Coverage(eligible=2, evaluated=2),
    ) as writer:
        writer.add(*verified_citations)

    response = client.get(f"/api/v1/analyses/{identity}/citations", headers=auth)
    assert response.status_code == 200
    data = response.json()

    assert len(data["authorities"]) == 0
    assert len(data["citations"]) == 2
    assert data["citations"][0]["verification_status"] == "not_found"
    assert data["citations"][1]["verification_status"] == "not_found"
    assert data["citations"][0]["authority_id"] is None
    assert data["citations"][1]["authority_id"] is None
    assert data["citations"][0]["location"]["start"] != data["citations"][1]["location"]["start"]
