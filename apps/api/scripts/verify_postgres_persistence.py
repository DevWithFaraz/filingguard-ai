"""Opt-in migration/round-trip check in a fresh disposable Neon schema only."""

import argparse
import hashlib
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import func, inspect, select, text
from sqlalchemy.schema import CreateSchema, DropSchema

from filingguard.db.models import (
    Authority,
    Base,
    Citation,
    Claim,
    ClaimAuthorityLink,
    DocumentSegment,
    Finding,
    Quote,
)
from filingguard.db.repository import AnalysisRepository
from filingguard.db.session import create_db_engine, create_session_factory, get_database_url
from filingguard.modules.evidence.schemas import EvidenceRecord
from filingguard.modules.evidence.service import finding_evidence, persist_evidence


def verify() -> None:
    url = get_database_url()
    if url.drivername != "postgresql+psycopg" or not (url.host or "").endswith(".neon.tech"):
        raise ValueError("Expected a Neon psycopg connection")
    if url.query.get("sslmode") not in {"require", "verify-ca", "verify-full"}:
        raise ValueError("TLS is required")
    schema = "fg_verify_" + uuid4().hex
    if not re.fullmatch(r"fg_verify_[a-f0-9]{32}", schema):
        raise ValueError("Unsafe verification schema")
    admin = create_db_engine(url)
    engine = None
    created = False
    try:
        with admin.begin() as connection:
            connection.execute(CreateSchema(schema))
            created = True
        # Search path contains only our freshly-created schema, never public/user tables.
        engine = create_db_engine(url.update_query_dict({"options": f"-c search_path={schema}"}))
        with engine.begin() as connection:
            if connection.scalar(text("SELECT current_schema()")) != schema:
                raise ValueError("Verification connection is not isolated")
            config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            if not set(Base.metadata.tables) <= set(inspect(connection).get_table_names()):
                raise ValueError("Migration tables missing")
        repository = AnalysisRepository(create_session_factory(engine))
        owner = hashlib.sha256(uuid4().bytes).hexdigest()
        source = "Synthetic PostgreSQL verification passage."
        analysis = repository.create_analysis(
            owner,
            document_name="Synthetic verification",
            court_profile_id="synthetic-demo-v1",
            ai_used=False,
            document_sha256=hashlib.sha256(source.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
        segment_id, authority_id, citation_id, claim_id, quote_id, finding_id = [
            uuid4() for _ in range(6)
        ]
        with repository.stage_update(owner, analysis.id, "document", "completed") as writer:
            writer.add(
                DocumentSegment(id=segment_id, paragraph_index=0, text=source),
                Authority(id=authority_id, source="synthetic", external_id="verification-only"),
                Citation(
                    id=citation_id,
                    raw_text="1 Synthetic 1",
                    segment_id=segment_id,
                    authority_id=authority_id,
                ),
                Claim(
                    id=claim_id,
                    text="Synthetic claim",
                    segment_id=segment_id,
                    extraction_method="heuristic",
                ),
                ClaimAuthorityLink(
                    claim_id=claim_id, citation_id=citation_id, authority_id=authority_id
                ),
                Quote(
                    id=quote_id,
                    quote_text="Synthetic quote",
                    segment_id=segment_id,
                    citation_id=citation_id,
                ),
                Finding(
                    id=finding_id,
                    type="system",
                    severity="info",
                    title="Test only",
                    description="Synthetic migration verification",
                    segment_id=segment_id,
                ),
            )
            persist_evidence(
                writer,
                EvidenceRecord(
                    id=uuid4(),
                    analysis_id=analysis.id,
                    finding_id=finding_id,
                    source_type="document",
                    source_label="Synthetic test source",
                    retrieved_at=datetime.now(UTC),
                    snapshot_sha256=hashlib.sha256(source.encode()).hexdigest(),
                    excerpt=source,
                    start=0,
                    end=len(source),
                    method_version="test-v1",
                    provenance="synthetic",
                ),
                source,
            )
        if len(finding_evidence(repository, owner, analysis.id, finding_id)) != 1:
            raise ValueError("Evidence round trip failed")
        repository.delete_analysis(owner, analysis.id)
        with engine.connect() as connection:
            for table in Base.metadata.sorted_tables:
                if connection.scalar(select(func.count()).select_from(table)) != 0:
                    raise ValueError("Cascade deletion failed")
        print("PostgreSQL migration, nine-entity round trip, evidence and cascade checks passed")
    finally:
        if engine is not None:
            engine.dispose()
        try:
            if created:
                with admin.begin() as connection:
                    connection.execute(DropSchema(schema, cascade=True))
                print("Disposable verification schema removed")
        finally:
            admin.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-isolated-write", action="store_true", required=True)
    parser.parse_args()
    try:
        verify()
        return 0
    except Exception as error:
        # Do not print a driver exception, SQL parameters or credential-bearing URL.
        print(f"Persistence verification failed ({type(error).__name__}); no details logged")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
