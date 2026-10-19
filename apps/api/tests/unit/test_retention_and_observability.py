import logging
import sys
import time
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from threading import BoundedSemaphore
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from filingguard.api.errors import install_error_boundary
from filingguard.db.models import Analysis, Base, DocumentSegment
from filingguard.db.repository import AnalysisRepository
from filingguard.db.session import create_db_engine, create_session_factory
from filingguard.integrations.storage.managed import RecoverableTemporaryStorage
from filingguard.integrations.storage.service import StorageError
from filingguard.modules.analyses.execution import ReviewLimits, StageResult
from filingguard.modules.analyses.lifecycle import AnalysisLifecycle
from filingguard.modules.analyses.orchestrator import REVIEW_STAGES, ReviewOrchestrator
from filingguard.modules.analyses.schemas import StageName, StageStatus

INTEGRATION_DIR = str(Path(__file__).resolve().parents[1] / "integration")
if INTEGRATION_DIR not in sys.path:
    sys.path.insert(0, INTEGRATION_DIR)
from review_workers import completed, fail  # noqa: E402

PDF = Path(__file__).resolve().parents[4] / "data/demo/curated-v1/filing.pdf"
OWNER = sha256(b"retention-observability-owner").hexdigest()


@pytest.fixture
def repo_system(tmp_path):
    engine = create_db_engine(f"sqlite+pysqlite:///{(tmp_path / 'retention.db').as_posix()}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    repo = AnalysisRepository(factory)
    with RecoverableTemporaryStorage(tmp_path / "private") as storage:
        yield factory, repo, storage, AnalysisLifecycle(repo, storage)
    engine.dispose()


def test_purge_all_expired_batch_deletes_expired_and_preserves_live(repo_system):
    factory, repo, storage, _ = repo_system
    now = datetime.now(UTC)

    expired_ids = []
    for i in range(5):
        analysis = repo.create_analysis(
            OWNER,
            document_name=f"Expired {i}",
            document_sha256="a" * 64,
            expires_at=now + timedelta(minutes=10),
        )
        expired_ids.append(analysis.id)

    live_ids = []
    for i in range(2):
        analysis = repo.create_analysis(
            OWNER,
            document_name=f"Live {i}",
            document_sha256="b" * 64,
            expires_at=now + timedelta(hours=1 + i),
        )
        live_ids.append(analysis.id)

    with factory.begin() as session:
        for i, eid in enumerate(expired_ids):
            row = session.get(Analysis, eid)
            row.created_at = now - timedelta(hours=2)
            row.expires_at = now - timedelta(minutes=5 + i)

    # Purge in batches of 2
    purged = repo.purge_all_expired(now, batch_size=2)
    assert purged == 5

    with factory() as session:
        for eid in expired_ids:
            assert session.get(Analysis, eid) is None
        for lid in live_ids:
            assert session.get(Analysis, lid) is not None


def test_purge_all_expired_cleans_up_files_and_protects_against_orphan_files(repo_system):
    factory, repo, storage, _ = repo_system
    now = datetime.now(UTC)

    pdf_bytes = PDF.read_bytes()
    file_entry = storage.store(pdf_bytes)
    analysis = repo.create_analysis(
        OWNER,
        document_name="With file",
        document_sha256="c" * 64,
        expires_at=now + timedelta(minutes=10),
        stored_file_id=UUID(file_entry.file_id),
    )
    with factory.begin() as session:
        row = session.get(Analysis, analysis.id)
        row.created_at = now - timedelta(hours=2)
        row.expires_at = now - timedelta(minutes=10)

    # Calling purge_all_expired without delete_file should protect against orphaned files
    purged = repo.purge_all_expired(now, delete_file=None, batch_size=10)
    assert purged == 0
    with factory() as session:
        assert session.get(Analysis, analysis.id) is not None
    assert storage.read(file_entry.file_id) == pdf_bytes

    # Calling with delete_file successfully deletes the file and the database row
    purged = repo.purge_all_expired(now, delete_file=storage.delete, batch_size=10)
    assert purged == 1
    with factory() as session:
        assert session.get(Analysis, analysis.id) is None
    assert not storage._entries


def test_purge_all_expired_handles_storage_delete_failure(repo_system, monkeypatch):
    factory, repo, storage, _ = repo_system
    now = datetime.now(UTC)

    pdf_bytes = PDF.read_bytes()
    file1 = storage.store(pdf_bytes)
    file2 = storage.store(pdf_bytes)

    a1 = repo.create_analysis(
        OWNER,
        document_name="Fail file",
        document_sha256="1" * 64,
        expires_at=now + timedelta(minutes=10),
        stored_file_id=UUID(file1.file_id),
    )
    a2 = repo.create_analysis(
        OWNER,
        document_name="Succeed file",
        document_sha256="2" * 64,
        expires_at=now + timedelta(minutes=10),
        stored_file_id=UUID(file2.file_id),
    )
    with factory.begin() as session:
        for a, mins in ((a1, 10), (a2, 5)):
            row = session.get(Analysis, a.id)
            row.created_at = now - timedelta(hours=2)
            row.expires_at = now - timedelta(minutes=mins)

    original_delete = storage.delete

    def failing_delete(file_id: str):
        if file_id == file1.file_id:
            raise StorageError("Disk error")
        return original_delete(file_id)

    purged = repo.purge_all_expired(now, delete_file=failing_delete, batch_size=10)
    assert purged == 1
    with factory() as session:
        assert session.get(Analysis, a1.id) is not None
        assert session.get(Analysis, a2.id) is None


def test_purge_all_expired_validates_inputs(repo_system):
    _, repo, _, _ = repo_system
    with pytest.raises(ValueError, match="timezone-aware"):
        repo.purge_all_expired(datetime.now())

    with pytest.raises(ValueError, match="batch size"):
        repo.purge_all_expired(datetime.now(UTC), batch_size=0)

    with pytest.raises(ValueError, match="batch size"):
        repo.purge_all_expired(datetime.now(UTC), batch_size=501)


def test_lifecycle_purge_all_expired(repo_system):
    factory, repo, storage, lifecycle = repo_system
    now = datetime.now(UTC)

    item = lifecycle.create_pdf(
        OWNER,
        PDF.read_bytes(),
        document_name="Expiring PDF",
        expires_at=now + timedelta(minutes=10),
    )
    with factory.begin() as session:
        row = session.get(Analysis, item.id)
        row.created_at = now - timedelta(hours=2)
        row.expires_at = now - timedelta(seconds=1)

    result = lifecycle.purge_all_expired(now)
    assert result.analyses_deleted == 1
    assert result.failures == 0
    with factory() as session:
        assert session.get(Analysis, item.id) is None


def test_orchestrator_logs_correlation_id_and_timing_without_leaking_content(
    repo_system, caplog
):
    factory, repo, storage, lifecycle = repo_system
    now = datetime.now(UTC)

    secret_content = "SECRET_UNREDACTED_FILING_TEXT_778899"
    analysis = repo.create_analysis(
        OWNER,
        document_name="Sensitive brief",
        document_sha256=sha256(secret_content.encode()).hexdigest(),
        expires_at=now + timedelta(minutes=30),
    )
    with repo.stage_update(OWNER, analysis.id, "document", "completed") as writer:
        writer.add(
            DocumentSegment(
                text=secret_content,
                paragraph_index=0,
                start_offset=0,
                end_offset=len(secret_content),
            )
        )
        writer.analysis.document_snapshot = {
            "text": secret_content,
            "paragraphs": [
                {
                    "text": secret_content,
                    "paragraph_index": 0,
                    "start": 0,
                    "end": len(secret_content),
                }
            ],
        }

    runners = {
        StageName.PRIVACY: completed,
        **{
            s: StageResult(status=StageStatus.SKIPPED, reason="Skipped in test")
            for s in REVIEW_STAGES
            if s != StageName.PRIVACY
        },
    }

    slot = BoundedSemaphore(1)
    orchestrator = ReviewOrchestrator(
        repo,
        slot,
        runners,
        limits=ReviewLimits(overall_seconds=30, stage_seconds=10),
    )

    with caplog.at_level(logging.INFO, logger="filingguard.modules.analyses.orchestrator"):
        orchestrator.start(OWNER, analysis.id)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            refreshed = repo.get_analysis(OWNER, analysis.id)
            if (
                refreshed.status == "completed"
                and f"review.job.finish analysis_id={analysis.id}" in caplog.text
            ):
                break
            time.sleep(0.05)

    aid = str(analysis.id)
    assert f"review.job.start analysis_id={aid} correlation_id={aid}" in caplog.text
    assert f"review.stage.start analysis_id={aid} correlation_id={aid} stage=privacy" in caplog.text
    assert (
        f"review.stage.finish analysis_id={aid} correlation_id={aid} "
        "stage=privacy status=completed duration_ms="
    ) in caplog.text
    assert (
        f"review.job.finish analysis_id={aid} correlation_id={aid} "
        "status=completed completed_stages=8 duration_ms="
    ) in caplog.text

    # LOG-003 & NFR-023: zero filing content leaked in logs
    assert secret_content not in caplog.text
    assert "778899" not in caplog.text
    orchestrator.close()


def test_orchestrator_stage_failure_logs_correlation_id_and_timing(repo_system, caplog):
    factory, repo, storage, _ = repo_system
    now = datetime.now(UTC)

    analysis = repo.create_analysis(
        OWNER,
        document_name="Failing stage test",
        document_sha256="d" * 64,
        expires_at=now + timedelta(minutes=30),
    )
    with repo.stage_update(OWNER, analysis.id, "document", "completed") as writer:
        writer.add(
            DocumentSegment(
                text="Sample text",
                paragraph_index=0,
                start_offset=0,
                end_offset=11,
            )
        )
        writer.analysis.document_snapshot = {
            "text": "Sample text",
            "paragraphs": [{"text": "Sample text", "paragraph_index": 0, "start": 0, "end": 11}],
        }

    runners = {
        StageName.PRIVACY: fail,
        **{
            s: StageResult(status=StageStatus.SKIPPED, reason="Skipped")
            for s in REVIEW_STAGES
            if s != StageName.PRIVACY
        },
    }

    slot = BoundedSemaphore(1)
    orchestrator = ReviewOrchestrator(
        repo,
        slot,
        runners,
        limits=ReviewLimits(overall_seconds=10, stage_seconds=2),
    )

    with caplog.at_level(logging.ERROR, logger="filingguard.modules.analyses.orchestrator"):
        orchestrator.start(OWNER, analysis.id)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            refreshed = repo.get_analysis(OWNER, analysis.id)
            if refreshed.status in {"partial", "failed"}:
                break
            time.sleep(0.05)

    aid = str(analysis.id)
    assert (
        f"review.stage.finish analysis_id={aid} correlation_id={aid} "
        "stage=privacy status=failed error_type=StageExecutionError duration_ms="
    ) in caplog.text
    orchestrator.close()


def test_error_boundary_logs_correlation_id_for_analysis_path(caplog):
    app = FastAPI()
    install_error_boundary(app)

    @app.get("/api/v1/analyses/{analysis_id}/custom-action")
    def fail_endpoint(analysis_id: UUID):
        raise RuntimeError("Something exploded with private data: TOP_SECRET_VALUE")

    target_id = uuid4()
    with TestClient(app) as client, caplog.at_level(logging.ERROR):
        response = client.get(f"/api/v1/analyses/{target_id}/custom-action")
        assert response.status_code == 500

    assert f"correlation_id={target_id}" in caplog.text
    assert "API failure (RuntimeError)" in caplog.text
    assert "TOP_SECRET_VALUE" not in caplog.text


def test_error_boundary_logs_correlation_id_from_header_and_query(caplog):
    app = FastAPI()
    install_error_boundary(app)

    @app.get("/api/v1/health-check")
    def fail_health():
        raise RuntimeError("Health check failure")

    header_cid = uuid4()
    with TestClient(app) as client, caplog.at_level(logging.ERROR):
        response = client.get("/api/v1/health-check", headers={"X-Correlation-ID": str(header_cid)})
        assert response.status_code == 500
    assert f"correlation_id={header_cid}" in caplog.text

    caplog.clear()
    query_cid = uuid4()
    with TestClient(app) as client, caplog.at_level(logging.ERROR):
        response = client.get(f"/api/v1/health-check?analysis_id={query_cid}")
        assert response.status_code == 500
    assert f"correlation_id={query_cid}" in caplog.text


def test_purge_all_expired_continues_past_full_batch_of_failures(repo_system):
    factory, repo, storage, _ = repo_system
    now = datetime.now(UTC)

    pdf_bytes = PDF.read_bytes()
    file1 = storage.store(pdf_bytes)
    file2 = storage.store(pdf_bytes)
    file3 = storage.store(pdf_bytes)

    a1 = repo.create_analysis(
        OWNER,
        document_name="Fail 1",
        document_sha256="1" * 64,
        expires_at=now + timedelta(minutes=10),
        stored_file_id=UUID(file1.file_id),
    )
    a2 = repo.create_analysis(
        OWNER,
        document_name="Fail 2",
        document_sha256="2" * 64,
        expires_at=now + timedelta(minutes=10),
        stored_file_id=UUID(file2.file_id),
    )
    a3 = repo.create_analysis(
        OWNER,
        document_name="Succeed 3",
        document_sha256="3" * 64,
        expires_at=now + timedelta(minutes=10),
        stored_file_id=UUID(file3.file_id),
    )
    with factory.begin() as session:
        for a, mins in ((a1, 15), (a2, 10), (a3, 5)):
            row = session.get(Analysis, a.id)
            row.created_at = now - timedelta(hours=2)
            row.expires_at = now - timedelta(minutes=mins)

    original_delete = storage.delete

    def failing_delete(file_id: str):
        if file_id in {file1.file_id, file2.file_id}:
            raise StorageError("Disk error on old batch")
        return original_delete(file_id)

    # Batch size of 2: first batch is [a1, a2], which BOTH fail.
    # The fix ensures it does not abort prematurely, but continues to the next batch with a3.
    purged = repo.purge_all_expired(now, delete_file=failing_delete, batch_size=2)
    assert purged == 1
    with factory() as session:
        assert session.get(Analysis, a1.id) is not None
        assert session.get(Analysis, a2.id) is not None
        assert session.get(Analysis, a3.id) is None


def test_lifecycle_purge_all_expired_accurately_counts_failures(repo_system, monkeypatch, caplog):
    factory, repo, storage, lifecycle = repo_system
    now = datetime.now(UTC)

    pdf_bytes = PDF.read_bytes()
    file1 = storage.store(pdf_bytes)
    file2 = storage.store(pdf_bytes)

    a1 = repo.create_analysis(
        OWNER,
        document_name="Failing analysis",
        document_sha256="1" * 64,
        expires_at=now + timedelta(minutes=10),
        stored_file_id=UUID(file1.file_id),
    )
    a2 = repo.create_analysis(
        OWNER,
        document_name="Succeeding analysis",
        document_sha256="2" * 64,
        expires_at=now + timedelta(minutes=10),
        stored_file_id=UUID(file2.file_id),
    )
    with factory.begin() as session:
        for a in (a1, a2):
            row = session.get(Analysis, a.id)
            row.created_at = now - timedelta(hours=2)
            row.expires_at = now - timedelta(minutes=5)

    real_delete = storage.delete

    def failing_delete(file_id: str):
        if file_id == file1.file_id:
            raise StorageError()
        return real_delete(file_id)

    monkeypatch.setattr(storage, "delete", failing_delete)

    with caplog.at_level(logging.INFO, logger="filingguard.modules.analyses.lifecycle"):
        result = lifecycle.purge_all_expired(now, batch_size=1)

    assert result.analyses_deleted == 1
    assert result.failures >= 1
    assert "retention.purge_all_expired analyses_deleted=1 files_deleted=" in caplog.text
