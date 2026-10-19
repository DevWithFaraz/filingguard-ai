"""Integration tests for saved legal matters."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from filingguard.core.config import Settings
from filingguard.db.models import Base
from filingguard.db.session import create_db_engine, create_session_factory
from filingguard.main import create_app

ORIGIN = "http://localhost:5173"


@pytest.fixture
def test_client(tmp_path, monkeypatch):
    settings = Settings(intake_enabled=True, private_storage_directory=tmp_path / "private")
    monkeypatch.setattr("filingguard.main.Settings", lambda: settings)
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("filingguard.core.runtime.create_db_engine", lambda: engine)
    with TestClient(create_app()) as client:
        yield client, create_session_factory(engine)


def headers(client):
    response = client.post("/api/v1/sessions", headers={"Origin": ORIGIN})
    assert response.status_code == 201, response.text
    return {"Authorization": "Bearer " + response.json()["token"], "Origin": ORIGIN}


def submit(client, auth, name="Brief in Support"):
    return client.post(
        "/api/v1/analyses/text",
        headers=auth,
        json={
            "document_name": name,
            "text": "First paragraph.\n\nSecond paragraph.",
            "court_profile_id": "unverified",
            "ai_used": True,
        },
    )


def test_create_and_list_matters(test_client):
    client, _ = test_client
    auth = headers(client)

    create_res = client.post(
        "/api/v1/matters",
        headers=auth,
        json={
            "name": "Acme v. Beta Corp",
            "case_number": "3:24-cv-01234",
            "client_id": "CLI-1001",
            "description": "Breach of contract defense.",
        },
    )
    assert create_res.status_code == 201, create_res.text
    matter_id = create_res.json()["id"]
    assert create_res.json()["name"] == "Acme v. Beta Corp"

    # Duplicate name should conflict
    dup = client.post(
        "/api/v1/matters",
        headers=auth,
        json={"name": "Acme v. Beta Corp"},
    )
    assert dup.status_code == 409

    list_res = client.get("/api/v1/matters", headers=auth)
    assert list_res.status_code == 200
    matters = list_res.json()
    assert len(matters) == 1
    assert matters[0]["id"] == matter_id


def test_assign_analysis_and_view_matter_detail(test_client):
    client, _ = test_client
    auth = headers(client)

    matter_res = client.post(
        "/api/v1/matters",
        headers=auth,
        json={"name": "Estate of Davis"},
    )
    matter_id = matter_res.json()["id"]

    created = submit(client, auth, "Motion for Summary Judgment")
    analysis_id = created.json()["analysis_id"]

    assign_res = client.post(
        f"/api/v1/matters/{matter_id}/analyses/{analysis_id}",
        headers=auth,
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["assigned"] is True

    detail_res = client.get(f"/api/v1/matters/{matter_id}", headers=auth)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["name"] == "Estate of Davis"
    assert len(detail["analyses"]) == 1
    assert detail["analyses"][0]["analysis_id"] == analysis_id
    assert detail["analyses"][0]["document_name"] == "Motion for Summary Judgment"


def test_unassign_and_delete_matter_preserves_analyses(test_client):
    client, _ = test_client
    auth = headers(client)

    matter = client.post("/api/v1/matters", headers=auth, json={"name": "Temporary Matter"}).json()
    mid = matter["id"]

    created = submit(client, auth, "Test Filing")
    aid = created.json()["analysis_id"]

    client.post(f"/api/v1/matters/{mid}/analyses/{aid}", headers=auth)

    del_res = client.delete(f"/api/v1/matters/{mid}", headers=auth)
    assert del_res.status_code == 200

    assert client.get(f"/api/v1/matters/{mid}", headers=auth).status_code == 404
    # Analysis is preserved
    assert client.get(f"/api/v1/analyses/{aid}", headers=auth).status_code == 200


def test_matter_owner_isolation(test_client):
    client, _ = test_client
    owner_a = headers(client)
    owner_b = headers(client)

    matter_a = client.post(
        "/api/v1/matters",
        headers=owner_a,
        json={"name": "Owner A Confidential Matter"},
    ).json()
    mid = matter_a["id"]

    assert client.get(f"/api/v1/matters/{mid}", headers=owner_b).status_code == 404
    assert client.delete(f"/api/v1/matters/{mid}", headers=owner_b).status_code == 404
    assert client.get(f"/api/v1/matters/{uuid4()}", headers=owner_a).status_code == 404
