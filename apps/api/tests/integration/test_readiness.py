from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from filingguard.core.config import API_ROOT, Settings
from filingguard.db.session import create_db_engine
from filingguard.main import create_app


def test_liveness_does_not_claim_intake_readiness(client):
    assert client.get("/api/v1/health").status_code == 200
    response = client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.headers["cache-control"] == "no-store"


def test_readiness_requires_current_migrations_and_healthy_cleanup(tmp_path, monkeypatch):
    settings = Settings(
        intake_enabled=True,
        private_storage_directory=tmp_path / "private",
        source_verification_enabled=False,
        semantic_review_enabled=False,
    )
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    config = Config()
    config.set_main_option("script_location", str(API_ROOT / "migrations"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    monkeypatch.setattr("filingguard.main.Settings", lambda: settings)
    monkeypatch.setattr("filingguard.core.runtime.create_db_engine", lambda: engine)
    with TestClient(create_app()) as client:
        runtime = client.app.state.analysis_runtime
        runtime.get_lifecycle()
        runtime.sweep()
        response = client.get("/api/v1/ready")
        assert response.status_code == 200
        assert all(response.json()["checks"].values())
        with engine.begin() as connection:
            connection.execute(text("UPDATE alembic_version SET version_num='old_schema'"))
        assert client.get("/api/v1/ready").status_code == 503
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE alembic_version SET version_num='0004_citation_extraction'")
            )
        runtime.cleanup_failed = True
        assert not client.get("/api/v1/ready").json()["checks"]["cleanup"]
        runtime.cleanup_failed = False
        settings.cors_origins = ["*"]
        assert not client.get("/api/v1/ready").json()["checks"]["exact_origins"]
        settings.semantic_review_enabled = True
        settings.groq_api_key = None
        assert not client.get("/api/v1/ready").json()["checks"]["provider_configuration"]
        assert client.get("/api/v1/health").json() == {"status": "ok"}
