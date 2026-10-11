"""Real contained workers, synthetic inputs and fake transports; no provider credits."""

import json
import time
from threading import Event
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from review_workers import completed as complete
from review_workers import spend_budget, stuck_descendant, stuck_provider

from filingguard.core.config import Settings
from filingguard.db.models import Analysis, Base
from filingguard.db.session import create_db_engine
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.main import create_app
from filingguard.modules.analyses.execution import (
    ReviewLimits,
    StageExecutionError,
    execute_stage,
    result_from_wire,
    result_to_wire,
)
from filingguard.modules.analyses.orchestrator import REVIEW_STAGES
from filingguard.modules.analyses.runners import local_runners, privacy_stage
from filingguard.modules.analyses.schemas import StageName

ORIGIN = "http://localhost:5173"


def make_analysis(text):
    return Analysis(
        id=uuid4(),
        document_name="Synthetic timeout sample",
        document_sha256="0" * 64,
        document_snapshot={"text": text},
        mode="live",
        court_profile_id="unverified",
        ai_used=False,
        status="running",
        stage_states={},
    )


def await_path(path):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.02)
    pytest.fail("Synthetic stuck worker did not start")


def terminal(client, auth, route, target="partial"):
    for _ in range(60):
        value = client.get(route + "/status", headers=auth)
        assert value.status_code == 200, value.text
        if value.json()["status"] == target:
            return value.json()
        time.sleep(0.5)
    pytest.fail("Review did not terminate")


@pytest.fixture
def private_app(tmp_path, monkeypatch):
    settings = Settings(
        intake_enabled=True,
        private_storage_directory=tmp_path / "private",
        analysis_timeout_seconds=30,
        review_stage_timeout_seconds=5,
    )
    monkeypatch.setattr("filingguard.main.Settings", lambda: settings)
    engine = create_db_engine(f"sqlite+pysqlite:///{(tmp_path / 'review.db').as_posix()}")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("filingguard.core.runtime.create_db_engine", lambda: engine)
    return create_app()


def prepare(client, text):
    session = client.post("/api/v1/sessions", headers={"Origin": ORIGIN})
    assert session.status_code == 201
    auth = {"Origin": ORIGIN, "Authorization": f"Bearer {session.json()['token']}"}
    value = client.post(
        "/api/v1/analyses/text",
        headers=auth,
        json={
            "document_name": "Synthetic sample",
            "text": text,
            "court_profile_id": "unverified",
            "ai_used": False,
        },
    )
    assert value.status_code == 201, value.text
    return auth, f"/api/v1/analyses/{value.json()['analysis_id']}"


def test_hard_stage_timeout_preserves_checks_and_api_liveness(private_app, tmp_path):
    marker = tmp_path / "stuck"
    private_app.state.review_runners = {**local_runners(), StageName.CITATIONS: stuck_provider}
    with TestClient(private_app) as client:
        auth, route = prepare(
            client,
            json.dumps(
                {
                    "marker": str(marker),
                    "argument": "Synthetic SSN 900-12-3456.",
                }
            ),
        )
        assert client.post(route + "/run", headers=auth).status_code == 202
        await_path(marker)
        started = time.monotonic()
        assert client.get("/api/v1/health").status_code == 200
        assert client.get(route + "/status", headers=auth).json()["status"] == "running"
        assert time.monotonic() - started < 2
        result = terminal(client, auth, route)
        states = {stage["name"]: stage for stage in result["stages"]}
        assert states["privacy"]["status"] == "completed"
        assert states["court_rules"]["status"] == "unavailable"
        assert states["citations"]["status"] == "unavailable"
        assert "deadline" in states["citations"]["reason"]
        assert all(stage["status"] not in {"queued", "running"} for stage in result["stages"])
        assert result["overall_score"] is None
        findings = client.get(route + "/findings", headers=auth)
        saved = findings.json()["findings"]
        assert len([row for row in saved if row["type"] == "privacy"]) == 1
        # Local quote extraction now inspects the quoted JSON keys/values in this
        # synthetic worker envelope. Missing citation output cannot verify them.
        assert all(
            row["type"] == "privacy" or (row["type"] == "quote" and row["authority_id"] is None)
            for row in saved
        )
        assert "900-12-3456" not in findings.text
        assert client.post(route + "/rerun", headers=auth).status_code == 201


def test_overall_cutoff_marks_unstarted_stages_without_running_them(private_app, tmp_path):
    marker = tmp_path / "overall"
    private_app.state.settings.analysis_timeout_seconds = 9
    private_app.state.settings.review_stage_timeout_seconds = 30
    private_app.state.review_runners = {
        **local_runners(),
        StageName.CITATIONS: stuck_provider,
        StageName.CLAIMS: spend_budget,
    }
    with TestClient(private_app) as client:
        auth, route = prepare(client, str(marker))
        started = time.monotonic()
        assert client.post(route + "/run", headers=auth).status_code == 202
        result = terminal(client, auth, route)
        assert time.monotonic() - started < 12
        states = {stage["name"]: stage for stage in result["stages"]}
        assert states["privacy"]["status"] == "completed"
        assert states["claims"]["status"] == "unavailable"
        assert "deadline" in states["claims"]["reason"]
        assert all(stage["status"] not in {"queued", "running"} for stage in result["stages"])


def test_request_attempts_are_shared_across_stage_processes(private_app):
    private_app.state.settings.max_provider_attempts = 2
    private_app.state.review_runners = {stage: spend_budget for stage in REVIEW_STAGES}
    with TestClient(private_app) as client:
        auth, route = prepare(client, "Synthetic budget test")
        assert client.post(route + "/run", headers=auth).status_code == 202
        states = {stage["name"]: stage for stage in terminal(client, auth, route)["stages"]}
        assert states["privacy"]["status"] == "completed"
        assert all(states[stage.value]["status"] == "unavailable" for stage in REVIEW_STAGES[1:])


def test_shutdown_kills_stuck_work_and_persists_interruption(private_app, tmp_path):
    marker = tmp_path / "shutdown"
    private_app.state.review_runners = {**local_runners(), StageName.CITATIONS: stuck_provider}
    with TestClient(private_app) as client:
        auth, route = prepare(client, str(marker))
        assert client.post(route + "/run", headers=auth).status_code == 202
        await_path(marker)
        started = time.monotonic()
        client.app.state.analysis_runtime.review.close()
        assert time.monotonic() - started < 2
        result = terminal(client, auth, route, "interrupted")
        assert all(stage["status"] not in {"queued", "running"} for stage in result["stages"])
        next_id = client.post(route + "/rerun", headers=auth).json()["analysis_id"]
        next_route = f"/api/v1/analyses/{next_id}"
        assert client.post(next_route + "/run", headers=auth).status_code == 503
        assert client.get(next_route + "/status", headers=auth).json()["status"] == "not_run"


def test_containment_stops_descendant_side_effects(tmp_path):
    path = tmp_path / "descendant"
    budget = ProviderBudget(deadline=time.monotonic() + 10)
    with pytest.raises(StageExecutionError, match="deadline"):
        execute_stage(
            stuck_descendant,
            make_analysis(str(path)),
            StageName.CITATIONS,
            budget,
            stage_seconds=5,
            stop=Event(),
        )
    assert path.exists(), "Test must start the descendant, not only kill interpreter startup"
    previous = path.read_text()
    time.sleep(0.15)
    assert path.read_text() == previous
    assert budget.attempts_used == budget.max_attempts


def test_worker_output_roundtrips_typed_ids_times_and_raw_private_evidence():
    analysis = make_analysis("Synthetic SSN 900-12-3456.")
    result = privacy_stage(analysis, ProviderBudget(deadline=time.monotonic() + 10))
    decoded = result_from_wire(json.loads(json.dumps(result_to_wire(result))), analysis.id)
    decoded.validate(StageName.PRIVACY)
    assert decoded.records[0].analysis_id == analysis.id
    assert decoded.records[1].retrieved_at.utcoffset() is not None
    assert decoded.records[1].excerpt == "900-12-3456"
    with pytest.raises(ValueError, match="ownership"):
        result_from_wire(result_to_wire(result), uuid4())


def test_large_input_pipe_cannot_postpone_the_hard_cutoff():
    started = time.monotonic()
    with pytest.raises(StageExecutionError, match="deadline"):
        execute_stage(
            complete,
            make_analysis("x" * 100000),
            StageName.CITATIONS,
            ProviderBudget(deadline=started + 10),
            stage_seconds=0.1,
            stop=Event(),
        )
    assert time.monotonic() - started < 2


def test_large_input_reaches_a_slow_starting_worker(monkeypatch):
    # Force startup beyond the former 100 ms pipe poll, with more input than
    # a Linux pipe holds. Delivery must finish without relaxing the deadline.
    import subprocess

    spawn = subprocess.Popen

    def slow_start(args, **kwargs):
        assert args[1:] == ["-m", "filingguard.modules.analyses.worker"]
        return spawn(
            [args[0], "-c", "import time,runpy;time.sleep(.3);"
             "runpy.run_module('filingguard.modules.analyses.worker',run_name='__main__')"],
            **kwargs,
        )

    monkeypatch.setattr("filingguard.modules.analyses.execution.subprocess.Popen", slow_start)
    result = execute_stage(
        complete,
        make_analysis("x" * 100000),
        StageName.CITATIONS,
        ProviderBudget(deadline=time.monotonic() + 10),
        stage_seconds=5,
        stop=Event(),
    )
    assert result.status.value == "completed"
    assert result.coverage.evaluated == 1


@pytest.mark.parametrize(
    "values",
    [
        {"overall_seconds": 0},
        {"stage_seconds": float("nan")},
        {"max_provider_attempts": 100},
        {"stage_seconds": True},
    ],
)
def test_limits_reject_unbounded_or_nonfinite_values(values):
    with pytest.raises(ValueError):
        ReviewLimits(**values)


def test_stage_input_and_spawn_errors_do_not_leak_secrets(monkeypatch):
    budget = ProviderBudget(deadline=time.monotonic() + 10)
    with pytest.raises(StageExecutionError, match="limits"):
        execute_stage(
            complete,
            make_analysis("x" * 100001),
            StageName.CITATIONS,
            budget,
            stage_seconds=5,
            stop=Event(),
        )
    monkeypatch.setenv("DATABASE_URL", "SYNTHETIC_DATABASE_SECRET")
    monkeypatch.setenv("GROQ_API_KEY", "SYNTHETIC_PROVIDER_SECRET")
    captured = []

    def unavailable(*_args, **kwargs):
        captured.append(kwargs["env"])
        raise OSError("SYNTHETIC_DATABASE_SECRET")

    monkeypatch.setattr("filingguard.modules.analyses.execution.subprocess.Popen", unavailable)
    with pytest.raises(StageExecutionError) as error:
        execute_stage(
            complete,
            make_analysis("Synthetic sample"),
            StageName.CITATIONS,
            budget,
            stage_seconds=5,
            stop=Event(),
        )
    assert "SECRET" not in str(error.value)
    assert "DATABASE_URL" not in captured[0] and "GROQ_API_KEY" not in captured[0]
