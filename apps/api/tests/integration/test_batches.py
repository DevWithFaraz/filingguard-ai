"""Integration tests for batch filing intake and processing."""

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


def test_create_list_and_get_batch(test_client):
    client, _ = test_client
    auth = headers(client)

    create_res = client.post(
        "/api/v1/batches",
        headers=auth,
        json={
            "name": "Pre-Trial Briefs Batch",
            "documents": [
                {
                    "document_name": "Brief Alpha.txt",
                    "text": "First brief paragraph one.\n\nFirst brief paragraph two.",
                    "court_profile_id": "unverified",
                    "ai_used": False,
                },
                {
                    "document_name": "Brief Beta.txt",
                    "text": "Second brief paragraph one.\n\nSecond brief paragraph two.",
                    "court_profile_id": "unverified",
                    "ai_used": True,
                },
            ],
        },
    )
    assert create_res.status_code == 201, create_res.text
    batch = create_res.json()
    assert batch["name"] == "Pre-Trial Briefs Batch"
    assert batch["total_count"] == 2
    assert batch["completed_count"] == 0
    assert batch["status"] == "queued"
    batch_id = batch["id"]

    # List batches
    list_res = client.get("/api/v1/batches", headers=auth)
    assert list_res.status_code == 200
    batches = list_res.json()
    assert len(batches) == 1
    assert batches[0]["id"] == batch_id

    # Get batch detail
    detail_res = client.get(f"/api/v1/batches/{batch_id}", headers=auth)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["name"] == "Pre-Trial Briefs Batch"
    assert len(detail["items"]) == 2
    doc_names = {item["document_name"] for item in detail["items"]}
    assert doc_names == {"Brief Alpha.txt", "Brief Beta.txt"}
    for item in detail["items"]:
        # Verify underlying analyses were created
        ana_res = client.get(f"/api/v1/analyses/{item['analysis_id']}", headers=auth)
        assert ana_res.status_code == 200


def test_cancel_batch(test_client):
    client, _ = test_client
    auth = headers(client)

    create_res = client.post(
        "/api/v1/batches",
        headers=auth,
        json={
            "name": "Batch to Cancel",
            "documents": [
                {
                    "document_name": "Doc 1.txt",
                    "text": "Text content one.\n\nText content two.",
                }
            ],
        },
    )
    batch_id = create_res.json()["id"]

    cancel_res = client.post(f"/api/v1/batches/{batch_id}/cancel", headers=auth)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    detail = client.get(f"/api/v1/batches/{batch_id}", headers=auth).json()
    assert detail["status"] == "cancelled"


def test_batch_owner_isolation(test_client):
    client, _ = test_client
    owner_a = headers(client)
    owner_b = headers(client)

    created = client.post(
        "/api/v1/batches",
        headers=owner_a,
        json={
            "name": "Confidential Batch A",
            "documents": [
                {"document_name": "Secret.txt", "text": "Secret content.\n\nSecret line."}
            ],
        },
    ).json()
    bid = created["id"]

    # Owner B cannot view or cancel
    assert client.get(f"/api/v1/batches/{bid}", headers=owner_b).status_code == 404
    assert client.post(f"/api/v1/batches/{bid}/cancel", headers=owner_b).status_code == 404
    assert client.get(f"/api/v1/batches/{uuid4()}", headers=owner_a).status_code == 404
