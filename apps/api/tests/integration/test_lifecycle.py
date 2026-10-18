from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import event, select
from sqlalchemy.exc import SQLAlchemyError

from filingguard.db.models import Analysis, Base, DocumentSegment
from filingguard.db.repository import AnalysisNotFound, AnalysisRepository
from filingguard.db.session import create_db_engine, create_session_factory
from filingguard.integrations.storage.managed import RecoverableTemporaryStorage
from filingguard.integrations.storage.service import StorageError
from filingguard.modules.analyses.lifecycle import AnalysisLifecycle

PDF = Path(__file__).resolve().parents[4] / "data/demo/curated-v1/filing.pdf"
OWNER = sha256(b"synthetic-owner").hexdigest()
OTHER = sha256(b"other-owner").hexdigest()


@pytest.fixture
def system(tmp_path):
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    repo = AnalysisRepository(factory)
    with RecoverableTemporaryStorage(tmp_path / "private") as storage:
        yield factory, repo, storage, AnalysisLifecycle(repo, storage)
    engine.dispose()


def create(lifecycle):
    return lifecycle.create_pdf(
        OWNER,
        PDF.read_bytes(),
        document_name="Synthetic filing",
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )


def test_analysis_and_file_have_one_owner_and_delete_together(system):
    factory, repo, storage, lifecycle = system
    analysis = create(lifecycle)
    file_id = str(analysis.stored_file_id)
    assert storage.read(file_id) == PDF.read_bytes()
    assert analysis.document_sha256 == sha256(PDF.read_bytes()).hexdigest()
    with repo.stage_update(OWNER, analysis.id, "document", "completed") as writer:
        writer.add(DocumentSegment(text="Saved first stage", paragraph_index=0))
    with pytest.raises(AnalysisNotFound):
        lifecycle.delete(OTHER, analysis.id)
    assert storage.read(file_id) == PDF.read_bytes()
    with pytest.raises(ValueError, match="cleanup"):
        repo.delete_analysis(OWNER, analysis.id)
    lifecycle.delete(OWNER, analysis.id)
    with factory() as session:
        assert session.get(Analysis, analysis.id) is None
        assert not list(session.scalars(select(DocumentSegment)))
    assert not storage._entries


def test_creation_failure_compensates_file_write(system, monkeypatch):
    _, repo, storage, lifecycle = system

    def fail(*args, **kwargs):
        raise SQLAlchemyError("Synthetic database failure")

    monkeypatch.setattr(repo, "create_analysis", fail)
    with pytest.raises(SQLAlchemyError):
        create(lifecycle)
    assert not storage._entries
    assert not list(storage._root.glob("*.pdf"))
    assert {path.name for path in storage._root.iterdir()} == {".owner.json", ".lease"}


def test_file_delete_failure_keeps_database_records_for_retry(system, monkeypatch):
    factory, repo, storage, lifecycle = system
    analysis = create(lifecycle)
    original = storage.delete

    def fail(file_id):
        raise StorageError()

    monkeypatch.setattr(storage, "delete", fail)
    with pytest.raises(StorageError):
        lifecycle.delete(OWNER, analysis.id)
    assert repo.get_analysis(OWNER, analysis.id).stored_file_id == analysis.stored_file_id
    monkeypatch.setattr(storage, "delete", original)
    lifecycle.delete(OWNER, analysis.id)
    with factory() as session:
        assert session.get(Analysis, analysis.id) is None


def test_database_commit_failure_after_file_delete_is_retryable(system):
    _, repo, storage, lifecycle = system
    analysis = create(lifecycle)
    blocked = [True]

    def fail(session):
        if blocked[0]:
            blocked[0] = False
            raise SQLAlchemyError("Synthetic commit failure")

    event.listen(repo._factory, "before_commit", fail)
    try:
        with pytest.raises(SQLAlchemyError):
            lifecycle.delete(OWNER, analysis.id)
        assert repo.get_analysis(OWNER, analysis.id)
        assert not storage._entries
        lifecycle.delete(OWNER, analysis.id)
        with pytest.raises(AnalysisNotFound):
            repo.get_analysis(OWNER, analysis.id)
    finally:
        event.remove(repo._factory, "before_commit", fail)


def test_expiry_sweep_retries_failed_rows_without_deleting_other_owners_live_data(
    system, monkeypatch
):
    factory, repo, storage, lifecycle = system
    first, second, live = create(lifecycle), create(lifecycle), create(lifecycle)
    now = datetime.now(UTC)
    with factory.begin() as session:
        for item in (first, second):
            row = session.get(Analysis, item.id)
            row.created_at = now - timedelta(hours=2)
            row.expires_at = now - timedelta(seconds=1)
    original = storage.delete

    def fail_one(file_id):
        if file_id == str(first.stored_file_id):
            raise StorageError()
        return original(file_id)

    monkeypatch.setattr(storage, "delete", fail_one)
    outcome = lifecycle.cleanup(now)
    assert outcome.analyses_deleted == 1 and outcome.failures == 1
    with factory() as session:
        assert session.get(Analysis, first.id)
        assert session.get(Analysis, second.id) is None
    assert repo.get_analysis(OWNER, live.id)
    monkeypatch.setattr(storage, "delete", original)
    assert lifecycle.cleanup(now).analyses_deleted == 1
    assert storage.read(str(live.stored_file_id)) == PDF.read_bytes()


def test_recovery_preserves_committed_stage_and_interrupts_incomplete_work(system):
    _, repo, _, lifecycle = system
    analysis = create(lifecycle)
    with repo.stage_update(OWNER, analysis.id, "document", "completed") as writer:
        writer.add(DocumentSegment(text="Saved stage", paragraph_index=0))
    with repo.stage_update(OWNER, analysis.id, "citations", "running", analysis_status="running"):
        pass
    assert lifecycle.recover(max_retries=0) == (0, 1)
    recovered = repo.get_analysis(OWNER, analysis.id)
    assert recovered.status == "interrupted"
    assert recovered.stage_states["document"]["status"] == "completed"
    assert recovered.stage_states["citations"]["status"] == "interrupted"
    assert repo.list_records(OWNER, analysis.id, DocumentSegment)[0].text == "Saved stage"
    assert recovered.overall_score is None
    assert lifecycle.recover(max_retries=0) == (0, 0)


def test_expiry_and_file_reference_validation_before_storage(system):
    _, repo, storage, lifecycle = system
    for expiry in (
        datetime.now(),
        datetime.now(UTC) - timedelta(seconds=1),
        datetime.now(UTC) + timedelta(hours=2),
    ):
        with pytest.raises(ValueError):
            lifecycle.create_pdf(OWNER, PDF.read_bytes(), document_name="Test", expires_at=expiry)
    assert not storage._entries
    with pytest.raises(ValueError):
        repo.create_analysis(
            OWNER,
            document_name="Test",
            document_sha256="a" * 64,
            expires_at=datetime.now(UTC) + timedelta(minutes=1),
            stored_file_id=str(uuid4()),
        )
