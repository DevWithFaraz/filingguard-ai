import hashlib
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from test_orchestrator import owner, prepare
from test_orchestrator import private_client as private_client

from filingguard.db.models import (
    Analysis,
    Authority,
    Citation,
    Claim,
    ClaimAuthorityLink,
    DocumentSegment,
    EvidenceRecord,
    Finding,
)
from filingguard.db.repository import AnalysisNotFound
from filingguard.modules.analyses.schemas import Coverage
from filingguard.modules.citations.service import extract_citations
from filingguard.modules.reports.service import (
    render_report,
    saved_evidence,
    saved_graph,
    saved_results,
)

FILING = "SSN 123-45-6789. Notice is required under 347 U.S. 483."
SOURCE = "Notice is required. However, emergencies are excepted."
MODEL = "openai/gpt-oss-120b"
PROMPT = "proposition-source-review-v1"


def seed(client, auth):
    identity = UUID(prepare(client, auth, text=FILING))
    repository = client.app.state.analysis_runtime.get_lifecycle().repository
    with repository._factory() as session:
        analysis = session.get(Analysis, identity)
        owner_hash = analysis.owner_hash
        segment = session.scalar(
            select(DocumentSegment).where(DocumentSegment.analysis_id == identity)
        )
    authority_id, citation_id, claim_id, finding_id = uuid4(), uuid4(), uuid4(), uuid4()
    parsed = extract_citations(FILING).occurrences[0]
    with repository.stage_update(
        owner_hash, identity, "citations", "completed", coverage=Coverage(eligible=1, evaluated=1)
    ) as writer:
        writer.add(
            Authority(
                id=authority_id,
                source="courtlistener",
                external_id="123",
                case_name="Synthetic notice case",
                source_url="https://www.courtlistener.com/opinion/123/",
                opinion_text_available=True,
                opinion_text=SOURCE,
                source_sha256=hashlib.sha256(SOURCE.encode()).hexdigest(),
                retrieved_at=datetime.now(UTC),
            )
        )
        writer.add(
            Citation(
                id=citation_id,
                raw_text=parsed.raw_text,
                normalized_text=parsed.normalized_text,
                start_offset=parsed.start,
                end_offset=parsed.end,
                segment_id=segment.id,
                page_number=None,
                authority_id=authority_id,
                extraction_metadata=parsed.extraction.model_dump(),
                verification_status="verified",
            )
        )
    with repository.stage_update(
        owner_hash, identity, "claims", "completed", coverage=Coverage(eligible=1, evaluated=1)
    ) as writer:
        writer.add(
            Claim(
                id=claim_id,
                text=FILING,
                segment_id=segment.id,
                start_offset=0,
                end_offset=len(FILING),
                extraction_method="heuristic",
            )
        )
        writer.add(
            ClaimAuthorityLink(
                id=uuid4(),
                claim_id=claim_id,
                citation_id=citation_id,
                authority_id=authority_id,
                support_status="partially_supported",
                confidence=None,
                explanation="SSN 123-45-6789: notice has an emergency exception.",
            )
        )
    left = FILING.index("123-45-6789") + 4
    right = left + 7
    with repository.stage_update(
        owner_hash,
        identity,
        "propositions",
        "completed",
        analysis_status="partial",
        coverage=Coverage(eligible=1, evaluated=1),
    ) as writer:
        writer.add(
            Finding(
                id=finding_id,
                type="claim_support",
                severity="medium",
                title="Review notice qualifications",
                description="Model echoed 123-45-6789.",
                status="open",
                stage="propositions",
                segment_id=segment.id,
                claim_id=claim_id,
                citation_id=citation_id,
                authority_id=authority_id,
                start_offset=left,
                end_offset=right,
                document_excerpt=FILING[left:right],
                ai_assisted=True,
            )
        )
        common = dict(
            finding_id=finding_id,
            segment_id=segment.id,
            claim_id=claim_id,
            citation_id=citation_id,
            authority_id=authority_id,
            start_offset=left,
            end_offset=right,
            method="grounded_proposition_review",
            method_version="grounded-proposition-review-v1",
            model_version=MODEL,
            prompt_version=PROMPT,
            retrieved_at=datetime.now(UTC),
            source_metadata={
                "provenance": "synthetic",
                "confidence_level": "medium",
                "external_id": "123",
            },
        )
        writer.add(
            EvidenceRecord(
                id=uuid4(),
                source_type="document",
                source_label="Original filing",
                excerpt=FILING[left:right],
                snapshot_text=FILING,
                source_url=None,
                source_sha256=hashlib.sha256(FILING.encode()).hexdigest(),
                source_start_offset=left,
                source_end_offset=right,
                **common,
            )
        )
        writer.add(
            EvidenceRecord(
                id=uuid4(),
                source_type="opinion_text",
                source_label="Source opinion",
                excerpt=SOURCE,
                snapshot_text=SOURCE,
                source_url="https://www.courtlistener.com/opinion/123/",
                source_sha256=hashlib.sha256(SOURCE.encode()).hexdigest(),
                source_start_offset=0,
                source_end_offset=len(SOURCE),
                **common,
            )
        )
    with repository.stage_update(
        owner_hash,
        identity,
        "quotes",
        "unavailable",
        reason="No source quote comparison",
        coverage=Coverage(eligible=1, unavailable=1),
    ):
        pass
    return repository, owner_hash, identity, finding_id


def test_saved_results_graph_evidence_and_report_agree(private_client, monkeypatch):
    client = private_client
    auth = owner(client)
    repository, owned, identity, finding_id = seed(client, auth)
    monkeypatch.setattr(
        "filingguard.integrations.llm.adapter.GroqPropositionAdapter.review",
        lambda *a, **k: pytest.fail("Saved result reclassified with provider"),
    )
    results = saved_results(repository, owned, identity)
    graph = saved_graph(repository, owned, identity)
    evidence = saved_evidence(repository, owned, identity, finding_id)
    assert results["score"]["value"] == 92
    assert results["score"]["provisional"]
    assert results["coverage"]["unavailable"] == 1
    assert graph["edges"][-1]["label"] == results["claims"][0]["links"][0]["support_status"]
    assert any(str(finding_id) in node["finding_ids"] for node in graph["nodes"])
    source = next(e for e in evidence["evidence"] if e["source_url"])
    assert source["excerpt"] == SOURCE
    assert source["source_sha256"] == hashlib.sha256(SOURCE.encode()).hexdigest()
    assert source["model_version"] == MODEL and source["prompt_version"] == PROMPT
    assert source["method_version"] == "grounded-proposition-review-v1"
    assert source["confidence_level"] == "medium"
    assert results["findings"][0]["evidence_count"] == len(evidence["evidence"])
    report = render_report(results)
    assert str(identity) in report and "92" in report
    assert SOURCE in report and MODEL in report and PROMPT in report
    assert source["source_sha256"] in report
    assert source["source_url"] in report
    assert "uncalibrated" in report


def test_full_filing_detection_masks_clipped_results_and_evidence(private_client):
    client = private_client
    repository, owned, identity, finding_id = seed(client, owner(client))
    results = saved_results(repository, owned, identity)
    evidence = saved_evidence(repository, owned, identity, finding_id)
    assert results["findings"][0]["masked_excerpt"] == "*******"
    assert "123-45-6789" not in results["findings"][0]["description"]
    document = next(e for e in evidence["evidence"] if e["source_url"] is None)
    assert document["excerpt"] == "*******"
    assert "123-45-6789" not in results["claims"][0]["links"][0]["explanation"]


def test_saved_data_is_owner_scoped_at_every_detail_boundary(private_client):
    client = private_client
    repository, _, identity, finding_id = seed(client, owner(client))
    for access, extra in [(saved_results, ()), (saved_graph, ()), (saved_evidence, (finding_id,))]:
        with pytest.raises(AnalysisNotFound):
            access(repository, "f" * 64, identity, *extra)


def test_results_routes_share_saved_identity_and_provenance(private_client):
    client = private_client
    auth, other = owner(client), owner(client)
    _, _, identity, finding_id = seed(client, auth)
    route = f"/api/v1/analyses/{identity}"
    result = client.get(route + "/results", headers=auth)
    assert result.status_code == 200, result.text
    assert result.json()["analysis_id"] == str(identity)
    for suffix in ("/results", "/graph", f"/findings/{finding_id}/evidence", "/report?format=html"):
        response = client.get(route + suffix, headers=auth)
        assert response.status_code == 200, response.text
        assert response.headers["cache-control"] == "no-store"
        assert client.get(route + suffix, headers=other).status_code == 404
    detail = client.get(route + f"/findings/{finding_id}/evidence", headers=auth).json()
    assert any(row["model_version"] == MODEL for row in detail["evidence"])
    pdf_res = client.get(route + "/report?format=pdf", headers=auth)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert f'filename="filingguard-{identity}.pdf"' in pdf_res.headers["content-disposition"]
    assert pdf_res.content.startswith(b"%PDF-1.")
    assert client.get(route + "/report?format=xml", headers=auth).status_code == 422


def test_active_results_cannot_claim_a_consistent_final_snapshot(private_client):
    client = private_client
    auth = owner(client)
    repository, owned, identity, _ = seed(client, auth)
    with repository._factory.begin() as session:
        analysis = session.get(Analysis, identity)
        analysis.status = "running"
    route = f"/api/v1/analyses/{identity}"
    for suffix in ("/results", "/graph", "/report?format=markdown"):
        response = client.get(route + suffix, headers=auth)
        assert response.status_code == 409, response.text


def test_tampered_evidence_fails_closed_without_exporting_source(private_client):
    client = private_client
    auth = owner(client)
    repository, owned, identity, finding_id = seed(client, auth)
    with repository._factory.begin() as session:
        session.execute(
            EvidenceRecord.__table__.update()
            .where(
                EvidenceRecord.analysis_id == identity,
                EvidenceRecord.source_type == "opinion_text",
            )
            .values(snapshot_text=SOURCE + " TAMPERED_PRIVATE_SENTINEL")
        )
    with pytest.raises(ValueError, match="snapshot"):
        saved_evidence(repository, owned, identity, finding_id)
    response = client.get(
        f"/api/v1/analyses/{identity}/findings/{finding_id}/evidence", headers=auth
    )
    assert response.status_code == 503
    assert "TAMPERED_PRIVATE_SENTINEL" not in response.text
