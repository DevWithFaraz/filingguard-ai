import hashlib
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from filingguard.api.contracts import (
    AnalysisAccepted,
    CourtProfileSummary,
    DeleteResponse,
    FindingsResponse,
    GraphResponse,
    TextSubmission,
    contract_definitions,
)
from filingguard.modules.analyses.schemas import (
    AnalysisSummary,
    CitationResult,
    Confidence,
    Coverage,
    DocumentLocation,
    FindingRecord,
    PropositionResult,
    QuoteResult,
    StageName,
    StageState,
)
from filingguard.modules.evidence.schemas import EvidenceRecord, validate_snapshot


def summary(**overrides):
    return AnalysisSummary.model_validate(
        {
            "analysis_id": uuid4(),
            "mode": "live",
            "court_profile_id": "synthetic-demo-v1",
            "created_at": datetime.now(UTC),
            **overrides,
        }
    )


def evidence(source="a filing paragraph", **overrides):
    return EvidenceRecord.model_validate(
        {
            "id": uuid4(),
            "analysis_id": uuid4(),
            "source_type": "document",
            "source_label": "Extracted filing",
            "retrieved_at": datetime.now(UTC),
            "snapshot_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "excerpt": source,
            "start": 0,
            "end": len(source),
            "method_version": "extract-v1",
            "provenance": "synthetic",
            **overrides,
        }
    )


def test_defaults_are_not_run_and_unscored():
    assert summary().status == "not_run"
    assert summary().overall_score is None
    assert summary().risk_level is None
    assert CitationResult(citation_id=uuid4()).status == "not_run"
    assert PropositionResult(claim_id=uuid4()).status == "not_run"
    assert QuoteResult(quote_id=uuid4()).status == "not_run"
    assert StageState(name="quotes").coverage.evaluated == 0
    assert not Coverage().complete


@pytest.mark.parametrize("status", ["partial", "unavailable", "failed", "interrupted", "skipped"])
def test_incomplete_stages_need_reasons(status):
    with pytest.raises(ValidationError):
        StageState(name="quotes", status=status)
    assert (
        StageState(
            name="quotes", status=status, reason="Check unavailable", applicable=status != "skipped"
        ).status
        == status
    )


def test_completed_stage_cannot_hide_partial_coverage():
    with pytest.raises(ValidationError):
        StageState(name="quotes", status="completed", coverage=Coverage(eligible=1, unavailable=1))
    with pytest.raises(ValidationError):
        StageState(name="quotes", coverage=Coverage(eligible=1, evaluated=1))


@pytest.mark.parametrize(
    "counts",
    [
        {"eligible": 2, "evaluated": 1},
        {"eligible": 1, "evaluated": 2},
        {"eligible": -1},
        {"eligible": True},
        {"truncated": True},
    ],
)
def test_invalid_coverage_rejected(counts):
    with pytest.raises(ValidationError):
        Coverage(**counts)


def test_completed_analysis_requires_all_stages():
    with pytest.raises(ValidationError):
        summary(status="completed")
    stages = [StageState(name=name, status="completed") for name in StageName]
    assert summary(status="completed", stages=stages).overall_score is None
    with pytest.raises(ValidationError):
        summary(stages=[stages[0], stages[0]])


def test_missing_checks_cannot_imply_readiness():
    with pytest.raises(ValidationError):
        summary(overall_score=100)
    with pytest.raises(ValidationError):
        summary(risk_level="ready_for_review")
    with pytest.raises(ValidationError):
        summary(
            status="partial",
            overall_score=90,
            risk_level="ready_for_review",
            coverage=Coverage(eligible=2, evaluated=1, unavailable=1),
        )
    with pytest.raises(ValidationError):
        summary(
            overall_score=100,
            coverage=Coverage(eligible=1, evaluated=1),
            score_is_provisional=False,
        )


def test_demo_must_be_explicit():
    assert summary(mode="demo", demo_fixture_id="fixture-v1").mode == "demo"
    with pytest.raises(ValidationError):
        summary(mode="demo")
    with pytest.raises(ValidationError):
        summary(demo_fixture_id="fixture-v1")


def test_verified_citation_requires_source_identity_and_evidence():
    with pytest.raises(ValidationError):
        CitationResult(citation_id=uuid4(), status="verified")
    with pytest.raises(ValidationError):
        CitationResult(citation_id=uuid4(), status="verified", authority_id=uuid4())
    with pytest.raises(ValidationError):
        CitationResult(citation_id=uuid4(), status="unavailable")
    assert (
        CitationResult(
            citation_id=uuid4(), status="verified", authority_id=uuid4(), evidence_ids=[uuid4()]
        ).status
        == "verified"
    )


@pytest.mark.parametrize("status", ["supported", "partially_supported", "misrepresented"])
def test_semantic_verdict_requires_evidence(status):
    with pytest.raises(ValidationError):
        PropositionResult(claim_id=uuid4(), status=status, explanation="Conclusion")


def test_ai_identity_is_required():
    with pytest.raises(ValidationError):
        PropositionResult(claim_id=uuid4(), ai_used=True)
    with pytest.raises(ValidationError):
        evidence(source_type="ai_analysis")
    assert (
        PropositionResult(
            claim_id=uuid4(), ai_used=True, model_version="model-v1", prompt_version="prompt-v1"
        ).status
        == "not_run"
    )


@pytest.mark.parametrize("status", ["exact", "normalized", "close"])
def test_quote_match_requires_sourced_passage(status):
    with pytest.raises(ValidationError):
        QuoteResult(quote_id=uuid4(), status=status, similarity=1)
    assert (
        QuoteResult(
            quote_id=uuid4(), status=status, method_version="match-v1", evidence_ids=[uuid4()]
        ).status
        == status
    )


def test_unavailable_quote_has_no_similarity():
    with pytest.raises(ValidationError):
        QuoteResult(quote_id=uuid4(), status="source_unavailable", similarity=0)


@pytest.mark.parametrize("value", [-0.1, 1.1, float("nan"), float("inf")])
def test_confidence_range(value):
    with pytest.raises(ValidationError):
        Confidence(value=value, level="high", method="heuristic-v1")


def test_confidence_is_not_a_calibrated_probability():
    with pytest.raises(ValidationError):
        Confidence(value=0.8)
    assert not Confidence(value=0.8, level="high", method="heuristic-v1").calibrated


def test_span_and_unicode_snapshot_integrity():
    source = "A \U0001f600 court sentence"
    record = evidence(source, excerpt=source[2:3], start=2, end=3)
    validate_snapshot(record, source)
    with pytest.raises(ValueError, match="hash"):
        validate_snapshot(record, source + " changed")
    record = record.model_copy(update={"excerpt": "B"})
    with pytest.raises(ValueError, match="passage"):
        validate_snapshot(record, source)
    with pytest.raises(ValidationError):
        DocumentLocation(start=2, end=2)


def test_evidence_rejects_missing_provenance_and_credentials():
    with pytest.raises(ValidationError):
        evidence(source_url="https://user:password@example.com/opinion")
    with pytest.raises(ValidationError):
        evidence(source_type="rule")
    with pytest.raises(ValidationError):
        EvidenceRecord(id=uuid4(), analysis_id=uuid4())


def test_findings_require_evidence():
    with pytest.raises(ValidationError):
        FindingRecord(
            id=uuid4(),
            analysis_id=uuid4(),
            type="quote",
            severity="high",
            title="Quote mismatch",
            description="Needs source review",
            evidence_ids=[],
        )


def test_submission_limits_and_no_fake_accepted_defaults():
    for text in ["", "   ", "x" * 100001]:
        with pytest.raises(ValidationError):
            TextSubmission(document_name="Motion", text=text, court_profile_id="demo", ai_used=True)
    with pytest.raises(ValidationError):
        TextSubmission(
            document_name="Motion", text="Text", court_profile_id="demo", ai_used=True, mode="demo"
        )
    with pytest.raises(ValidationError):
        AnalysisAccepted(analysis_id=uuid4(), mode="live")


def test_openapi_components_and_review_routes_are_declared():
    definitions = contract_definitions()
    assert "AnalysisSummary" in definitions
    assert "EvidenceRecord" in definitions
    assert "ApiError" in definitions
    assert definitions["SafeCitationsResponse"]["properties"]["citations"]["maxItems"] == 200
    from filingguard.main import create_app

    assert set(create_app().openapi()["paths"]) == {
        "/api/v1/health",
        "/api/v1/ready",
        "/api/v1/demos/{fixture_id}",
        "/api/v1/capabilities",
        "/api/v1/court-profiles",
        "/api/v1/sessions",
        "/api/v1/analyses",
        "/api/v1/analyses/text",
        "/api/v1/analyses/file",
        "/api/v1/analyses/demo",
        "/api/v1/analyses/{analysis_id}",
        "/api/v1/analyses/{analysis_id}/status",
        "/api/v1/analyses/{analysis_id}/run",
        "/api/v1/analyses/{analysis_id}/findings",
        "/api/v1/analyses/{analysis_id}/rerun",
        "/api/v1/analyses/{analysis_id}/citations",
        "/api/v1/analyses/{analysis_id}/results",
        "/api/v1/analyses/{analysis_id}/graph",
        "/api/v1/analyses/{analysis_id}/report",
        "/api/v1/analyses/{analysis_id}/findings/{finding_id}/evidence",
        "/api/v1/analyses/{analysis_id}/findings/{finding_id}/questions",
        "/api/v1/analyses/{analysis_id}/red-team",
    }


def test_coverage_is_reconciled_and_skips_cannot_hide_checks():
    skips = [
        StageState(name=name, status="skipped", applicable=False, reason="Not applicable")
        for name in StageName
    ]
    with pytest.raises(ValidationError):
        summary(
            status="completed",
            stages=skips,
            coverage=Coverage(eligible=1, evaluated=1),
            overall_score=100,
            score_is_provisional=False,
            risk_level="ready_for_review",
        )
    with pytest.raises(ValidationError):
        StageState(name="quotes", status="skipped", reason="Provider failed")
    with pytest.raises(ValidationError):
        StageState(
            name="quotes",
            status="skipped",
            applicable=False,
            reason="No source",
            coverage=Coverage(eligible=1, unavailable=1),
        )
    stages = [StageState(name=name, status="completed") for name in StageName]
    stages[0] = StageState(
        name="document", status="completed", coverage=Coverage(eligible=1, evaluated=1)
    )
    assert (
        summary(
            status="completed",
            stages=stages,
            coverage=Coverage(eligible=1, evaluated=1),
            overall_score=80,
            score_is_provisional=False,
            risk_level="needs_review",
        ).overall_score
        == 80
    )
    with pytest.raises(ValidationError):
        summary(stages=stages, coverage=Coverage(eligible=1, evaluated=1), overall_score=100)


def test_response_records_cannot_cross_analyses_or_dangle():
    analysis_id, finding_id = uuid4(), uuid4()
    record = evidence(analysis_id=analysis_id, finding_id=finding_id)
    finding = FindingRecord(
        id=finding_id,
        analysis_id=analysis_id,
        type="quote",
        severity="high",
        title="Quote mismatch",
        description="Human review required",
        evidence_ids=[record.id],
    )
    assert FindingsResponse(analysis_id=analysis_id, findings=[finding], evidence=[record])
    with pytest.raises(ValidationError):
        FindingsResponse(analysis_id=uuid4(), findings=[finding], evidence=[record])
    with pytest.raises(ValidationError):
        FindingsResponse(analysis_id=analysis_id, findings=[finding], evidence=[])
    with pytest.raises(ValidationError):
        FindingsResponse(analysis_id=analysis_id, findings=[finding], evidence=[record, record])


def test_strict_booleans_labels_and_source_identity():
    with pytest.raises(ValidationError):
        TextSubmission(
            document_name="Motion", text="Filing", court_profile_id="court", ai_used="no"
        )
    with pytest.raises(ValidationError):
        DeleteResponse(analysis_id=uuid4(), deleted=1)
    with pytest.raises(ValidationError):
        Confidence(value=True, level="high", method="heuristic")
    with pytest.raises(ValidationError):
        Confidence(level="high", method="  ")
    with pytest.raises(ValidationError):
        evidence(source_type="opinion_text")
    with pytest.raises(ValidationError):
        CourtProfileSummary(
            id="demo", version="v1", name="Demo", is_demo=True, applicability="verified_scope"
        )
    with pytest.raises(ValidationError):
        PropositionResult(claim_id=uuid4(), model_version="model", prompt_version="v1")
    with pytest.raises(ValidationError):
        PropositionResult(claim_id=uuid4(), confidence=Confidence(level="high"))
    with pytest.raises(ValidationError):
        QuoteResult(
            quote_id=uuid4(),
            status="exact",
            similarity=0,
            method_version="v1",
            evidence_ids=[uuid4()],
        )


def test_graph_edges_cannot_reference_missing_nodes():
    with pytest.raises(ValidationError):
        GraphResponse(
            analysis_id=uuid4(),
            nodes=[],
            edges=[
                {
                    "id": uuid4(),
                    "source": uuid4(),
                    "target": uuid4(),
                    "type": "cites",
                }
            ],
        )
