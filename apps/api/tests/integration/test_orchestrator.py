"""Synthetic stage runners exercise the job boundary without legal verdicts."""

import json
import logging
import time

import pytest
from fastapi.testclient import TestClient
from review_workers import completed, fail, held

from filingguard.core.config import Settings
from filingguard.db.models import Base
from filingguard.db.session import create_db_engine
from filingguard.main import create_app
from filingguard.modules.analyses.orchestrator import REVIEW_STAGES, StageResult
from filingguard.modules.analyses.schemas import StageName, StageStatus

ORIGIN = "http://localhost:5173"


@pytest.fixture
def private_client(tmp_path, monkeypatch):
    settings = Settings(intake_enabled=True, private_storage_directory=tmp_path / "private")
    monkeypatch.setattr("filingguard.main.Settings", lambda: settings)
    engine = create_db_engine(f"sqlite+pysqlite:///{(tmp_path / 'review.db').as_posix()}")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("filingguard.core.runtime.create_db_engine", lambda: engine)
    with TestClient(create_app()) as client:
        yield client


def owner(client):
    response = client.post("/api/v1/sessions", headers={"Origin": ORIGIN})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['token']}", "Origin": ORIGIN}


def prepare(client, auth, *, text="Synthetic argument with no real legal assertions."):
    response = client.post(
        "/api/v1/analyses/text",
        headers=auth,
        json={
            "document_name": "Synthetic filing",
            "text": text,
            "court_profile_id": "unverified",
            "ai_used": False,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["analysis_id"]


def await_status(client, auth, identity, target):
    # The contained job permits 90 seconds including cold interpreter startup.
    deadline = time.monotonic() + 95
    while time.monotonic() < deadline:
        response = client.get(f"/api/v1/analyses/{identity}/status", headers=auth)
        assert response.status_code == 200, response.text
        if response.json()["status"] == target:
            return response.json()
        time.sleep(0.5)
    pytest.fail(f"Review did not reach {target}")


def await_file(path):
    for _ in range(600):
        if path.exists():
            return
        time.sleep(0.02)
    pytest.fail("Contained runner did not start")


def test_empty_stage_output_cannot_be_marked_complete():
    with pytest.raises(ValueError, match="eligible checks"):
        StageResult(status=StageStatus.COMPLETED).validate(StageName.CITATIONS)


def test_local_review_is_partial_and_owner_scoped(private_client):
    client = private_client
    first, second = owner(client), owner(client)
    identity = prepare(client, first)
    route = f"/api/v1/analyses/{identity}"
    assert client.post(route + "/run", headers=first).status_code == 202
    result = await_status(client, first, identity, "partial")
    stages = {stage["name"]: stage["status"] for stage in result["stages"]}
    assert stages["privacy"] == "completed"
    assert stages["court_rules"] == "unavailable"
    assert stages["citations"] == "skipped"
    assert client.get(route + "/status", headers=second).status_code == 404
    assert client.get(route + "/findings", headers=second).status_code == 404
    assert client.post(route + "/run", headers=second).status_code == 404


def test_review_persists_queue_and_holds_preparation_slot(private_client, tmp_path):
    client = private_client
    auth, other = owner(client), owner(client)
    entered, release = tmp_path / "entered", tmp_path / "release"
    identity = prepare(
        client, auth, text=json.dumps({"entered": str(entered), "release": str(release)})
    )

    client.app.state.review_runners = {
        stage: held
        if stage == StageName.PRIVACY
        else StageResult(
            status=StageStatus.SKIPPED, reason="Synthetic control-path input has no eligible checks"
        )
        for stage in REVIEW_STAGES
    }
    route = f"/api/v1/analyses/{identity}"
    try:
        response = client.post(route + "/run", headers=auth)
        assert response.status_code == 202, response.text
        assert response.json() == {"analysis_id": identity, "status": "queued", "mode": "live"}
        await_file(entered)
        assert client.get(route + "/status", headers=auth).json()["status"] == "running"
        assert client.post(route + "/run", headers=auth).status_code == 409
        assert client.post(route + "/run", headers=other).status_code == 404
        assert client.delete(route, headers=auth).status_code == 409
        assert client.post("/api/v1/analyses/text", headers=auth, json={}).status_code == 409
    finally:
        release.touch()
    result = await_status(client, auth, identity, "completed")
    assert len(result["stages"]) == 9
    assert result["coverage"] == {
        "eligible": 2,
        "evaluated": 2,
        "unavailable": 0,
        "pending": 0,
        "truncated": False,
        "limitation": None,
    }
    # Scheduling/admission checks do not invent evaluated legal verdicts.
    assert result["overall_score"] is None and result["score_is_provisional"] is True
    assert result["risk_level"] is None
    assert client.get(route, headers=auth).json()["execution_status"] == "completed"
    assert client.post(route + "/run", headers=auth).status_code == 409
    assert client.delete(route, headers=auth).status_code == 200


def test_review_failure_keeps_prior_stage_and_hides_exception(private_client, caplog):
    client = private_client
    auth = owner(client)
    identity = prepare(client, auth)

    client.app.state.review_runners = {
        StageName.PRIVACY: completed,
        StageName.COURT_RULES: StageResult(
            status=StageStatus.UNAVAILABLE, reason="Synthetic court profile is unavailable"
        ),
        StageName.CITATIONS: completed,
        StageName.STATUTES: StageResult(
            status=StageStatus.UNAVAILABLE, reason="No statute source in the synthetic control"
        ),
        StageName.TABLE_OF_AUTHORITIES: StageResult(
            status=StageStatus.SKIPPED, reason="No Table of Authorities in the synthetic control"
        ),
        StageName.CLAIMS: fail,
        StageName.PROPOSITIONS: StageResult(
            status=StageStatus.UNAVAILABLE, reason="Synthetic claim dependency unavailable"
        ),
        StageName.QUOTES: StageResult(
            status=StageStatus.SKIPPED, reason="No quotation in the synthetic control input"
        ),
    }
    with caplog.at_level(logging.ERROR):
        assert client.post(f"/api/v1/analyses/{identity}/run", headers=auth).status_code == 202
        result = await_status(client, auth, identity, "partial")
    stages = {state["name"]: state["status"] for state in result["stages"]}
    assert stages["document"] == "completed"
    assert stages["citations"] == "completed"
    assert stages["claims"] == "failed"
    assert stages["propositions"] == "unavailable"
    assert stages["privacy"] == "completed"
    assert stages["quotes"] == "skipped"
    assert "SYNTHETIC_PRIVATE_SENTINEL" not in caplog.text
    assert identity in caplog.text
    assert prepare(client, auth)


def test_privacy_findings_are_masked_and_independent_of_citations(private_client, caplog):
    client = private_client
    auth = owner(client)
    response = client.post(
        "/api/v1/analyses/text",
        headers=auth,
        json={
            "document_name": "Private sample",
            "court_profile_id": "unverified",
            "ai_used": False,
            "text": (
                "No citation. SSN 900-12-3456; account number 000123456789; "
                "date of birth 04/17/2000."
            ),
        },
    )
    assert response.status_code == 201, response.text
    identity = response.json()["analysis_id"]
    route = f"/api/v1/analyses/{identity}"
    with caplog.at_level(logging.INFO, logger="filingguard.modules.analyses.orchestrator"):
        assert client.post(route + "/run", headers=auth).status_code == 202
        result = await_status(client, auth, identity, "partial")
    assert f"review.job.start analysis_id={identity}" in caplog.text
    assert f"review.job.finish analysis_id={identity}" in caplog.text
    assert "duration_ms=" in caplog.text
    assert "900-12-3456" not in caplog.text
    assert "000123456789" not in caplog.text
    assert {s["name"]: s["status"] for s in result["stages"]}["privacy"] == "completed"
    findings = client.get(route + "/findings", headers=auth)
    assert findings.status_code == 200, findings.text
    body = findings.json()
    assert len(body["findings"]) == 3
    assert all(item["evidence_count"] == 1 for item in body["findings"])
    assert "900-12-3456" not in findings.text
    assert "000123456789" not in findings.text
    assert "04/17/2000" not in findings.text
    rerun = client.post(route + "/rerun", headers=auth)
    assert rerun.status_code == 201, rerun.text
    next_id = rerun.json()["analysis_id"]
    assert next_id != identity
    assert rerun.json()["execution_status"] == "not_run"
    assert client.get(route + "/findings", headers=auth).json()["findings"] == body["findings"]
    assert client.post(f"/api/v1/analyses/{next_id}/run", headers=auth).status_code == 202
    await_status(client, auth, next_id, "partial")


def test_curated_demo_runs_synthetic_rule_and_privacy_checks(private_client):
    client = private_client
    auth = owner(client)
    response = client.post(
        "/api/v1/analyses/demo",
        headers=auth,
        json={
            "fixture_id": "curated-v1",
            "mode": "demo",
        },
    )
    assert response.status_code == 201, response.text
    identity = response.json()["analysis_id"]
    route = f"/api/v1/analyses/{identity}"
    assert client.post(route + "/run", headers=auth).status_code == 202
    result = await_status(client, auth, identity, "partial")
    stages = {stage["name"]: stage["status"] for stage in result["stages"]}
    assert stages["privacy"] == "completed"
    assert stages["court_rules"] in {"completed", "partial"}
    court = next(stage for stage in result["stages"] if stage["name"] == "court_rules")
    assert "synthetic exercise" in court["reason"]
    assert "Heading presence only" not in court["reason"]
    findings = client.get(route + "/findings", headers=auth).json()["findings"]
    assert {item["type"] for item in findings} == {"privacy", "court_rule", "quote", "citation"}
    quote_results = client.get(route + "/results", headers=auth).json()["quotes"]
    assert {q["match_status"] for q in quote_results} == {"exact", "close"}
    assert any(item["title"] == "Synthetic AI-use disclosure missing" for item in findings)
    assert client.post(route + "/run", headers=auth).status_code == 409
