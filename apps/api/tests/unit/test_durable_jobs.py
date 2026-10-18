import time
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from threading import BoundedSemaphore

import pytest
from sqlalchemy.orm.attributes import flag_modified

from filingguard.db.models import Analysis, Base, DocumentSegment, Finding
from filingguard.db.repository import AnalysisRepository
from filingguard.db.session import create_db_engine, create_session_factory
from filingguard.integrations.storage.managed import RecoverableTemporaryStorage
from filingguard.modules.analyses.execution import ReviewLimits, StageResult
from filingguard.modules.analyses.lifecycle import AnalysisLifecycle
from filingguard.modules.analyses.orchestrator import REVIEW_STAGES, ReviewOrchestrator
from filingguard.modules.analyses.schemas import (
    Coverage,
    FindingType,
    Severity,
    StageStatus,
)
from filingguard.modules.documents.extraction import extract_text

OWNER = sha256(b"durable-jobs-test-owner").hexdigest()


@pytest.fixture
def repo_system(tmp_path: Path):
    db_file = tmp_path / "durable_test.db"
    engine = create_db_engine(f"sqlite+pysqlite:///{db_file.as_posix()}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    repo = AnalysisRepository(factory)
    with RecoverableTemporaryStorage(tmp_path / "private") as storage:
        lifecycle = AnalysisLifecycle(repo, storage)
        yield factory, repo, storage, lifecycle
    engine.dispose()


def test_atomic_lease_acquisition_and_mutual_exclusion(repo_system):
    _, repo, _, _ = repo_system
    now = datetime.now(UTC)
    analysis = repo.create_analysis(
        OWNER,
        document_name="Test Doc",
        document_sha256="a" * 64,
        expires_at=now + timedelta(hours=1),
        status="queued",
    )

    # Worker 1 acquires lease
    assert repo.acquire_lease(OWNER, analysis.id, "worker-1", lease_seconds=60) is True

    # Analysis is now running with worker-1 lease
    stored = repo.get_analysis(OWNER, analysis.id)
    assert stored.status == "running"
    meta = stored.stage_states.get("lease_metadata", {})
    assert meta.get("worker_id") == "worker-1"
    assert meta.get("retry_count") == 0
    assert meta.get("lease_expires_at") is not None

    # Worker 2 attempts to acquire lease on the active job -> rejected
    assert repo.acquire_lease(OWNER, analysis.id, "worker-2", lease_seconds=60) is False

    # Worker 1 can re-acquire its own lease
    assert repo.acquire_lease(OWNER, analysis.id, "worker-1", lease_seconds=90) is True


def test_lease_renewal_during_active_execution(repo_system):
    _, repo, _, _ = repo_system
    now = datetime.now(UTC)
    analysis = repo.create_analysis(
        OWNER,
        document_name="Test Doc",
        document_sha256="a" * 64,
        expires_at=now + timedelta(hours=1),
        status="queued",
    )

    assert repo.acquire_lease(OWNER, analysis.id, "worker-1", lease_seconds=60) is True
    initial_exp = repo.get_analysis(OWNER, analysis.id).stage_states["lease_metadata"][
        "lease_expires_at"
    ]

    # Non-owning worker cannot renew
    assert repo.renew_lease(OWNER, analysis.id, "worker-2", lease_seconds=120) is False

    # Owning worker renews successfully
    assert repo.renew_lease(OWNER, analysis.id, "worker-1", lease_seconds=300) is True
    renewed_exp = repo.get_analysis(OWNER, analysis.id).stage_states["lease_metadata"][
        "lease_expires_at"
    ]
    assert renewed_exp >= initial_exp

    # Owning worker releases lease
    repo.release_lease(OWNER, analysis.id, "worker-1")
    stored = repo.get_analysis(OWNER, analysis.id)
    meta = stored.stage_states["lease_metadata"]
    assert meta.get("worker_id") is None
    assert meta.get("lease_expires_at") is None


def test_expired_lease_allows_reacquisition(repo_system):
    factory, repo, _, _ = repo_system
    now = datetime.now(UTC)
    analysis = repo.create_analysis(
        OWNER,
        document_name="Test Doc",
        document_sha256="a" * 64,
        expires_at=now + timedelta(hours=1),
        status="queued",
    )

    assert repo.acquire_lease(OWNER, analysis.id, "worker-1", lease_seconds=60) is True

    # Manually expire the lease timestamp in the past
    with factory.begin() as session:
        stored = session.get(Analysis, analysis.id)
        meta = dict(stored.stage_states["lease_metadata"])
        meta["lease_expires_at"] = (now - timedelta(seconds=10)).isoformat()
        stored.stage_states = {**stored.stage_states, "lease_metadata": meta}
        flag_modified(stored, "stage_states")

    # Worker 2 can now acquire the expired lease
    assert repo.acquire_lease(OWNER, analysis.id, "worker-2", lease_seconds=120) is True
    stored = repo.get_analysis(OWNER, analysis.id)
    assert stored.stage_states["lease_metadata"]["worker_id"] == "worker-2"


def test_crash_recovery_bounded_reschedule_and_interruption(repo_system):
    factory, repo, _, lifecycle = repo_system
    now = datetime.now(UTC)
    analysis = repo.create_analysis(
        OWNER,
        document_name="Test Doc",
        document_sha256="a" * 64,
        expires_at=now + timedelta(hours=1),
        status="not_run",
    )

    # Simulate completed document stage and running citations stage
    with repo.stage_update(OWNER, analysis.id, "document", "completed") as writer:
        writer.add(DocumentSegment(text="Stage 1 saved paragraph", paragraph_index=0))
    with repo.stage_update(
        OWNER, analysis.id, "citations", "running", analysis_status="running"
    ):
        pass

    # Expire lease on the running analysis (simulating crashed worker)
    with factory.begin() as session:
        stored = session.get(Analysis, analysis.id)
        states = dict(stored.stage_states)
        states["lease_metadata"] = {
            "worker_id": "crashed-worker",
            "lease_expires_at": (now - timedelta(seconds=10)).isoformat(),
            "retry_count": 0,
        }
        stored.stage_states = states
        flag_modified(stored, "stage_states")

    # First recovery attempt: retry_count=0 < max_retries=2 -> reschedules
    rescheduled, interrupted = lifecycle.recover(now=now, max_retries=2)
    assert (rescheduled, interrupted) == (1, 0)

    stored = repo.get_analysis(OWNER, analysis.id)
    assert stored.status == "queued"
    assert stored.stage_states["document"]["status"] == "completed"
    assert stored.stage_states["citations"]["status"] == "queued"
    assert stored.stage_states["lease_metadata"]["retry_count"] == 1
    assert stored.stage_states["lease_metadata"]["worker_id"] is None

    # Simulate second worker picking it up and crashing again
    with factory.begin() as session:
        stored = session.get(Analysis, analysis.id)
        stored.status = "running"
        states = dict(stored.stage_states)
        states["citations"]["status"] = "running"
        states["lease_metadata"]["worker_id"] = "crashed-worker-2"
        states["lease_metadata"]["lease_expires_at"] = (
            now - timedelta(seconds=5)
        ).isoformat()
        stored.stage_states = states
        flag_modified(stored, "stage_states")

    # Second recovery attempt: retry_count=1 < max_retries=2 -> reschedules
    rescheduled, interrupted = lifecycle.recover(now=now, max_retries=2)
    assert (rescheduled, interrupted) == (1, 0)
    stored = repo.get_analysis(OWNER, analysis.id)
    assert stored.status == "queued"
    assert stored.stage_states["lease_metadata"]["retry_count"] == 2

    # Simulate third crash: retry_count=2 >= max_retries=2 -> transitions to interrupted
    with factory.begin() as session:
        stored = session.get(Analysis, analysis.id)
        stored.status = "running"
        states = dict(stored.stage_states)
        states["citations"]["status"] = "running"
        states["lease_metadata"]["worker_id"] = "crashed-worker-3"
        states["lease_metadata"]["lease_expires_at"] = (
            now - timedelta(seconds=5)
        ).isoformat()
        stored.stage_states = states
        flag_modified(stored, "stage_states")

    # Third recovery attempt: retries exhausted -> terminal interrupted
    rescheduled, interrupted = lifecycle.recover(now=now, max_retries=2)
    assert (rescheduled, interrupted) == (0, 1)

    stored = repo.get_analysis(OWNER, analysis.id)
    assert stored.status == "interrupted"
    assert stored.stage_states["document"]["status"] == "completed"
    assert stored.stage_states["citations"]["status"] == "interrupted"
    assert "retries exceeded" in stored.stage_states["citations"]["reason"].lower()
    assert stored.overall_score is None

    # Fourth recovery attempt: no active expired running jobs -> 0, 0
    assert lifecycle.recover(now=now, max_retries=2) == (0, 0)


def test_stage_idempotency_preserves_completed_stage_records(repo_system):
    _, repo, _, lifecycle = repo_system
    now = datetime.now(UTC)
    analysis = repo.create_analysis(
        OWNER,
        document_name="Test Doc",
        document_sha256="a" * 64,
        expires_at=now + timedelta(hours=1),
        status="not_run",
    )

    # Save document segment
    with repo.stage_update(OWNER, analysis.id, "document", "completed") as writer:
        writer.add(DocumentSegment(text="Immutable section text", paragraph_index=0))

    # Save a finding in privacy stage
    with repo.stage_update(
        OWNER, analysis.id, "privacy", "completed", analysis_status="running"
    ) as writer:
        writer.add(
            Finding(
                type=FindingType.PRIVACY.value,
                severity=Severity.HIGH.value,
                title="Planted SSN finding",
                description="Deterministic detection finding",
            )
        )

    # Analysis is running and crashes before next stage completes
    # Recover with bounded retry
    rescheduled, interrupted = lifecycle.recover(now=now, max_retries=2)
    assert (rescheduled, interrupted) == (1, 0)

    # Verify completed results and records survived recovery unaltered
    recovered = repo.get_analysis(OWNER, analysis.id)
    assert recovered.stage_states["document"]["status"] == "completed"
    assert recovered.stage_states["privacy"]["status"] == "completed"

    segments = repo.list_records(OWNER, analysis.id, DocumentSegment)
    assert len(segments) == 1
    assert segments[0].text == "Immutable section text"

    findings = repo.list_records(OWNER, analysis.id, Finding)
    assert len(findings) == 1
    assert findings[0].title == "Planted SSN finding"


def test_orchestrator_lease_lifecycle(repo_system):
    factory, repo, _, _ = repo_system
    now = datetime.now(UTC)
    analysis = repo.create_analysis(
        OWNER,
        document_name="Test Doc",
        document_sha256="a" * 64,
        expires_at=now + timedelta(hours=1),
        status="not_run",
        demo_fixture_id=None,
    )

    extracted = extract_text("Doc content")
    with factory.begin() as session:
        stored = session.get(Analysis, analysis.id)
        stored.document_snapshot = extracted.model_dump(mode="json")

    with repo.stage_update(OWNER, analysis.id, "document", "completed") as writer:
        for p in extracted.paragraphs:
            writer.add(
                DocumentSegment(
                    text=p.text,
                    paragraph_index=p.paragraph_index,
                    page_number=p.page_number,
                    start_offset=p.start,
                    end_offset=p.end,
                )
            )

    runners = {
        stage: StageResult(
            StageStatus.SKIPPED,
            Coverage(),
            reason="Synthetic test skip",
        )
        for stage in REVIEW_STAGES
    }

    slot = BoundedSemaphore(1)
    orchestrator = ReviewOrchestrator(
        repo,
        slot,
        runners,
        limits=ReviewLimits(overall_seconds=10, stage_seconds=2),
        worker_id="orchestrator-worker-42",
    )

    try:
        orchestrator.start(OWNER, analysis.id)
        orchestrator.executor.shutdown(wait=True)

        stored = repo.get_analysis(OWNER, analysis.id)
        assert stored.status == "completed"
        # Lease must be cleanly released in finally block
        meta = stored.stage_states.get("lease_metadata", {})
        assert meta.get("worker_id") is None
        assert meta.get("lease_expires_at") is None
    finally:
        orchestrator.close()


def test_competing_orchestrator_workers(repo_system):
    factory, repo, _, _ = repo_system
    now = datetime.now(UTC)
    analysis = repo.create_analysis(
        OWNER,
        document_name="Test Doc",
        document_sha256="a" * 64,
        expires_at=now + timedelta(hours=1),
        status="not_run",
        demo_fixture_id=None,
    )

    extracted = extract_text("Doc content")
    with factory.begin() as session:
        stored = session.get(Analysis, analysis.id)
        stored.document_snapshot = extracted.model_dump(mode="json")

    with repo.stage_update(OWNER, analysis.id, "document", "completed") as writer:
        for p in extracted.paragraphs:
            writer.add(
                DocumentSegment(
                    text=p.text,
                    paragraph_index=p.paragraph_index,
                    page_number=p.page_number,
                    start_offset=p.start,
                    end_offset=p.end,
                )
            )

    repo.queue_review(OWNER, analysis.id, REVIEW_STAGES)

    # Worker A acquires lease
    assert repo.acquire_lease(OWNER, analysis.id, "worker-A", lease_seconds=120) is True

    runners = {
        stage: StageResult(
            StageStatus.SKIPPED,
            Coverage(),
            reason="Synthetic test skip",
        )
        for stage in REVIEW_STAGES
    }

    # Worker B tries to run the same analysis through orchestrator
    slot_b = BoundedSemaphore(1)
    slot_b.acquire()
    orchestrator_b = ReviewOrchestrator(
        repo,
        slot_b,
        runners,
        limits=ReviewLimits(overall_seconds=10, stage_seconds=2),
        worker_id="worker-B",
    )

    try:
        # Worker B's worker thread fails to acquire lease and safely aborts
        orchestrator_b._run_and_release(OWNER, analysis.id, deadline=time.monotonic() + 10)
        stored = repo.get_analysis(OWNER, analysis.id)
        # Worker A still owns the lease and status remains running
        assert stored.status == "running"
        assert stored.stage_states["lease_metadata"]["worker_id"] == "worker-A"
    finally:
        orchestrator_b.close()
        repo.release_lease(OWNER, analysis.id, "worker-A")


def test_zero_raw_filing_data_in_lease_metadata(repo_system):
    _, repo, _, _ = repo_system
    now = datetime.now(UTC)
    analysis = repo.create_analysis(
        OWNER,
        document_name="Secret_Filing_2026.pdf",
        document_sha256="c" * 64,
        expires_at=now + timedelta(hours=1),
        status="queued",
    )

    assert repo.acquire_lease(
        OWNER, analysis.id, "worker-telemetry-check", lease_seconds=60
    ) is True
    stored = repo.get_analysis(OWNER, analysis.id)
    lease_meta = stored.stage_states.get("lease_metadata", {})

    # Lease metadata must only contain non-sensitive execution tokens
    assert set(lease_meta.keys()) == {"worker_id", "lease_expires_at", "retry_count"}
    assert "Secret_Filing" not in str(lease_meta)
    assert OWNER not in str(lease_meta)
