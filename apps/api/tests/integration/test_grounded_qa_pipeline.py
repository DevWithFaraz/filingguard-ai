"""Integration tests for Grounded Q&A endpoints (FR-260 through FR-264)."""

from test_orchestrator import owner
from test_orchestrator import private_client as private_client
from test_review_results import seed

from filingguard.db.models import Analysis
from filingguard.modules.grounded_qa.service import clear_qa_store


def test_grounded_qa_endpoint_answers_with_persisted_evidence(private_client):
    clear_qa_store()
    client = private_client
    auth, other = owner(client), owner(client)
    _, _, identity, finding_id = seed(client, auth)

    route = f"/api/v1/analyses/{identity}/findings/{finding_id}/questions"

    # Ask grounded question
    res = client.post(
        route,
        json={"question": "What evidence was used for this finding?"},
        headers=auth,
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["analysis_id"] == str(identity)
    assert data["finding_id"] == str(finding_id)
    assert data["status"] == "answered"
    assert data["refusal_reason"] == "none"
    assert len(data["evidence_record_ids"]) >= 1
    assert "Evidence Record" in data["answer"]

    # History retrieval
    hist_res = client.get(route, headers=auth)
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert hist["count"] == 1
    assert hist["questions"][0]["question"] == "What evidence was used for this finding?"

    # Isolation: foreign owner receives 404
    q_payload = {"question": "What evidence was used?"}
    assert client.post(route, json=q_payload, headers=other).status_code == 404
    assert client.get(route, headers=other).status_code == 404


def test_grounded_qa_endpoint_refuses_legal_advice(private_client):
    clear_qa_store()
    client = private_client
    auth = owner(client)
    _, _, identity, finding_id = seed(client, auth)

    route = f"/api/v1/analyses/{identity}/findings/{finding_id}/questions"

    # Disallowed broad legal advice question
    res = client.post(route, json={"question": "What should I argue in court?"}, headers=auth)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "refused"
    assert data["refusal_reason"] == "broad_legal_advice"
    assert "cannot provide legal advice" in data["answer"]
    assert "licensed legal counsel" in data["answer"]
    assert data["evidence_record_ids"] == []


def test_grounded_qa_requires_terminal_status_and_validates_input(private_client):
    clear_qa_store()
    client = private_client
    auth = owner(client)
    repository, _, identity, finding_id = seed(client, auth)

    route = f"/api/v1/analyses/{identity}/findings/{finding_id}/questions"

    # Input validation: empty question
    bad_res = client.post(route, json={"question": ""}, headers=auth)
    assert bad_res.status_code == 422

    # Input validation: whitespace-only
    bad_res2 = client.post(route, json={"question": "   "}, headers=auth)
    assert bad_res2.status_code == 422

    # Terminal state check: 409 when running
    with repository._factory.begin() as session:
        analysis = session.get(Analysis, identity)
        analysis.status = "running"

    assert client.post(route, json={"question": "Why flagged?"}, headers=auth).status_code == 409
    assert client.get(route, headers=auth).status_code == 409
