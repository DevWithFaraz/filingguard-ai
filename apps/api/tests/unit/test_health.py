from fastapi.testclient import TestClient

from filingguard.main import create_app


def test_liveness_works_without_provider_credentials(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("COURTLISTENER_API_TOKEN", raising=False)
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
