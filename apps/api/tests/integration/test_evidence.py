import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from filingguard.db.models import Base, Finding
from filingguard.db.repository import AnalysisNotFound, AnalysisRepository
from filingguard.db.session import create_db_engine, create_session_factory
from filingguard.modules.evidence.schemas import EvidenceRecord
from filingguard.modules.evidence.service import finding_evidence, persist_evidence


def test_finding_resolves_to_immutable_validated_snapshot():
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    try:
        Base.metadata.create_all(engine)
        repository = AnalysisRepository(create_session_factory(engine))
        owner = hashlib.sha256(b"synthetic owner").hexdigest()
        source = "Synthetic \U0001f600 passage with a quote."
        analysis = repository.create_analysis(
            owner,
            document_name="Fixture",
            document_sha256=hashlib.sha256(source.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        finding_id = uuid4()
        evidence = EvidenceRecord(
            id=uuid4(),
            analysis_id=analysis.id,
            finding_id=finding_id,
            source_type="document",
            source_label="Synthetic filing",
            retrieved_at=datetime.now(UTC),
            snapshot_sha256=hashlib.sha256(source.encode()).hexdigest(),
            excerpt=source,
            start=0,
            end=len(source),
            method_version="extract-v1",
            provenance="synthetic",
        )
        with repository.stage_update(owner, analysis.id, "document", "completed") as writer:
            writer.add(
                Finding(
                    id=finding_id,
                    type="quote",
                    severity="high",
                    title="Review quote",
                    description="Synthetic warning",
                )
            )
            persist_evidence(writer, evidence, source)
        records = finding_evidence(repository, owner, analysis.id, finding_id)
        assert len(records) == 1
        assert records[0].excerpt == source
        assert records[0].source_metadata["offset_unit"] == "unicode_code_points"
        with pytest.raises(AnalysisNotFound):
            finding_evidence(repository, "f" * 64, analysis.id, finding_id)
        with pytest.raises(ValueError, match="hash"):
            with repository.stage_update(owner, analysis.id, "document", "completed") as writer:
                persist_evidence(writer, evidence, source + " changed")
        assert len(finding_evidence(repository, owner, analysis.id, finding_id)) == 1
    finally:
        engine.dispose()
