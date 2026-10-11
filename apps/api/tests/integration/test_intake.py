from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from filingguard.core.config import Settings
from filingguard.db.models import Analysis, AnonymousSession, Base
from filingguard.db.session import create_db_engine, create_session_factory
from filingguard.main import create_app

PDF = Path(__file__).resolve().parents[4] / "data/demo/curated-v1/filing.pdf"
ORIGIN = "http://localhost:5173"


@pytest.fixture
def private_client(tmp_path, monkeypatch):
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
    assert response.headers["cache-control"] == "no-store"
    return {"Authorization": "Bearer " + response.json()["token"], "Origin": ORIGIN}


def submit(client, auth, text="Synthetic claim.\n\nSecond claim."):
    return client.post(
        "/api/v1/analyses/text",
        headers=auth,
        json={
            "document_name": "Synthetic filing",
            "text": text,
            "court_profile_id": "unverified",
            "ai_used": True,
        },
    )


def test_public_default_keeps_intake_disabled(client):
    assert not client.get("/api/v1/capabilities").json()["intake_enabled"]
    assert client.post("/api/v1/sessions", headers={"Origin": ORIGIN}).status_code == 503
    assert client.post("/api/v1/analyses/text", json={}).status_code == 503


def test_text_prepare_owner_isolation_and_delete(private_client):
    client, factory = private_client
    first, second = headers(client), headers(client)
    response = submit(client, first)
    assert response.status_code == 201, response.text
    result = response.json()
    identity = result["analysis_id"]
    assert result["execution_status"] == "not_run"
    assert len(result["document"]["paragraphs"]) == 2
    assert "owner_hash" not in response.text and "stored_file_id" not in response.text
    assert client.get(f"/api/v1/analyses/{identity}", headers=second).status_code == 404
    assert client.delete(f"/api/v1/analyses/{identity}", headers=second).status_code == 404
    assert client.get("/api/v1/analyses", headers=second).json() == []
    assert client.get(f"/api/v1/analyses/{identity}", headers=first).status_code == 200
    activity = client.get("/api/v1/analyses", headers=first).json()
    assert activity[0]["paragraph_count"] == 2
    assert "document" not in activity[0]
    assert client.delete(f"/api/v1/analyses/{identity}", headers=first).status_code == 200
    with factory() as session:
        assert not list(session.scalars(select(Analysis)))
        assert all(len(row.owner_hash) == 64 for row in session.scalars(select(AnonymousSession)))


def test_pdf_preparation_stores_private_bytes_then_deletes_them(private_client, monkeypatch):
    client, _ = private_client
    auth = headers(client)
    # The parent cannot parse a PDF again after isolated worker validation.
    monkeypatch.setattr(
        "filingguard.integrations.storage.service._validate_pdf",
        lambda _: pytest.fail("PDF parsed in parent"),
    )
    response = client.post(
        "/api/v1/analyses/file?court_profile_id=unverified&ai_used=true",
        headers={**auth, "Content-Type": "application/pdf", "X-Document-Name": "demo.pdf"},
        content=PDF.read_bytes(),
    )
    assert response.status_code == 201, response.text
    root = client.app.state.analysis_runtime.storage._root
    assert response.json()["ai_used"] is True
    assert len(list(root.glob("*.pdf"))) == 1
    identity = response.json()["analysis_id"]
    assert client.get("/private/demo.pdf").status_code == 404
    assert client.delete(f"/api/v1/analyses/{identity}", headers=auth).status_code == 200
    assert not list(root.glob("*.pdf"))


def test_session_expiry_and_bad_origins_fail_closed(private_client):
    client, factory = private_client
    assert client.post("/api/v1/sessions").status_code == 403
    assert (
        client.post("/api/v1/sessions", headers={"Origin": "https://evil.test"}).status_code == 403
    )
    auth = headers(client)
    assert client.get("/api/v1/analyses").status_code == 401
    assert client.get("/api/v1/analyses", headers={**auth, "Origin": "null"}).status_code == 403
    with factory.begin() as session:
        session.execute(
            AnonymousSession.__table__.update().values(
                expires_at=datetime.now(UTC) - timedelta(seconds=1)
            )
        )
    assert client.get("/api/v1/analyses", headers=auth).status_code == 401


def test_limits_busy_body_and_safe_validation_errors(private_client):
    client, _ = private_client
    auth = headers(client)
    assert submit(client, auth, "").status_code == 422
    assert submit(client, auth, "x" * 100001).status_code == 422
    response = client.post(
        "/api/v1/analyses/text",
        headers={**auth, "Content-Length": "999999999"},
        content=b"SYNTHETIC_PRIVATE_SENTINEL",
    )
    assert response.status_code == 413
    assert "SYNTHETIC_PRIVATE_SENTINEL" not in response.text
    client.app.state.admission.slot.acquire()
    try:
        assert submit(client, auth).status_code == 409
    finally:
        client.app.state.admission.slot.release()
    for _ in range(5):
        assert submit(client, auth).status_code == 201
    assert submit(client, auth).status_code == 429


def test_demo_is_server_owned_and_never_becomes_engine_results(private_client):
    client, _ = private_client
    auth = headers(client)
    response = client.post(
        "/api/v1/analyses/demo", headers=auth, json={"fixture_id": "curated-v1", "mode": "demo"}
    )
    assert response.status_code == 201, response.text
    assert response.json()["mode"] == "demo"
    assert response.json()["execution_status"] == "not_run"
    assert "examples" not in response.json()
    assert (
        client.post(
            "/api/v1/analyses/demo", headers=auth, json={"fixture_id": "unknown", "mode": "demo"}
        ).status_code
        == 503
    )
    assert (
        client.post(
            "/api/v1/analyses/demo", headers=auth, json={"fixture_id": "curated-v1", "mode": "live"}
        ).status_code
        == 422
    )


def test_pdf_preflight_allows_filename_header_but_not_foreign_origin(private_client):
    client, _ = private_client
    request_headers = {
        "Origin": ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type,x-document-name",
    }
    response = client.options("/api/v1/analyses/file", headers=request_headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN
    response = client.options(
        "/api/v1/analyses/file", headers={**request_headers, "Origin": "https://evil.test"}
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_pdf_metadata_booleans_are_strict_and_names_are_display_only(private_client):
    client, _ = private_client
    auth = {
        **headers(client),
        "Content-Type": "application/pdf",
        "X-Document-Name": "..%2Fsynthetic.pdf",
    }
    response = client.post(
        "/api/v1/analyses/file?court_profile_id=unverified&ai_used=false",
        headers=auth,
        content=PDF.read_bytes(),
    )
    assert response.status_code == 201
    assert response.json()["ai_used"] is False
    root = client.app.state.analysis_runtime.storage._root
    assert all(path.stem != "synthetic" for path in root.glob("*.pdf"))
    assert (
        client.post(
            "/api/v1/analyses/file?court_profile_id=unverified&ai_used=yes",
            headers=auth,
            content=b"%PDF-invalid",
        ).status_code
        == 422
    )
