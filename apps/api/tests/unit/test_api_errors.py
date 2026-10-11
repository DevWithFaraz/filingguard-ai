import logging
from uuid import UUID

from fastapi import HTTPException
from fastapi.testclient import TestClient

from filingguard.api.contracts import TextSubmission
from filingguard.main import create_app


def test_unknown_resource_has_safe_error_envelope(client):
    response = client.get("/api/v1/unknown", headers={"X-Request-ID": "untrusted-input"})
    assert response.status_code == 404
    detail = response.json()["error"]
    assert detail["code"] == "not_found"
    assert str(UUID(detail["request_id"])) == response.headers["x-request-id"]
    assert response.headers["cache-control"] == "no-store"
    assert "untrusted-input" not in response.text


def test_method_not_allowed_retains_allowed_methods(client):
    response = client.post("/api/v1/health")
    assert response.status_code == 405
    assert "GET" in response.headers["allow"]
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_validation_never_echoes_document_or_sensitive_values():
    app = create_app()

    @app.post("/_contract_test")
    def submit(body: TextSubmission):
        return {"accepted": True}

    secret = "private-test-fragment"
    with TestClient(app) as client:
        response = client.post("/_contract_test", json={"text": secret, "ai_used": "no"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert secret not in response.text


def test_http_error_sanitizes_detail_but_preserves_bounded_retry_header():
    app = create_app()

    @app.get("/_contract_test")
    def busy():
        raise HTTPException(429, detail="private-test-fragment", headers={"Retry-After": "5"})

    with TestClient(app) as client:
        response = client.get("/_contract_test")
    assert response.status_code == 429
    assert response.headers["retry-after"] == "5"
    assert "private-test-fragment" not in response.text


def test_unexpected_error_is_sanitized_and_cors_survives(caplog):
    app = create_app()

    @app.get("/_contract_test")
    def fail():
        raise ValueError("private-test-fragment")

    with TestClient(app) as client, caplog.at_level(logging.ERROR):
        response = client.get("/_contract_test", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "private-test-fragment" not in response.text + caplog.text
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
