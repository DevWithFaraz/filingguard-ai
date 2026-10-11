"""Real contained citation/claims workers preserve scoped traceable parent output."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from analysis_workers import verified_synthetic_citations
from sqlalchemy import func, select
from test_orchestrator import await_status, owner, prepare
from test_orchestrator import private_client as private_client

from filingguard.db.models import (
    Analysis,
    Authority,
    Citation,
    Claim,
    ClaimAuthorityLink,
    EvidenceRecord,
)
from filingguard.modules.analyses.execution import StageResult
from filingguard.modules.analyses.orchestrator import REVIEW_STAGES
from filingguard.modules.analyses.schemas import StageName, StageStatus
from filingguard.modules.claims.runner import claims_stage


def configure(client):
    client.app.state.review_runners = {
        stage: verified_synthetic_citations if stage == StageName.CITATIONS
        else claims_stage if stage == StageName.CLAIMS
        else StageResult(status=StageStatus.UNAVAILABLE, reason="Synthetic test stage unconfigured")
        for stage in REVIEW_STAGES
    }


def test_verified_and_unavailable_citations_feed_claims_in_actual_workers(private_client, caplog):
    client = private_client
    configure(client)
    auth, other = owner(client), owner(client)
    text = "😀 The equal treatment rule follows 347 U.S. 483 and 576 U.S. 644."
    identity = prepare(client, auth, text=text)
    route = f"/api/v1/analyses/{identity}"
    assert client.post(route + "/run", headers=auth).status_code == 202
    summary = await_status(client, auth, identity, "partial")
    stages = {item["name"]: item for item in summary["stages"]}
    assert stages["citations"]["status"] == "partial"
    assert stages["citations"]["coverage"]["evaluated"] == 1
    assert stages["citations"]["coverage"]["unavailable"] == 1
    assert stages["claims"]["status"] == "completed"
    assert stages["claims"]["coverage"]["evaluated"] == 2
    citation_response = client.get(route + "/citations", headers=auth)
    assert citation_response.status_code == 200
    assert "unavailable" in citation_response.text and "verified" in citation_response.text
    assert client.get(route + "/citations", headers=other).status_code == 404
    results = client.get(route + "/results", headers=auth)
    assert results.status_code == 200, results.text
    assert results.headers["cache-control"] == "no-store"
    assert len(results.json()["claims"]) == 1
    returned_claim = results.json()["claims"][0]
    assert returned_claim["text"] == text
    assert len(returned_claim["links"]) == 2
    assert all(link["support_status"] == "not_run" for link in returned_claim["links"])
    assert client.get(route + "/results", headers=other).status_code == 404
    assert client.get(route + "/results").status_code == 401
    assert "SYNTHETIC_COURTLISTENER_TOKEN" not in results.text + caplog.text
    assert "Synthetic public opinion passage" not in caplog.text

    factory = client.app.state.analysis_runtime.get_lifecycle().repository._factory
    with factory() as session:
        claims = list(session.scalars(select(Claim).where(Claim.analysis_id == UUID(identity))))
        links = list(session.scalars(select(ClaimAuthorityLink).where(
            ClaimAuthorityLink.analysis_id == UUID(identity))))
        evidence = list(session.scalars(select(EvidenceRecord).where(
            EvidenceRecord.analysis_id == UUID(identity), EvidenceRecord.claim_id.is_not(None))))
        assert len(claims) == len(evidence) == 1 and len(links) == 2
        claim = claims[0]
        assert claim.text == text and claim.start_offset == 0 and claim.end_offset == len(text)
        assert evidence[0].excerpt == claim.text and evidence[0].claim_id == claim.id
        assert evidence[0].method_version == "claims-context-v1"
        assert {link.claim_id for link in links} == {claim.id}
        assert all(link.support_status == "not_run" for link in links)
        assert sum(link.authority_id is not None for link in links) == 1
        citation_ids = {link.citation_id for link in links}
        assert citation_ids == set(session.scalars(select(Citation.id).where(
            Citation.analysis_id == UUID(identity))))

    assert client.delete(route, headers=auth).status_code == 200
    with factory() as session:
        for model in (Claim, ClaimAuthorityLink, EvidenceRecord, Citation, Authority):
            assert session.scalar(select(func.count()).select_from(model).where(
                model.analysis_id == UUID(identity))) == 0


def test_claim_worker_retains_unresolved_reference_without_authority_guess(private_client):
    client = private_client
    configure(client)
    auth = owner(client)
    text = "The rule follows 347 U.S. 483. Id. at 484."
    identity = prepare(client, auth, text=text)
    route = f"/api/v1/analyses/{identity}"
    assert client.post(route + "/run", headers=auth).status_code == 202
    summary = await_status(client, auth, identity, "partial")
    assert {s["name"]: s["status"] for s in summary["stages"]}["claims"] == "completed"
    factory = client.app.state.analysis_runtime.get_lifecycle().repository._factory
    with factory() as session:
        citations = list(session.scalars(select(Citation).where(
            Citation.analysis_id == UUID(identity)).order_by(Citation.start_offset)))
        links = list(session.scalars(select(ClaimAuthorityLink).where(
            ClaimAuthorityLink.analysis_id == UUID(identity))))
        reference = citations[1]
        assert reference.extraction_metadata["kind"] == "id"
        assert reference.verification_status == "not_run" and reference.authority_id is None
        reference_link = next(link for link in links if link.citation_id == reference.id)
        assert reference_link.authority_id is None and reference_link.support_status == "not_run"


def test_results_mask_claim_text_without_changing_offsets_and_enforce_expiry(private_client):
    client = private_client
    configure(client)
    auth = owner(client)
    text = "SSN 900-12-3456; the rule follows 347 U.S. 483."
    identity = prepare(client, auth, text=text)
    route = f"/api/v1/analyses/{identity}"
    assert client.post(route + "/run", headers=auth).status_code == 202
    await_status(client, auth, identity, "partial")
    response = client.get(route + "/results", headers=auth)
    assert response.status_code == 200, response.text
    assert "900-12-3456" not in response.text
    claim = response.json()["claims"][0]
    assert len(claim["text"]) == len(text)
    assert claim["location"]["start"] == 0 and claim["location"]["end"] == len(text)
    clone = client.post(route + "/rerun", headers=auth)
    assert clone.status_code == 201, clone.text
    assert clone.json()["analysis_id"] != identity
    clone_route = f"/api/v1/analyses/{clone.json()['analysis_id']}"
    clone_results = client.get(clone_route + "/results", headers=auth)
    assert clone_results.status_code == 200 and clone_results.json()["claims"] == []
    factory = client.app.state.analysis_runtime.get_lifecycle().repository._factory
    with factory.begin() as session:
        session.get(Analysis, UUID(identity)).expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert client.get(route + "/results", headers=auth).status_code == 404
