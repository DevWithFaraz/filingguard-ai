"""Verification records survive completed/partial boundaries without false negatives."""

import time
from uuid import uuid4

import httpx
import pytest

from filingguard.db.models import Analysis, Authority, Citation
from filingguard.integrations.courtlistener import CourtListenerAdapter
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.execution import ReviewSegment, validate_citation_records
from filingguard.modules.analyses.schemas import StageName, StageStatus
from filingguard.modules.citations.runner import verified_citation_stage
from filingguard.modules.documents.extraction import extract_text


def run_stage(text, *, failing_status=None, missing=False):
    document = extract_text(text)
    analysis = Analysis(id=uuid4(), document_snapshot=document.model_dump(mode="json"))
    analysis.review_segments = tuple(ReviewSegment(id=uuid4(), start=p.start, end=p.end,
                                                   page_number=p.page_number)
                                     for p in document.paragraphs)
    budget = ProviderBudget(deadline=time.monotonic() + 30, max_attempts=60)
    calls = []

    def handler(request):
        calls.append(request.url.path)
        if "citation-lookup" in request.url.path:
            if failing_status and "576" in request.read().decode():
                return httpx.Response(failing_status)
            if missing:
                return httpx.Response(200, json=[{"status": 404, "clusters": []}])
            return httpx.Response(200, json=[{
                "status": 200, "normalized_citations": ["347 U.S. 483"],
                "clusters": [{"id": 105221, "case_name": "Synthetic example",
                              "sub_opinions": [105221]}],
            }])
        return httpx.Response(200, json={"id": 105221, "type": "010combined",
                                       "plain_text": "Public synthetic opinion text."})

    adapter = CourtListenerAdapter(token="SYNTHETIC_COURTLISTENER_TOKEN", budget=budget,
                                  transport=httpx.MockTransport(handler))
    try:
        result = verified_citation_stage(analysis, budget, adapter=adapter)
    finally:
        adapter.close()
    result.validate(StageName.CITATIONS)
    citations = tuple(row for row in result.records if isinstance(row, Citation))
    validate_citation_records(analysis, analysis.review_segments, citations)
    return result, citations, calls


def test_verified_result_allows_authority_and_original_occurrences():
    text = "😀 A rule follows 347 U.S. 483. The same rule follows 347 U.S. 483."
    result, citations, calls = run_stage(text)
    assert result.status == StageStatus.COMPLETED and result.coverage.evaluated == 2
    assert len(result.records) == 3 and len(citations) == 2
    assert len([row for row in result.records if isinstance(row, Authority)]) == 1
    assert calls == ["/api/rest/v4/citation-lookup/", "/api/rest/v4/opinions/105221/"]
    assert all(row.verification_status == "verified" for row in citations)
    assert all(text[row.start_offset:row.end_offset] == row.raw_text for row in citations)


@pytest.mark.parametrize("status", [401, 429, 503])
def test_unavailable_stage_is_partial_with_reason_and_never_not_found(status):
    result, citations, _ = run_stage("A rule follows 576 U.S. 644.", failing_status=status)
    assert result.status == StageStatus.PARTIAL
    assert result.coverage.eligible == result.coverage.unavailable == 1
    assert result.coverage.evaluated == 0
    assert citations[0].verification_status == "unavailable"
    receipt = citations[0].extraction_metadata["verification"]
    assert receipt["reason"] and receipt["limitation"] and receipt["retrieved_at"]


def test_mixed_results_preserve_success_and_unavailable_occurrence():
    result, citations, _ = run_stage("A rule follows 347 U.S. 483; another 576 U.S. 644.",
                                     failing_status=401)
    assert result.status == StageStatus.PARTIAL
    assert result.coverage.evaluated == result.coverage.unavailable == 1
    assert len([row for row in result.records if isinstance(row, Authority)]) == 1
    assert [row.verification_status for row in citations] == ["verified", "unavailable"]
    assert citations[0].authority_id and citations[1].authority_id is None


def test_short_reference_is_unrun_and_does_not_inherit_authority():
    result, citations, calls = run_stage("The rule follows 347 U.S. 483. Id. at 484.")
    assert result.status == StageStatus.PARTIAL and result.coverage.unavailable == 1
    assert [row.verification_status for row in citations] == ["verified", "not_run"]
    assert citations[1].authority_id is None and len(calls) == 2


@pytest.mark.parametrize("count", [200, 201])
def test_occurrence_boundary_handles_authority_rows_and_reports_truncation(count):
    result, citations, calls = run_stage("; ".join(["347 U.S. 483"] * count))
    assert len(citations) == 200 and len(result.records) == 201 and len(calls) == 2
    assert result.coverage.eligible == count and result.coverage.evaluated == 200
    assert result.coverage.unavailable == count - 200
    assert result.coverage.truncated == (count == 201)
    assert result.status == (StageStatus.COMPLETED if count == 200 else StageStatus.PARTIAL)


def test_database_absence_retains_coverage_warning():
    result, citations, _ = run_stage("A rule follows 347 U.S. 483.", missing=True)
    assert result.coverage.evaluated == 1 and citations[0].verification_status == "not_found"
    receipt = citations[0].extraction_metadata["verification"]
    assert receipt["reason"] == "not_found_in_courtlistener_database"
    limitation = receipt["limitation"].lower()
    assert "fabricat" in limitation or "coverage" in limitation
