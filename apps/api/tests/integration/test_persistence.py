"""Local-only migration, ownership and stage-transaction regressions."""

from datetime import UTC, datetime, timedelta, timezone
from hashlib import sha256
from io import StringIO
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, inspect, select, text
from sqlalchemy.exc import IntegrityError, StatementError

from filingguard.db.models import (
    Analysis,
    Authority,
    Base,
    Citation,
    Claim,
    ClaimAuthorityLink,
    DocumentSegment,
    EvidenceRecord,
    Finding,
    Quote,
)
from filingguard.db.repository import RECORD_TYPES, AnalysisNotFound, AnalysisRepository
from filingguard.db.session import (
    DatabaseConfigurationError,
    create_db_engine,
    create_session_factory,
    get_database_url,
    transaction,
)
from filingguard.modules.analyses.schemas import Coverage, StageState

API_ROOT = Path(__file__).resolve().parents[2]
OWNER = sha256(b"synthetic-owner").hexdigest()
OTHER_OWNER = sha256(b"other-synthetic-owner").hexdigest()
DOCUMENT_HASH = sha256(b"Synthetic filing text").hexdigest()


def alembic_config(output=None):
    return Config(str(API_ROOT / "alembic.ini"), output_buffer=output)


@pytest.fixture
def database():
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        config = alembic_config()
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        assert connection.scalar(text("PRAGMA foreign_keys")) == 1
    factory = create_session_factory(engine)
    yield engine, factory, AnalysisRepository(factory)
    engine.dispose()


def new_analysis(repository, owner=OWNER, **kwargs):
    return repository.create_analysis(
        owner,
        document_name="Synthetic filing",
        document_sha256=DOCUMENT_HASH,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
        **kwargs,
    )


def test_file_migration_preserves_existing_parent_and_child_rows():
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    try:
        with engine.begin() as connection:
            config = alembic_config()
            config.attributes["connection"] = connection
            command.upgrade(config, "0001_initial")
            identity = uuid4().hex
            now = datetime.now(UTC)
            connection.execute(text(
                "INSERT INTO analyses (id, owner_hash, document_name, document_sha256, "
                "created_at, updated_at, expires_at) VALUES "
                "(:id, :owner, 'Synthetic', :hash, :now, :now, :expiry)"
            ), {"id": identity, "owner": OWNER, "hash": DOCUMENT_HASH,
                "now": now, "expiry": now + timedelta(hours=1)})
            connection.execute(text(
                "INSERT INTO document_segments (id, analysis_id, paragraph_index, text) "
                "VALUES (:id, :analysis, 0, 'Previously saved text')"
            ), {"id": uuid4().hex, "analysis": identity})
            command.upgrade(config, "head")
            assert connection.scalar(text("SELECT COUNT(*) FROM analyses")) == 1
            assert (
                connection.scalar(text("SELECT text FROM document_segments"))
                == "Previously saved text"
            )
            command.downgrade(config, "0001_initial")
            assert connection.scalar(text("SELECT COUNT(*) FROM document_segments")) == 1
            assert "stored_file_id" not in {
                column["name"] for column in inspect(connection).get_columns("analyses")
            }
    finally:
        engine.dispose()


def test_citation_extraction_migration_preserves_populated_rows():
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    try:
        with engine.begin() as connection:
            config = alembic_config()
            config.attributes["connection"] = connection
            command.upgrade(config, "0003_anonymous_sessions")
            identity, segment_id, citation_id = (uuid4().hex for _ in range(3))
            now = datetime.now(UTC)
            connection.execute(text(
                "INSERT INTO analyses (id, owner_hash, document_name, document_sha256, "
                "created_at, updated_at, expires_at) VALUES "
                "(:id, :owner, 'Synthetic', :hash, :now, :now, :expiry)"
            ), {"id": identity, "owner": OWNER, "hash": DOCUMENT_HASH,
                "now": now, "expiry": now + timedelta(hours=1)})
            connection.execute(text(
                "INSERT INTO document_segments (id, analysis_id, paragraph_index, text) "
                "VALUES (:id, :analysis, 0, '347 U.S. 483')"
            ), {"id": segment_id, "analysis": identity})
            connection.execute(text(
                "INSERT INTO citations (id, analysis_id, segment_id, raw_text, "
                "start_offset, end_offset) VALUES (:id, :analysis, :segment, '347 U.S. 483', 0, 12)"
            ), {"id": citation_id, "analysis": identity, "segment": segment_id})
            command.upgrade(config, "head")
            assert connection.scalar(text("SELECT extraction_metadata FROM citations")) == "{}"
            assert connection.scalar(text("SELECT verification_status FROM citations")) == "not_run"
            assert connection.scalar(text("SELECT raw_text FROM citations")) == "347 U.S. 483"
            assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
            command.downgrade(config, "0003_anonymous_sessions")
            assert "extraction_metadata" not in {
                column["name"] for column in inspect(connection).get_columns("citations")
            }
            assert connection.scalar(text("SELECT COUNT(*) FROM citations")) == 1
            assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
    finally:
        engine.dispose()


def seed_graph(repository, analysis):
    ids = {model: uuid4() for model in RECORD_TYPES}
    standalone_id = uuid4()
    source = "A synthetic source passage."
    records = [
        DocumentSegment(
            id=ids[DocumentSegment],
            paragraph_index=0,
            text="Synthetic filing text",
            page_number=1,
            start_offset=0,
            end_offset=21,
        ),
        Authority(
            id=ids[Authority],
            source="synthetic",
            external_id="fixture-1",
            source_url="https://example.invalid/opinion/1",
            opinion_text=source,
            opinion_text_available=True,
            source_sha256=sha256(source.encode()).hexdigest(),
            retrieved_at=datetime.now(timezone(timedelta(hours=5))),
            source_metadata={"fixture_id": "public-synthetic-1"},
        ),
        Citation(
            id=ids[Citation],
            raw_text="1 Test 1",
            segment_id=ids[DocumentSegment],
            authority_id=ids[Authority],
            start_offset=0,
            end_offset=8,
        ),
        Claim(
            id=ids[Claim],
            text="Synthetic proposition",
            segment_id=ids[DocumentSegment],
            extraction_method="heuristic",
            confidence=0.5,
        ),
        ClaimAuthorityLink(
            id=ids[ClaimAuthorityLink],
            claim_id=ids[Claim],
            citation_id=ids[Citation],
            authority_id=ids[Authority],
        ),
        Quote(
            id=ids[Quote],
            quote_text="Synthetic quote",
            segment_id=ids[DocumentSegment],
            citation_id=ids[Citation],
            similarity=0.6,
        ),
        Finding(
            id=ids[Finding],
            type="quote",
            severity="medium",
            title="Review quote",
            description="Synthetic discrepancy",
            stage="quotes",
            segment_id=ids[DocumentSegment],
            citation_id=ids[Citation],
            authority_id=ids[Authority],
            claim_id=ids[Claim],
            quote_id=ids[Quote],
            document_excerpt="Synthetic quote",
        ),
        EvidenceRecord(
            id=ids[EvidenceRecord],
            finding_id=ids[Finding],
            segment_id=ids[DocumentSegment],
            citation_id=ids[Citation],
            authority_id=ids[Authority],
            claim_id=ids[Claim],
            quote_id=ids[Quote],
            source_type="opinion_text",
            source_label="Synthetic opinion",
            excerpt=source,
            snapshot_text=source,
            source_url="https://example.invalid/opinion/1",
            source_sha256=sha256(source.encode()).hexdigest(),
            retrieved_at=datetime.now(UTC),
            source_start_offset=0,
            source_end_offset=len(source),
            method="exact",
            method_version="v1",
            model_version="synthetic-model-v1",
            prompt_version="synthetic-prompt-v1",
            source_metadata={"fixture_id": "public-synthetic-1"},
        ),
        EvidenceRecord(
            id=standalone_id,
            citation_id=ids[Citation],
            authority_id=ids[Authority],
            source_type="opinion_text",
            source_label="Supported check",
            excerpt=source,
            snapshot_text=source,
            method="exact",
            method_version="v1",
        ),
    ]
    with repository.stage_update(
        analysis.owner_hash, analysis.id, "document", "completed"
    ) as stage:
        # Producer ordering must not weaken FK checks or require caller-managed flushes.
        stage.add(*reversed(records))
    return ids, standalone_id


def test_migration_matches_metadata_and_downgrades(database):
    engine, _, _ = database
    with engine.begin() as connection:
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
        inspector = inspect(connection)
        for table in Base.metadata.sorted_tables:
            actual = inspector.get_check_constraints(table.name)
            expected = {
                constraint.name
                for constraint in table.constraints
                if constraint.__class__.__name__ == "CheckConstraint"
            }
            assert {constraint["name"] for constraint in actual} == expected
            for foreign_key in inspector.get_foreign_keys(table.name):
                assert foreign_key["options"]["ondelete"] == "CASCADE"
        config = alembic_config()
        config.attributes["connection"] = connection
        command.downgrade(config, "base")
        assert set(inspect(connection).get_table_names()) == {"alembic_version"}
        command.upgrade(config, "head")
        assert set(Base.metadata.tables) <= set(inspect(connection).get_table_names())


@pytest.mark.parametrize(
    "url",
    [
        "sqlite+pysqlite:///:memory:",
        "postgresql+psycopg://synthetic:never-print-this@example.invalid/test?sslmode=require",
    ],
)
def test_offline_migration_never_connects_or_discloses_url(monkeypatch, url):
    import filingguard.db.session as db_session

    def forbidden_engine(*args, **kwargs):
        pytest.fail("Offline migration must not create an engine")

    monkeypatch.setattr(db_session, "create_db_engine", forbidden_engine)
    monkeypatch.setenv("DATABASE_URL", url)
    output = StringIO()
    command.upgrade(alembic_config(output), "head", sql=True)
    script = output.getvalue()
    assert "CREATE TABLE analyses" in script
    assert "CREATE TABLE evidence_records" in script
    assert "never-print-this" not in script
    assert "example.invalid" not in script
    if url.startswith("postgresql"):
        assert "JSONB" in script and "UUID" in script and "TIMESTAMP WITH TIME ZONE" in script
    else:
        # Execute the offline SQL against a fresh SQLite DB, with FK enforcement enabled.
        engine = create_db_engine("sqlite+pysqlite:///:memory:")
        try:
            raw = engine.raw_connection()
            try:
                raw.driver_connection.executescript(script)
                assert len(inspect(engine).get_table_names()) == 11
            finally:
                raw.close()
        finally:
            engine.dispose()


def test_roundtrip_relationships_provenance_and_unknown_defaults(database):
    _, factory, repository = database
    analysis = new_analysis(repository)
    assert isinstance(analysis.id, UUID)
    assert analysis.status == "not_run"
    assert analysis.stage_states == {}
    assert analysis.overall_score is None and analysis.risk_level is None
    assert analysis.ai_used is None
    assert analysis.created_at.tzinfo == UTC and analysis.expires_at.tzinfo == UTC
    ids, standalone = seed_graph(repository, analysis)
    with factory() as session:
        stored = session.get(Analysis, analysis.id)
        assert len(stored.authorities) == 1
        assert StageState.model_validate(stored.stage_states["document"]).status == "completed"
        citation = session.get(Citation, ids[Citation])
        assert citation.segment.id == ids[DocumentSegment]
        assert citation.authority.id == ids[Authority]
        assert citation.verification_status == "not_run"
        link = session.get(ClaimAuthorityLink, ids[ClaimAuthorityLink])
        assert link.claim.id == ids[Claim] and link.citation.id == ids[Citation]
        assert link.support_status == "not_run"
        assert session.get(Quote, ids[Quote]).match_status == "not_run"
        evidence = session.get(EvidenceRecord, ids[EvidenceRecord])
        assert evidence.finding.id == ids[Finding]
        assert evidence.source_sha256 == sha256(evidence.excerpt.encode()).hexdigest()
        assert evidence.snapshot_text == evidence.excerpt
        assert evidence.source_end_offset == len(evidence.excerpt)
        assert evidence.method_version == "v1"
        assert evidence.model_version == "synthetic-model-v1"
        assert evidence.prompt_version == "synthetic-prompt-v1"
        assert evidence.source_metadata == {"fixture_id": "public-synthetic-1"}
        assert evidence.retrieved_at.tzinfo == UTC
        assert citation.authority.retrieved_at.tzinfo == UTC
        assert session.get(EvidenceRecord, standalone).finding_id is None
        assert len(stored.evidence_records) == 2


def test_wrong_owner_and_analysis_cannot_read_write_or_delete(database):
    _, _, repository = database
    analysis = new_analysis(repository)
    other = new_analysis(repository, OTHER_OWNER)
    ids, _ = seed_graph(repository, analysis)
    for operation in (
        lambda: repository.get_analysis(OTHER_OWNER, analysis.id),
        lambda: repository.list_records(OTHER_OWNER, analysis.id, Finding),
        lambda: repository.get_record(OTHER_OWNER, analysis.id, Finding, ids[Finding]),
        lambda: repository.delete_analysis(OTHER_OWNER, analysis.id),
    ):
        with pytest.raises(AnalysisNotFound):
            operation()
    with (
        pytest.raises(AnalysisNotFound),
        repository.stage_update(
            OTHER_OWNER,
            analysis.id,
            "quotes",
            "completed",
        ),
    ):
        pytest.fail("Wrong owner must never enter a stage transaction")
    assert repository.get_record(OTHER_OWNER, other.id, Finding, ids[Finding]) is None
    assert repository.list_records(OTHER_OWNER, other.id, Finding) == []
    assert set(repository.get_analysis(OWNER, analysis.id).stage_states) == {"document"}


def test_expired_analysis_fails_closed_for_every_repository_operation(database):
    _, factory, repository = database
    analysis = new_analysis(repository)
    ids, _ = seed_graph(repository, analysis)
    with transaction(factory) as session:
        stored = session.get(Analysis, analysis.id)
        stored.created_at = datetime.now(UTC) - timedelta(days=2)
        stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    for operation in (
        lambda: repository.get_analysis(OWNER, analysis.id),
        lambda: repository.list_records(OWNER, analysis.id, EvidenceRecord),
        lambda: repository.get_record(OWNER, analysis.id, Finding, ids[Finding]),
        lambda: repository.delete_analysis(OWNER, analysis.id),
    ):
        with pytest.raises(AnalysisNotFound):
            operation()
    with (
        pytest.raises(AnalysisNotFound),
        repository.stage_update(
            OWNER,
            analysis.id,
            "quotes",
            "running",
        ),
    ):
        pytest.fail("Expired analysis must not enter a stage transaction")
    # A future private retention job may delete expired rows directly; this is not public access.
    with factory() as session:
        assert session.get(Finding, ids[Finding]) is not None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"stage": "unknown", "status": "completed"},
        {"stage": "quotes", "status": "not_applicable"},
        {"stage": "quotes", "status": "unavailable"},
        {"stage": "quotes", "status": "completed", "coverage": {"eligible": 1, "pending": 1}},
        {"stage": "quotes", "status": "skipped", "reason": "No quotes"},
    ],
)
def test_stage_state_rejects_unknown_names_missing_reasons_and_incoherent_coverage(
    database,
    kwargs,
):
    _, _, repository = database
    analysis = new_analysis(repository)
    with pytest.raises(ValueError), repository.stage_update(OWNER, analysis.id, **kwargs):
        pytest.fail("Invalid stage state must not enter a write transaction")
    assert repository.get_analysis(OWNER, analysis.id).stage_states == {}


def test_skipped_stage_persists_explicit_reason_and_inapplicability(database):
    _, _, repository = database
    analysis = new_analysis(repository)
    with repository.stage_update(
        OWNER,
        analysis.id,
        "quotes",
        "skipped",
        applicable=False,
        reason="No quotations in this synthetic filing",
    ):
        pass
    state = StageState.model_validate(
        repository.get_analysis(OWNER, analysis.id).stage_states["quotes"]
    )
    assert state.status == "skipped" and state.applicable is False
    assert state.coverage.evaluated == 0 and state.reason is not None


def test_stage_failure_rolls_back_only_new_work_and_can_save_partial_state(database):
    _, _, repository = database
    analysis = new_analysis(repository, status="queued")
    ids, _ = seed_graph(repository, analysis)
    with (
        pytest.raises(IntegrityError),
        repository.stage_update(
            OWNER,
            analysis.id,
            "quotes",
            "completed",
            analysis_status="completed",
        ) as stage,
    ):
        stage.add(
            Finding(
                type="quote",
                severity="high",
                title="Uncommitted output",
                description="Must roll back",
            )
        )
        stage.add(
            EvidenceRecord(
                source_type="opinion_text",
                source_label="Missing finding",
                finding_id=uuid4(),
                excerpt="Synthetic",
                method="exact",
                method_version="v1",
            )
        )
    assert repository.get_analysis(OWNER, analysis.id).status == "queued"
    assert [finding.id for finding in repository.list_records(OWNER, analysis.id, Finding)] == [
        ids[Finding],
    ]
    assert len(repository.list_records(OWNER, analysis.id, EvidenceRecord)) == 2
    with (
        pytest.raises(RuntimeError),
        repository.stage_update(
            OWNER,
            analysis.id,
            "citations",
            "completed",
        ),
    ):
        raise RuntimeError("Synthetic producer failure")
    with repository.stage_update(
        OWNER,
        analysis.id,
        "quotes",
        "unavailable",
        analysis_status="partial",
        reason="Synthetic source unavailable",
        coverage=Coverage(eligible=1, unavailable=1),
    ):
        pass
    stored = repository.get_analysis(OWNER, analysis.id)
    assert stored.status == "partial"
    assert set(stored.stage_states) == {"document", "quotes"}
    quote_state = StageState.model_validate(stored.stage_states["quotes"])
    assert quote_state.status == "unavailable" and quote_state.coverage.unavailable == 1
    assert stored.overall_score is None and stored.risk_level is None


# Exercise every composite entity-reference edge using inserts that bypass the repository.
CROSS_ANALYSIS_EDGES = [
    (model, column, target)
    for model in RECORD_TYPES
    for constraint in model.__table__.foreign_key_constraints
    if len(constraint.elements) == 2
    for column, target in [
        (
            constraint.elements[1].parent.name,
            next(
                candidate
                for candidate in RECORD_TYPES
                if candidate.__tablename__ == constraint.elements[1].column.table.name
            ),
        )
    ]
]


@pytest.mark.parametrize(
    "model,column,target",
    CROSS_ANALYSIS_EDGES,
    ids=[f"{m.__name__}.{c}" for m, c, _ in CROSS_ANALYSIS_EDGES],
)
def test_database_rejects_every_cross_analysis_reference(database, model, column, target):
    _, factory, repository = database
    first = new_analysis(repository)
    second = new_analysis(repository, OTHER_OWNER)
    local, _ = seed_graph(repository, first)
    foreign, _ = seed_graph(repository, second)
    with factory() as session:
        original = session.get(model, local[model])
        values = {
            attribute.key: getattr(original, attribute.key)
            for attribute in inspect(model).column_attrs
        }
    values.update(id=uuid4(), **{column: foreign[target]})
    # Core INSERT cannot be protected by repository-only validation or ORM hooks.
    with pytest.raises(IntegrityError), transaction(factory) as session:
        session.execute(model.__table__.insert().values(**values))


def test_finding_and_analysis_deletion_cascade_without_cross_analysis_loss(database):
    _, factory, repository = database
    analysis = new_analysis(repository)
    survivor = new_analysis(repository, OTHER_OWNER)
    ids, standalone = seed_graph(repository, analysis)
    seed_graph(repository, survivor)
    with transaction(factory) as session:
        session.execute(
            delete(Finding).where(
                Finding.analysis_id == analysis.id,
                Finding.id == ids[Finding],
            )
        )
    assert repository.get_record(OWNER, analysis.id, EvidenceRecord, ids[EvidenceRecord]) is None
    assert repository.get_record(OWNER, analysis.id, EvidenceRecord, standalone) is not None
    repository.delete_analysis(OWNER, analysis.id)
    with factory() as session:
        assert session.get(Analysis, analysis.id) is None
        for model in RECORD_TYPES:
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(
                        model.analysis_id == analysis.id,
                    )
                )
                == 0
            )
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(
                        model.analysis_id == survivor.id,
                    )
                )
                >= 1
            )


@pytest.mark.parametrize(
    "model,changes",
    [
        (Analysis, {"status": "verified"}),
        (Analysis, {"overall_score": 101}),
        (Analysis, {"risk_level": "safe"}),
        (Analysis, {"risk_level": "high_risk", "overall_score": None}),
        (Citation, {"verification_status": "passed"}),
        (Citation, {"verification_status": "partial"}),
        (ClaimAuthorityLink, {"support_status": "passed"}),
        (ClaimAuthorityLink, {"support_status": "interrupted"}),
        (Quote, {"match_status": "passed"}),
        (Quote, {"match_status": "partial"}),
        (Claim, {"confidence": 1.01}),
        (ClaimAuthorityLink, {"confidence": -0.01}),
        (Quote, {"similarity": 1.01}),
        (Finding, {"severity": "fatal"}),
        (Finding, {"status": "passed"}),
        (DocumentSegment, {"start_offset": -1, "end_offset": 1}),
        (DocumentSegment, {"start_offset": 10, "end_offset": 9}),
        (DocumentSegment, {"start_offset": None, "end_offset": 9}),
        (DocumentSegment, {"page_number": 0}),
        (EvidenceRecord, {"source_start_offset": 10, "source_end_offset": 1}),
    ],
)
def test_database_checks_reject_invalid_statuses_scores_confidence_and_locations(
    database,
    model,
    changes,
):
    _, factory, repository = database
    analysis = new_analysis(repository)
    ids, _ = seed_graph(repository, analysis)
    record_id = analysis.id if model is Analysis else ids[model]
    with pytest.raises(IntegrityError), transaction(factory) as session:
        session.execute(model.__table__.update().where(model.id == record_id).values(**changes))


def test_evidence_snapshot_is_immutable_but_can_be_attached_to_same_analysis_finding(database):
    _, factory, repository = database
    analysis = new_analysis(repository)
    ids, standalone = seed_graph(repository, analysis)
    with pytest.raises(ValueError, match="immutable"), transaction(factory) as session:
        session.get(EvidenceRecord, standalone).excerpt = "Altered source"
    with transaction(factory) as session:
        session.get(EvidenceRecord, standalone).finding_id = ids[Finding]
    stored = repository.get_record(OWNER, analysis.id, EvidenceRecord, standalone)
    assert stored.finding_id == ids[Finding]
    assert stored.excerpt == "A synthetic source passage."


@pytest.mark.parametrize(
    "field,value",
    [
        ("snapshot_text", "Replacement source"),
        ("source_sha256", "0" * 64),
        ("retrieved_at", datetime(2030, 1, 1, tzinfo=UTC)),
        ("source_start_offset", 1),
        ("source_metadata", {"rule_version": "changed"}),
        ("method_version", "changed"),
        ("model_version", "changed"),
        ("prompt_version", "changed"),
    ],
)
def test_evidence_provenance_fields_cannot_be_rewritten(database, field, value):
    _, factory, repository = database
    analysis = new_analysis(repository)
    ids, _ = seed_graph(repository, analysis)
    with pytest.raises(ValueError, match="immutable"), transaction(factory) as session:
        setattr(session.get(EvidenceRecord, ids[EvidenceRecord]), field, value)


def test_naive_timestamps_rejected_and_invalid_database_url_redacted(database, monkeypatch):
    _, factory, repository = database
    analysis = new_analysis(repository)
    with pytest.raises(StatementError, match="timezone-aware"), transaction(factory) as session:
        session.get(Analysis, analysis.id).expires_at = datetime(2030, 1, 1)
    monkeypatch.setenv("DATABASE_URL", "not-a-url-with-never-print-this")
    with pytest.raises(DatabaseConfigurationError) as error:
        get_database_url()
    assert "never-print-this" not in str(error.value)


def test_engine_creation_and_health_are_lazy_and_uncoupled(monkeypatch):
    import filingguard.db.session as db_session
    from filingguard.main import create_app

    monkeypatch.setenv("DATABASE_URL", "invalid-never-connect")

    def forbidden_engine(*args, **kwargs):
        pytest.fail("Application creation must not create a database engine")

    monkeypatch.setattr(db_session, "create_db_engine", forbidden_engine)
    with TestClient(create_app()) as client:
        assert client.get("/api/v1/health").json() == {"status": "ok"}
