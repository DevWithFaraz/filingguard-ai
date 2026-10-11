"""Portable relational identities, ownership boundaries and evidence provenance."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    event,
    false,
    func,
    inspect,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column, relationship

from filingguard.db.session import UTCDateTime
from filingguard.modules.analyses.schemas import (
    AnalysisMode,
    AnalysisStatus,
    CitationStatus,
    FindingType,
    PropositionStatus,
    QuoteStatus,
    ReviewStatus,
    RiskLevel,
    Severity,
    StageStatus,
)

ANALYSIS_STATUSES = tuple(status.value for status in AnalysisStatus)
STAGE_STATUSES = tuple(status.value for status in StageStatus)
JSON_VALUE = JSON().with_variant(JSONB(), "postgresql")


def status_check(column: str, values: tuple[str, ...]) -> CheckConstraint:
    allowed = ", ".join(f"'{value}'" for value in values)
    return CheckConstraint(f"{column} IN ({allowed})", name=f"{column}_valid")


def offsets_check(start: str = "start_offset", end: str = "end_offset") -> CheckConstraint:
    return CheckConstraint(
        f"({start} IS NULL AND {end} IS NULL) OR "
        f"({start} IS NOT NULL AND {end} IS NOT NULL AND {start} >= 0 AND {end} >= {start})",
        name=f"{start}_valid",
    )


def confidence_check(column: str = "confidence") -> CheckConstraint:
    return CheckConstraint(f"{column} >= 0 AND {column} <= 1", name=f"{column}_valid")


def scoped_fk(column: str, table: str) -> ForeignKeyConstraint:
    return ForeignKeyConstraint(
        ["analysis_id", column],
        [f"{table}.analysis_id", f"{table}.id"],
        ondelete="CASCADE",
    )


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class AnalysisOwned:
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("analyses.id", ondelete="CASCADE"),
        index=True,
    )

    @declared_attr.directive
    def __table_args__(cls):
        return (UniqueConstraint("analysis_id", "id"),)


class AnonymousSession(Base):
    __tablename__ = "anonymous_sessions"
    __table_args__ = (CheckConstraint("length(owner_hash) = 64", name="owner_hash_valid"),)
    owner_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)


class DocumentLocation:
    page_number: Mapped[int | None] = mapped_column(Integer)
    start_offset: Mapped[int | None] = mapped_column(Integer)
    end_offset: Mapped[int | None] = mapped_column(Integer)


class Analysis(Base):
    __tablename__ = "analyses"
    __table_args__ = (
        status_check("status", ANALYSIS_STATUSES),
        status_check("mode", tuple(mode.value for mode in AnalysisMode)),
        status_check("risk_level", tuple(level.value for level in RiskLevel)),
        CheckConstraint("overall_score >= 0 AND overall_score <= 100", name="score_valid"),
        CheckConstraint(
            "risk_level IS NULL OR overall_score IS NOT NULL", name="risk_requires_score"
        ),
        CheckConstraint("length(owner_hash) = 64", name="owner_hash_valid"),
        CheckConstraint("length(document_sha256) = 64", name="document_hash_valid"),
        CheckConstraint("expires_at > created_at", name="expiry_valid"),
        CheckConstraint(
            "(mode = 'live' AND demo_fixture_id IS NULL) OR "
            "(mode = 'demo' AND demo_fixture_id IS NOT NULL AND length(demo_fixture_id) > 0)",
            name="demo_identity_valid",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    document_name: Mapped[str] = mapped_column(String(255))
    document_sha256: Mapped[str] = mapped_column(String(64))
    stored_file_id: Mapped[UUID | None] = mapped_column(Uuid, unique=True, index=True)
    document_snapshot: Mapped[dict | None] = mapped_column(JSON_VALUE)
    mode: Mapped[str] = mapped_column(String(20), default="live", server_default="live")
    demo_fixture_id: Mapped[str | None] = mapped_column(String(255))
    court_profile_id: Mapped[str | None] = mapped_column(String(255))
    ai_used: Mapped[bool | None] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String(32), default="not_run", server_default="not_run")
    stage_states: Mapped[dict] = mapped_column(JSON_VALUE, default=dict, server_default="{}")
    overall_score: Mapped[int | None] = mapped_column(Integer)
    risk_level: Mapped[str | None] = mapped_column(String(32))

    segments: Mapped[list["DocumentSegment"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    authorities: Mapped[list["Authority"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    citations: Mapped[list["Citation"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="Citation.analysis_id",
    )
    claims: Mapped[list["Claim"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="Claim.analysis_id",
    )
    claim_authority_links: Mapped[list["ClaimAuthorityLink"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="ClaimAuthorityLink.analysis_id",
    )
    quotes: Mapped[list["Quote"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="Quote.analysis_id",
    )
    findings: Mapped[list["Finding"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="Finding.analysis_id",
    )
    evidence_records: Mapped[list["EvidenceRecord"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="EvidenceRecord.analysis_id",
    )


class DocumentSegment(AnalysisOwned, DocumentLocation, Base):
    __tablename__ = "document_segments"
    __table_args__ = (
        UniqueConstraint("analysis_id", "id"),
        UniqueConstraint("analysis_id", "paragraph_index"),
        offsets_check(),
        CheckConstraint("page_number >= 1", name="page_number_valid"),
        CheckConstraint("paragraph_index >= 0", name="paragraph_index_valid"),
    )

    paragraph_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)


class Authority(AnalysisOwned, Base):
    __tablename__ = "authorities"
    __table_args__ = (
        UniqueConstraint("analysis_id", "id"),
        UniqueConstraint("analysis_id", "source", "external_id"),
        CheckConstraint("length(source_sha256) = 64", name="source_hash_valid"),
    )

    source: Mapped[str] = mapped_column(String(80))
    external_id: Mapped[str | None] = mapped_column(String(255))
    case_name: Mapped[str | None] = mapped_column(Text)
    citation: Mapped[str | None] = mapped_column(String(255))
    court: Mapped[str | None] = mapped_column(String(255))
    year: Mapped[int | None] = mapped_column(Integer)
    source_url: Mapped[str | None] = mapped_column(Text)
    opinion_text_available: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
    )
    opinion_text: Mapped[str | None] = mapped_column(Text)
    source_sha256: Mapped[str | None] = mapped_column(String(64))
    retrieved_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    source_metadata: Mapped[dict] = mapped_column(JSON_VALUE, default=dict, server_default="{}")


class Citation(AnalysisOwned, DocumentLocation, Base):
    __tablename__ = "citations"
    __table_args__ = (
        UniqueConstraint("analysis_id", "id"),
        scoped_fk("segment_id", "document_segments"),
        scoped_fk("authority_id", "authorities"),
        offsets_check(),
        CheckConstraint("page_number >= 1", name="page_number_valid"),
        status_check("verification_status", tuple(status.value for status in CitationStatus)),
    )

    raw_text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str | None] = mapped_column(Text)
    extraction_metadata: Mapped[dict] = mapped_column(
        JSON_VALUE, default=dict, server_default="{}"
    )
    segment_id: Mapped[UUID] = mapped_column(Uuid)
    authority_id: Mapped[UUID | None] = mapped_column(Uuid)
    segment: Mapped["DocumentSegment"] = relationship(foreign_keys=[segment_id])
    authority: Mapped["Authority | None"] = relationship(foreign_keys=[authority_id])
    verification_status: Mapped[str] = mapped_column(
        String(32),
        default="not_run",
        server_default="not_run",
    )


class Claim(AnalysisOwned, DocumentLocation, Base):
    __tablename__ = "claims"
    __table_args__ = (
        UniqueConstraint("analysis_id", "id"),
        scoped_fk("segment_id", "document_segments"),
        offsets_check(),
        confidence_check(),
        CheckConstraint("page_number >= 1", name="page_number_valid"),
        status_check("extraction_method", ("heuristic", "ai")),
    )

    text: Mapped[str] = mapped_column(Text)
    segment_id: Mapped[UUID] = mapped_column(Uuid)
    segment: Mapped["DocumentSegment"] = relationship(foreign_keys=[segment_id])
    extraction_method: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float | None] = mapped_column(Float)
    model_version: Mapped[str | None] = mapped_column(String(255))
    prompt_version: Mapped[str | None] = mapped_column(String(255))


class ClaimAuthorityLink(AnalysisOwned, Base):
    __tablename__ = "claim_authority_links"
    __table_args__ = (
        UniqueConstraint("analysis_id", "id"),
        UniqueConstraint("analysis_id", "claim_id", "citation_id", "authority_id"),
        scoped_fk("claim_id", "claims"),
        scoped_fk("citation_id", "citations"),
        scoped_fk("authority_id", "authorities"),
        confidence_check(),
        status_check("support_status", tuple(status.value for status in PropositionStatus)),
    )

    claim_id: Mapped[UUID] = mapped_column(Uuid)
    citation_id: Mapped[UUID] = mapped_column(Uuid)
    authority_id: Mapped[UUID | None] = mapped_column(Uuid)
    claim: Mapped["Claim"] = relationship(foreign_keys=[claim_id])
    citation: Mapped["Citation"] = relationship(foreign_keys=[citation_id])
    authority: Mapped["Authority | None"] = relationship(foreign_keys=[authority_id])
    support_status: Mapped[str] = mapped_column(
        String(32),
        default="not_run",
        server_default="not_run",
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    explanation: Mapped[str | None] = mapped_column(Text)


class Quote(AnalysisOwned, DocumentLocation, Base):
    __tablename__ = "quotes"
    __table_args__ = (
        UniqueConstraint("analysis_id", "id"),
        scoped_fk("segment_id", "document_segments"),
        scoped_fk("citation_id", "citations"),
        offsets_check(),
        confidence_check("similarity"),
        CheckConstraint("page_number >= 1", name="page_number_valid"),
        status_check("match_status", tuple(status.value for status in QuoteStatus)),
    )

    quote_text: Mapped[str] = mapped_column(Text)
    segment_id: Mapped[UUID] = mapped_column(Uuid)
    citation_id: Mapped[UUID | None] = mapped_column(Uuid)
    segment: Mapped["DocumentSegment"] = relationship(foreign_keys=[segment_id])
    citation: Mapped["Citation | None"] = relationship(foreign_keys=[citation_id])
    match_status: Mapped[str] = mapped_column(
        String(32), default="not_run", server_default="not_run"
    )
    similarity: Mapped[float | None] = mapped_column(Float)
    closest_passage: Mapped[str | None] = mapped_column(Text)


class Finding(AnalysisOwned, DocumentLocation, Base):
    __tablename__ = "findings"
    __table_args__ = (
        UniqueConstraint("analysis_id", "id"),
        scoped_fk("segment_id", "document_segments"),
        scoped_fk("citation_id", "citations"),
        scoped_fk("authority_id", "authorities"),
        scoped_fk("claim_id", "claims"),
        scoped_fk("quote_id", "quotes"),
        offsets_check(),
        confidence_check(),
        CheckConstraint("page_number >= 1", name="page_number_valid"),
        status_check("type", tuple(kind.value for kind in FindingType)),
        status_check("severity", tuple(level.value for level in Severity)),
        status_check("status", tuple(status.value for status in ReviewStatus)),
    )

    type: Mapped[str] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="open", server_default="open")
    stage: Mapped[str | None] = mapped_column(String(80))
    segment_id: Mapped[UUID | None] = mapped_column(Uuid)
    citation_id: Mapped[UUID | None] = mapped_column(Uuid)
    authority_id: Mapped[UUID | None] = mapped_column(Uuid)
    claim_id: Mapped[UUID | None] = mapped_column(Uuid)
    quote_id: Mapped[UUID | None] = mapped_column(Uuid)
    rule_id: Mapped[str | None] = mapped_column(String(255))
    document_excerpt: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    ai_assisted: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    segment: Mapped["DocumentSegment | None"] = relationship(foreign_keys=[segment_id])
    citation: Mapped["Citation | None"] = relationship(foreign_keys=[citation_id])
    authority: Mapped["Authority | None"] = relationship(foreign_keys=[authority_id])
    claim: Mapped["Claim | None"] = relationship(foreign_keys=[claim_id])
    quote: Mapped["Quote | None"] = relationship(foreign_keys=[quote_id])
    evidence_records: Mapped[list["EvidenceRecord"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="EvidenceRecord.finding_id",
        back_populates="finding",
    )


class EvidenceRecord(AnalysisOwned, DocumentLocation, Base):
    __tablename__ = "evidence_records"
    __table_args__ = (
        UniqueConstraint("analysis_id", "id"),
        scoped_fk("finding_id", "findings"),
        scoped_fk("segment_id", "document_segments"),
        scoped_fk("citation_id", "citations"),
        scoped_fk("authority_id", "authorities"),
        scoped_fk("claim_id", "claims"),
        scoped_fk("quote_id", "quotes"),
        offsets_check(),
        offsets_check("source_start_offset", "source_end_offset"),
        CheckConstraint("page_number >= 1", name="page_number_valid"),
        CheckConstraint("length(source_sha256) = 64", name="source_hash_valid"),
        status_check("source_type", ("document", "api", "opinion_text", "ai_analysis", "rule")),
    )

    finding_id: Mapped[UUID | None] = mapped_column(Uuid, index=True)
    segment_id: Mapped[UUID | None] = mapped_column(Uuid)
    citation_id: Mapped[UUID | None] = mapped_column(Uuid)
    authority_id: Mapped[UUID | None] = mapped_column(Uuid)
    claim_id: Mapped[UUID | None] = mapped_column(Uuid)
    quote_id: Mapped[UUID | None] = mapped_column(Uuid)
    source_type: Mapped[str] = mapped_column(String(32))
    source_label: Mapped[str] = mapped_column(String(255))
    excerpt: Mapped[str] = mapped_column(Text)
    snapshot_text: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    source_sha256: Mapped[str | None] = mapped_column(String(64))
    retrieved_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    source_start_offset: Mapped[int | None] = mapped_column(Integer)
    source_end_offset: Mapped[int | None] = mapped_column(Integer)
    method: Mapped[str] = mapped_column(String(80))
    method_version: Mapped[str] = mapped_column(String(255))
    model_version: Mapped[str | None] = mapped_column(String(255))
    prompt_version: Mapped[str | None] = mapped_column(String(255))
    source_metadata: Mapped[dict] = mapped_column(JSON_VALUE, default=dict, server_default="{}")
    finding: Mapped["Finding | None"] = relationship(
        foreign_keys=[finding_id],
        back_populates="evidence_records",
    )
    segment: Mapped["DocumentSegment | None"] = relationship(foreign_keys=[segment_id])
    citation: Mapped["Citation | None"] = relationship(foreign_keys=[citation_id])
    authority: Mapped["Authority | None"] = relationship(foreign_keys=[authority_id])
    claim: Mapped["Claim | None"] = relationship(foreign_keys=[claim_id])
    quote: Mapped["Quote | None"] = relationship(foreign_keys=[quote_id])


@event.listens_for(EvidenceRecord, "before_update")
def preserve_evidence_snapshot(mapper, connection, target):
    # A new retrieval/method creates a new record; attaching a finding is allowed later.
    state = inspect(target)
    immutable = set(state.mapper.column_attrs.keys()) - {"finding_id"}
    if any(state.attrs[name].history.has_changes() for name in immutable):
        raise ValueError("Evidence provenance is immutable; append a new evidence record")
