"""Small owner/analysis-scoped operations; each stage commits independently."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from filingguard.db.models import (
    Analysis,
    AnonymousSession,
    Authority,
    Citation,
    Claim,
    ClaimAuthorityLink,
    DocumentSegment,
    EvidenceRecord,
    Finding,
    Quote,
)
from filingguard.db.models.entities import ANALYSIS_STATUSES, AnalysisOwned
from filingguard.db.session import transaction
from filingguard.modules.analyses.schemas import Coverage, StageName, StageState

RECORD_TYPES = (
    DocumentSegment,
    Authority,
    Citation,
    Claim,
    ClaimAuthorityLink,
    Quote,
    Finding,
    EvidenceRecord,
)


class AnalysisNotFound(LookupError):
    """Missing analysis and wrong owner are deliberately indistinguishable."""


class AnalysisNotReady(ValueError):
    """A prepared analysis cannot be queued again without an explicit rerun."""


def _owned_analysis(
    session: Session,
    owner_hash: str,
    analysis_id: UUID,
    *,
    lock: bool = False,
) -> Analysis:
    query = select(Analysis).where(
        Analysis.id == analysis_id,
        Analysis.owner_hash == owner_hash,
        Analysis.expires_at > datetime.now(UTC),
    )
    if lock:
        query = query.with_for_update()
    analysis = session.scalar(query)
    if analysis is None:
        raise AnalysisNotFound("Analysis not found")
    return analysis


class StageWrite:
    """Append stage output to one analysis; flush in parent-before-child order."""

    def __init__(self, session: Session, analysis: Analysis):
        self._session = session
        self.analysis = analysis
        self._records: list[AnalysisOwned] = []

    def add(self, *records: AnalysisOwned) -> None:
        for record in records:
            if type(record) not in RECORD_TYPES:
                raise TypeError("Only analysis-owned persistence records can be added")
            if record.analysis_id not in {None, self.analysis.id}:
                raise ValueError("Record belongs to a different analysis")
            record.analysis_id = self.analysis.id
            if record.id is None:
                record.id = uuid4()
            self._records.append(record)

    def _flush(self) -> None:
        for model in RECORD_TYPES:
            records = [record for record in self._records if type(record) is model]
            if records:
                self._session.add_all(records)
                self._session.flush()

    def update_propositions(self, *records: ClaimAuthorityLink) -> None:
        for record in records:
            if type(record) is not ClaimAuthorityLink or record.analysis_id != self.analysis.id:
                raise ValueError("Only owned proposition links may be updated")
            stored = self._session.scalar(
                select(ClaimAuthorityLink).where(
                    ClaimAuthorityLink.analysis_id == self.analysis.id,
                    ClaimAuthorityLink.id == record.id,
                )
            )
            if stored is None or any(
                getattr(stored, k) != getattr(record, k)
                for k in ("claim_id", "citation_id", "authority_id")
            ):
                raise ValueError("Proposition link identity mismatch")
            stored.support_status = record.support_status
            stored.confidence = record.confidence
            stored.explanation = record.explanation


class AnalysisRepository:
    def __init__(self, factory: sessionmaker[Session]):
        self._factory = factory

    def issue_session(self, owner_hash: str, expires_at: datetime) -> None:
        with transaction(self._factory) as session:
            session.execute(
                delete(AnonymousSession).where(AnonymousSession.expires_at <= datetime.now(UTC))
            )
            if session.scalar(select(func.count()).select_from(AnonymousSession)) >= 256:
                raise OverflowError("Session capacity reached")
            session.add(AnonymousSession(owner_hash=owner_hash, expires_at=expires_at))

    def session_expiry(self, owner_hash: str) -> datetime:
        with self._factory() as session:
            expiry = session.scalar(
                select(AnonymousSession.expires_at).where(
                    AnonymousSession.owner_hash == owner_hash,
                    AnonymousSession.expires_at > datetime.now(UTC),
                )
            )
            if expiry is None:
                raise AnalysisNotFound("Session unavailable")
            return expiry

    def prune_sessions(self) -> None:
        with transaction(self._factory) as session:
            session.execute(
                delete(AnonymousSession).where(AnonymousSession.expires_at <= datetime.now(UTC))
            )

    def list_analyses(self, owner_hash: str) -> list[Analysis]:
        with self._factory() as session:
            return list(
                session.scalars(
                    select(Analysis)
                    .where(
                        Analysis.owner_hash == owner_hash, Analysis.expires_at > datetime.now(UTC)
                    )
                    .order_by(Analysis.created_at.desc())
                    .limit(20)
                )
            )

    def create_analysis(
        self,
        owner_hash: str,
        *,
        document_name: str,
        document_sha256: str,
        expires_at: datetime,
        mode: str = "live",
        demo_fixture_id: str | None = None,
        court_profile_id: str | None = None,
        ai_used: bool | None = None,
        status: str = "not_run",
        stored_file_id: UUID | None = None,
    ) -> Analysis:
        if status not in ANALYSIS_STATUSES:
            raise ValueError("Invalid analysis status")
        if stored_file_id is not None and (
            not isinstance(stored_file_id, UUID) or stored_file_id.version != 4
        ):
            raise ValueError("Invalid private file reference")
        analysis = Analysis(
            owner_hash=owner_hash,
            document_name=document_name,
            document_sha256=document_sha256,
            expires_at=expires_at,
            mode=mode,
            demo_fixture_id=demo_fixture_id,
            court_profile_id=court_profile_id,
            ai_used=ai_used,
            status=status,
            stored_file_id=stored_file_id,
        )
        with transaction(self._factory) as session:
            session.add(analysis)
            session.flush()
        return analysis

    def get_analysis(self, owner_hash: str, analysis_id: UUID) -> Analysis:
        with self._factory() as session:
            return _owned_analysis(session, owner_hash, analysis_id)

    def queue_review(
        self, owner_hash: str, analysis_id: UUID, stages: tuple[StageName, ...]
    ) -> None:
        if not stages or len(stages) != len(set(stages)) or StageName.DOCUMENT in stages:
            raise ValueError("Review stages must be distinct legal stages")
        with transaction(self._factory) as session:
            analysis = _owned_analysis(session, owner_hash, analysis_id, lock=True)
            if (
                analysis.status != "not_run"
                or analysis.document_snapshot is None
                or analysis.stage_states.get("document", {}).get("status") != "completed"
            ):
                raise AnalysisNotReady("Analysis is not ready for a first review")
            analysis.stage_states = {
                **analysis.stage_states,
                **{
                    stage.value: StageState(name=stage, status="queued").model_dump(mode="json")
                    for stage in stages
                },
            }
            analysis.status = "queued"

    def clone_for_rerun(self, owner_hash: str, analysis_id: UUID) -> UUID:
        """Create a fresh prepared attempt; previous results remain immutable."""
        with transaction(self._factory) as session:
            source = _owned_analysis(session, owner_hash, analysis_id, lock=True)
            if (
                source.mode != "live"
                or source.status not in {"completed", "partial", "failed", "interrupted"}
                or source.document_snapshot is None
            ):
                raise AnalysisNotReady("Only a terminal live review can be rerun")
            if (
                session.scalar(
                    select(func.count())
                    .select_from(Analysis)
                    .where(
                        Analysis.owner_hash == owner_hash, Analysis.expires_at > datetime.now(UTC)
                    )
                )
                >= 5
            ):
                raise OverflowError("Session document limit reached")
            clone = Analysis(
                id=uuid4(),
                owner_hash=owner_hash,
                expires_at=source.expires_at,
                document_name=source.document_name,
                document_sha256=source.document_sha256,
                document_snapshot=source.document_snapshot,
                mode="live",
                court_profile_id=source.court_profile_id,
                ai_used=source.ai_used,
                status="not_run",
                stage_states={"document": source.stage_states["document"]},
            )
            session.add(clone)
            session.flush()
            for segment in session.scalars(
                select(DocumentSegment).where(DocumentSegment.analysis_id == source.id)
            ):
                session.add(
                    DocumentSegment(
                        analysis_id=clone.id,
                        paragraph_index=segment.paragraph_index,
                        page_number=segment.page_number,
                        start_offset=segment.start_offset,
                        end_offset=segment.end_offset,
                        text=segment.text,
                    )
                )
            return clone.id

    def fail_review(
        self,
        owner_hash: str,
        analysis_id: UUID,
        failed_stage: StageName,
        remaining_stages: tuple[StageName, ...],
        *,
        partial: bool,
    ) -> None:
        with transaction(self._factory) as session:
            analysis = _owned_analysis(session, owner_hash, analysis_id, lock=True)
            analysis.stage_states = {
                **analysis.stage_states,
                failed_stage.value: StageState(
                    name=failed_stage, status="failed", reason="Review stage failed"
                ).model_dump(mode="json"),
                **{
                    stage.value: StageState(
                        name=stage,
                        status="interrupted",
                        reason="Review stopped after a prior stage failed",
                    ).model_dump(mode="json")
                    for stage in remaining_stages
                },
            }
            analysis.status = "partial" if partial else "failed"

    def get_record[Record: AnalysisOwned](
        self,
        owner_hash: str,
        analysis_id: UUID,
        model: type[Record],
        record_id: UUID,
    ) -> Record | None:
        self._check_model(model)
        with self._factory() as session:
            _owned_analysis(session, owner_hash, analysis_id)
            return session.scalar(
                select(model).where(
                    model.analysis_id == analysis_id,
                    model.id == record_id,
                )
            )

    def list_records[Record: AnalysisOwned](
        self,
        owner_hash: str,
        analysis_id: UUID,
        model: type[Record],
    ) -> list[Record]:
        self._check_model(model)
        with self._factory() as session:
            _owned_analysis(session, owner_hash, analysis_id)
            return list(session.scalars(select(model).where(model.analysis_id == analysis_id)))

    def list_citations(self, owner_hash: str, analysis_id: UUID) -> list[Citation]:
        with self._factory() as session:
            _owned_analysis(session, owner_hash, analysis_id)
            return list(
                session.scalars(
                    select(Citation)
                    .where(Citation.analysis_id == analysis_id)
                    .order_by(Citation.start_offset, Citation.end_offset, Citation.id)
                    .limit(200)
                )
            )

    @contextmanager
    def stage_update(
        self,
        owner_hash: str,
        analysis_id: UUID,
        stage: str,
        status: str,
        *,
        analysis_status: str | None = None,
        reason: str | None = None,
        coverage: Coverage | dict | None = None,
        applicable: bool = True,
    ) -> Iterator[StageWrite]:
        state = StageState(
            name=stage,
            status=status,
            reason=reason,
            coverage=coverage if coverage is not None else Coverage(),
            applicable=applicable,
        )
        if analysis_status is not None and analysis_status not in ANALYSIS_STATUSES:
            raise ValueError("Invalid analysis status")
        with transaction(self._factory) as session:
            analysis = _owned_analysis(session, owner_hash, analysis_id, lock=True)
            writer = StageWrite(session, analysis)
            yield writer
            writer._flush()
            analysis.stage_states = {
                **analysis.stage_states,
                state.name.value: state.model_dump(mode="json"),
            }
            if analysis_status is not None:
                analysis.status = analysis_status

    def delete_analysis(
        self,
        owner_hash: str,
        analysis_id: UUID,
        *,
        delete_file: Callable[[str], bool] | None = None,
    ) -> None:
        with transaction(self._factory) as session:
            analysis = _owned_analysis(session, owner_hash, analysis_id, lock=True)
            if analysis.status in {"queued", "running"}:
                raise AnalysisNotReady("An active review cannot be deleted")
            self._delete_file(analysis, delete_file)
            session.execute(
                delete(Analysis).where(
                    Analysis.id == analysis_id,
                    Analysis.owner_hash == owner_hash,
                )
            )

    @staticmethod
    def _delete_file(analysis: Analysis, delete_file: Callable[[str], bool] | None) -> None:
        if analysis.stored_file_id is not None:
            if delete_file is None:
                raise ValueError("Private file cleanup is required")
            delete_file(str(analysis.stored_file_id))

    def expired_ids(self, now: datetime, *, limit: int = 100) -> list[UUID]:
        if now.utcoffset() is None or type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Invalid cleanup boundary")
        with self._factory() as session:
            return list(
                session.scalars(
                    select(Analysis.id)
                    .where(Analysis.expires_at <= now)
                    .order_by(Analysis.expires_at, Analysis.id)
                    .limit(limit)
                )
            )

    def delete_expired(
        self, analysis_id: UUID, now: datetime, *, delete_file: Callable[[str], bool]
    ) -> bool:
        if now.utcoffset() is None:
            raise ValueError("Cleanup time must be timezone-aware")
        with transaction(self._factory) as session:
            analysis = session.scalar(
                select(Analysis)
                .where(Analysis.id == analysis_id, Analysis.expires_at <= now)
                .with_for_update()
            )
            if analysis is None:
                return False
            self._delete_file(analysis, delete_file)
            session.execute(delete(Analysis).where(Analysis.id == analysis_id))
            return True

    def interrupt_pending(self) -> int:
        with transaction(self._factory) as session:
            analyses = list(
                session.scalars(
                    select(Analysis)
                    .where(Analysis.status.in_(["queued", "running"]))
                    .with_for_update()
                )
            )
            for analysis in analyses:
                analysis.status = "interrupted"
                analysis.overall_score = None
                analysis.risk_level = None
                states = dict(analysis.stage_states)
                for name, state in states.items():
                    if state.get("status") in {"queued", "running"}:
                        states[name] = {
                            **state,
                            "status": "interrupted",
                            "reason": "Previous process stopped before the stage completed",
                        }
                analysis.stage_states = states
            return len(analyses)

    @staticmethod
    def _check_model(model: type[AnalysisOwned]) -> None:
        if model not in RECORD_TYPES:
            raise TypeError("Unsupported persistence record type")
