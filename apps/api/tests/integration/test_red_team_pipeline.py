"""Integration tests for Legal Red-Team API endpoints (FR-240 through FR-245)."""


from test_orchestrator import owner
from test_orchestrator import private_client as private_client
from test_review_results import seed

from filingguard.db.models import Analysis


def test_red_team_endpoints_return_grounded_weaknesses_and_isolation(private_client):
    client = private_client
    auth, other = owner(client), owner(client)
    _, _, identity, finding_id = seed(client, auth)

    route = f"/api/v1/analyses/{identity}/red-team"

    # Both POST and GET are supported and return HTTP 200
    post_res = client.post(route, headers=auth)
    assert post_res.status_code == 200, post_res.text
    data = post_res.json()

    assert data["analysis_id"] == str(identity)
    assert data["total_weaknesses"] >= 1
    assert "not legal strategy or legal advice" in data["limitation"]
    assert any(str(finding_id) in w["linked_finding_ids"] for w in data["weaknesses"])

    # Weaknesses are sorted by severity (critical, high, medium, low)
    severities = [w["severity"] for w in data["weaknesses"]]
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    assert severities == sorted(severities, key=lambda s: order.get(s, 99))

    get_res = client.get(route, headers=auth)
    assert get_res.status_code == 200
    assert get_res.json()["total_weaknesses"] == data["total_weaknesses"]

    # Foreign session is denied (404)
    assert client.get(route, headers=other).status_code == 404
    assert client.post(route, headers=other).status_code == 404


def test_red_team_requires_terminal_analysis_status(private_client):
    client = private_client
    auth = owner(client)
    repository, _, identity, _ = seed(client, auth)

    with repository._factory.begin() as session:
        analysis = session.get(Analysis, identity)
        analysis.status = "running"

    route = f"/api/v1/analyses/{identity}/red-team"
    assert client.post(route, headers=auth).status_code == 409
    assert client.get(route, headers=auth).status_code == 409
