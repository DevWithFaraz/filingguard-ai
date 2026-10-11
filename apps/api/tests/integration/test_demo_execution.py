"""Real contained engines over curated cached opinions; no semantic fixture replay."""

import time

from test_orchestrator import owner
from test_orchestrator import private_client as private_client


def test_curated_demo_executes_sources_quotes_and_exports_without_model(private_client):
    client = private_client
    auth = owner(client)
    prepared = client.post(
        "/api/v1/analyses/demo",
        headers=auth,
        json={
            "fixture_id": "curated-v1",
            "mode": "demo",
            "ai_used": True,
            "court_profile_id": "synthetic-demo-v1",
        },
    )
    assert prepared.status_code == 201, prepared.text
    route = f"/api/v1/analyses/{prepared.json()['analysis_id']}"
    assert client.post(route + "/run", headers=auth).status_code == 202
    deadline = time.monotonic() + 95
    while time.monotonic() < deadline:
        status = client.get(route + "/status", headers=auth).json()
        if status["status"] in {"completed", "partial", "failed", "interrupted"}:
            break
        time.sleep(0.3)
    assert status["status"] == "partial", status
    response = client.get(route + "/results", headers=auth)
    assert response.status_code == 200, response.text
    result = response.json()
    stages = {s["name"]: s for s in result["stages"]}
    assert stages["citations"]["status"] == "partial"
    assert stages["quotes"]["status"] in {"completed", "partial"}
    assert stages["propositions"]["status"] == "unavailable"
    assert len({c["authority_id"] for c in result["citations"] if c["authority_id"]}) == 3
    assert sum(c["verification_status"] == "verified" for c in result["citations"]) >= 4
    assert any(c["verification_status"] != "verified" for c in result["citations"])
    assert {q["match_status"] for q in result["quotes"]} >= {"exact", "close"}, result["quotes"]
    assert {f["type"] for f in result["findings"]} >= {"quote", "court_rule", "privacy"}
    assert len(result["score"]["categories"]) == 5
    assert result["score"]["value"] is not None
    assert all(
        link["support_status"] == "not_run" for claim in result["claims"] for link in claim["links"]
    )
    graph = client.get(route + "/graph", headers=auth)
    assert graph.status_code == 200 and graph.json()["edges"]
    for finding in result["findings"][:2]:
        detail = client.get(route + f"/findings/{finding['id']}/evidence", headers=auth)
        assert detail.status_code == 200 and detail.json()["evidence"]
    for format in ("markdown", "html"):
        report = client.get(route + f"/report?format={format}", headers=auth)
        assert report.status_code == 200 and "not legal advice" in report.text.lower()
        assert "cached_public" in report.text
    other = owner(client)
    assert client.get(route + "/results", headers=other).status_code == 404
    assert client.delete(route, headers=auth).status_code == 200
    assert client.get(route + "/results", headers=auth).status_code == 404


def test_demo_court_and_ai_choices_are_saved_and_bounded(private_client):
    client = private_client
    auth = owner(client)
    for court in ("synthetic-demo-v1", "unverified"):
        response = client.post(
            "/api/v1/analyses/demo",
            headers=auth,
            json={
                "fixture_id": "curated-v1",
                "mode": "demo",
                "ai_used": False,
                "court_profile_id": court,
            },
        )
        assert response.status_code == 201
        assert response.json()["court_profile_id"] == court
        assert response.json()["ai_used"] is False
    response = client.post(
        "/api/v1/analyses/demo",
        headers=auth,
        json={
            "fixture_id": "curated-v1",
            "mode": "demo",
            "court_profile_id": "invented",
        },
    )
    assert response.status_code == 422
