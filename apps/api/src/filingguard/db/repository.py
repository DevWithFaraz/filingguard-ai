"""Small owner/analysis-scoped operations; each stage commits independently."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
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
    IdentitySession,
    LocalIdentity,
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

    def resolve_session(self, token_hash: str) -> tuple[str, datetime]:
        """Map bearer SHA-256 to owner_hash. Identity sessions store a different hash."""
        with self._factory() as session:
            now = datetime.now(UTC)
            anonymous = session.scalar(
                select(AnonymousSession).where(
                    AnonymousSession.owner_hash == token_hash,
                    AnonymousSession.expires_at > now,
                )
            )
            if anonymous is not None:
                return anonymous.owner_hash, anonymous.expires_at
            identity = session.scalar(
                select(IdentitySession).where(
                    IdentitySession.token_hash == token_hash,
                    IdentitySession.expires_at > now,
                )
            )
            if identity is not None:
                return identity.owner_hash, identity.expires_at
            raise AnalysisNotFound("Session unavailable")

    def get_local_identity_by_owner(self, owner_hash: str) -> LocalIdentity | None:
        with self._factory() as session:
            return session.scalar(
                select(LocalIdentity).where(LocalIdentity.owner_hash == owner_hash)
            )

    def get_local_identity_by_username(self, username: str) -> LocalIdentity | None:
        with self._factory() as session:
            return session.scalar(select(LocalIdentity).where(LocalIdentity.username == username))

    def add_local_identity(self, owner_hash: str, username: str, secret_hash: str) -> LocalIdentity:
        with transaction(self._factory) as session:
            if session.scalar(select(LocalIdentity).where(LocalIdentity.owner_hash == owner_hash)):
                raise ValueError("owner_claimed")
            if session.scalar(select(LocalIdentity).where(LocalIdentity.username == username)):
                raise ValueError("username_taken")
            row = LocalIdentity(owner_hash=owner_hash, username=username, secret_hash=secret_hash)
            session.add(row)
            session.flush()
            return row

    def issue_identity_session(
        self, token_hash: str, owner_hash: str, expires_at: datetime
    ) -> None:
        with transaction(self._factory) as session:
            session.execute(
                delete(IdentitySession).where(IdentitySession.expires_at <= datetime.now(UTC))
            )
            if session.scalar(select(func.count()).select_from(IdentitySession)) >= 256:
                raise OverflowError("Session capacity reached")
            session.add(
                IdentitySession(token_hash=token_hash, owner_hash=owner_hash, expires_at=expires_at)
            )

    def prune_sessions(self) -> None:
        with transaction(self._factory) as session:
            session.execute(
                delete(AnonymousSession).where(AnonymousSession.expires_at <= datetime.now(UTC))
            )
            session.execute(
                delete(IdentitySession).where(IdentitySession.expires_at <= datetime.now(UTC))
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

    def save_claim_correction(
        self,
        owner_hash: str,
        analysis_id: UUID,
        claim_id: UUID,
        corrected_text: str,
    ) -> tuple[str, list[dict], list[UUID]]:
        """Append correction history; never rewrite original Claim.text."""
        from filingguard.modules.claim_corrections.schemas import MAX_HISTORY
        from filingguard.modules.claim_corrections.text import history_entries

        stale = (
            "Proposition support is stale after a user correction of the extracted claim. "
            "In-place proposition re-run is not available. POST /analyses/{id}/rerun clones "
            "a new analysis and re-extracts claims without this correction. "
            "Review flag, not a legal determination."
        )
        with transaction(self._factory) as session:
            analysis = _owned_analysis(session, owner_hash, analysis_id, lock=True)
            if analysis.status in {"queued", "running"}:
                raise AnalysisNotReady("An active review cannot be corrected")
            claim = session.scalar(
                select(Claim).where(Claim.analysis_id == analysis_id, Claim.id == claim_id)
            )
            if claim is None:
                raise LookupError("Claim not found")
            if claim.text == corrected_text and not history_entries(claim):
                raise ValueError("Invalid claim correction")
            history = history_entries(claim)
            if history and history[-1].get("corrected_text") == corrected_text:
                raise ValueError("Invalid claim correction")
            entry = {
                "id": str(uuid4()),
                "corrected_text": corrected_text,
                "created_at": datetime.now(UTC).isoformat(),
            }
            history = [*history, entry][-MAX_HISTORY:]
            claim.correction_history = history
            link_ids = []
            for link in session.scalars(
                select(ClaimAuthorityLink).where(
                    ClaimAuthorityLink.analysis_id == analysis_id,
                    ClaimAuthorityLink.claim_id == claim_id,
                )
            ):
                link.support_status = "not_run"
                link.confidence = None
                link.explanation = stale
                link_ids.append(link.id)
            states = dict(analysis.stage_states or {})
            current = dict(states.get("propositions") or {})
            if current:
                current["reason"] = stale
                states["propositions"] = current
            analysis.stage_states = states
            session.flush()
            return claim.text, history, link_ids

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
                .with_for_update(skip_locked=True)
            )
            if analysis is None:
                return False
            self._delete_file(analysis, delete_file)
            session.execute(delete(Analysis).where(Analysis.id == analysis_id))
            return True

    def purge_all_expired(
        self,
        now: datetime | None = None,
        *,
        delete_file: Callable[[str], bool] | None = None,
        batch_size: int = 100,
        failed_ids_out: list[UUID] | None = None,
    ) -> int:
        if now is None:
            now = datetime.now(UTC)
        if now.utcoffset() is None:
            raise ValueError("Cleanup time must be timezone-aware")
        if type(batch_size) is not int or not 1 <= batch_size <= 500:
            raise ValueError("Invalid batch size")

        total_purged = 0
        failed_ids: set[UUID] = set()

        while True:
            with transaction(self._factory) as session:
                query = select(Analysis).where(Analysis.expires_at <= now)
                if failed_ids:
                    query = query.where(Analysis.id.not_in(failed_ids))
                analyses = list(
                    session.scalars(
                        query.order_by(Analysis.expires_at, Analysis.id)
                        .limit(batch_size)
                        .with_for_update(skip_locked=True)
                    )
                )
                if not analyses:
                    break

                batch_deleted_ids: list[UUID] = []
                for analysis in analyses:
                    if analysis.stored_file_id is not None:
                        if delete_file is None:
                            failed_ids.add(analysis.id)
                            continue
                        try:
                            delete_file(str(analysis.stored_file_id))
                        except Exception:
                            failed_ids.add(analysis.id)
                            continue
                    batch_deleted_ids.append(analysis.id)

                if batch_deleted_ids:
                    session.execute(delete(Analysis).where(Analysis.id.in_(batch_deleted_ids)))
                    total_purged += len(batch_deleted_ids)

                if len(analyses) < batch_size:
                    break

        if failed_ids_out is not None:
            failed_ids_out.extend(failed_ids)

        return total_purged

    def acquire_lease(
        self,
        owner_hash: str,
        analysis_id: UUID,
        worker_id: str,
        lease_seconds: int = 120,
    ) -> bool:
        now = datetime.now(UTC)
        with transaction(self._factory) as session:
            analysis = session.scalar(
                select(Analysis)
                .where(
                    Analysis.id == analysis_id,
                    Analysis.owner_hash == owner_hash,
                    Analysis.expires_at > now,
                )
                .with_for_update()
            )
            if analysis is None or analysis.status not in {"queued", "running"}:
                return False

            states = dict(analysis.stage_states)
            lease_meta = dict(states.get("lease_metadata", {}))
            current_worker = lease_meta.get("worker_id")
            lease_exp_str = lease_meta.get("lease_expires_at")

            if analysis.status == "running" and current_worker and lease_exp_str:
                try:
                    lease_exp = datetime.fromisoformat(lease_exp_str)
                    if lease_exp > now and current_worker != worker_id:
                        return False
                except (ValueError, TypeError):
                    pass

            lease_meta["worker_id"] = worker_id
            lease_meta["lease_expires_at"] = (
                now + timedelta(seconds=lease_seconds)
            ).isoformat()
            if "retry_count" not in lease_meta:
                lease_meta["retry_count"] = 0

            states["lease_metadata"] = lease_meta
            analysis.stage_states = states
            analysis.status = "running"
            return True

    def renew_lease(
        self,
        owner_hash: str,
        analysis_id: UUID,
        worker_id: str,
        lease_seconds: int = 120,
    ) -> bool:
        now = datetime.now(UTC)
        with transaction(self._factory) as session:
            analysis = session.scalar(
                select(Analysis)
                .where(
                    Analysis.id == analysis_id,
                    Analysis.owner_hash == owner_hash,
                    Analysis.expires_at > now,
                )
                .with_for_update()
            )
            if analysis is None or analysis.status != "running":
                return False

            states = dict(analysis.stage_states)
            lease_meta = dict(states.get("lease_metadata", {}))
            if lease_meta.get("worker_id") != worker_id:
                return False

            lease_meta["lease_expires_at"] = (
                now + timedelta(seconds=lease_seconds)
            ).isoformat()
            states["lease_metadata"] = lease_meta
            analysis.stage_states = states
            return True

    def release_lease(
        self,
        owner_hash: str,
        analysis_id: UUID,
        worker_id: str,
    ) -> None:
        now = datetime.now(UTC)
        with transaction(self._factory) as session:
            analysis = session.scalar(
                select(Analysis)
                .where(
                    Analysis.id == analysis_id,
                    Analysis.owner_hash == owner_hash,
                    Analysis.expires_at > now,
                )
                .with_for_update()
            )
            if analysis is None:
                return

            states = dict(analysis.stage_states)
            lease_meta = dict(states.get("lease_metadata", {}))
            if lease_meta.get("worker_id") == worker_id:
                lease_meta["worker_id"] = None
                lease_meta["lease_expires_at"] = None
                states["lease_metadata"] = lease_meta
                analysis.stage_states = states

    def recover_orphaned_leases(
        self,
        now: datetime | None = None,
        max_retries: int = 2,
    ) -> tuple[int, int]:
        if now is None:
            now = datetime.now(UTC)
        if now.utcoffset() is None:
            raise ValueError("Recovery time must be timezone-aware")

        rescheduled_count = 0
        interrupted_count = 0

        with transaction(self._factory) as session:
            analyses = list(
                session.scalars(
                    select(Analysis)
                    .where(
                        Analysis.status == "running",
                        Analysis.expires_at > now,
                    )
                    .with_for_update()
                )
            )
            for analysis in analyses:
                states = dict(analysis.stage_states)
                lease_meta = dict(states.get("lease_metadata", {}))
                lease_exp_str = lease_meta.get("lease_expires_at")
                is_expired = False
                if not lease_exp_str:
                    is_expired = True
                else:
                    try:
                        lease_exp = datetime.fromisoformat(lease_exp_str)
                        if lease_exp <= now:
                            is_expired = True
                    except (ValueError, TypeError):
                        is_expired = True

                if not is_expired:
                    continue

                retry_count = int(lease_meta.get("retry_count", 0))
                if retry_count < max_retries:
                    lease_meta["retry_count"] = retry_count + 1
                    lease_meta["worker_id"] = None
                    lease_meta["lease_expires_at"] = None
                    states["lease_metadata"] = lease_meta

                    for stage_name, stage_state in list(states.items()):
                        if stage_name == "lease_metadata":
                            continue
                        if (
                            isinstance(stage_state, dict)
                            and stage_state.get("status") == "running"
                        ):
                            states[stage_name] = {
                                **stage_state,
                                "status": "queued",
                            }

                    analysis.stage_states = states
                    analysis.status = "queued"
                    rescheduled_count += 1
                else:
                    lease_meta["worker_id"] = None
                    lease_meta["lease_expires_at"] = None
                    states["lease_metadata"] = lease_meta

                    analysis.status = "interrupted"
                    analysis.overall_score = None
                    analysis.risk_level = None

                    for stage_name, stage_state in list(states.items()):
                        if stage_name == "lease_metadata":
                            continue
                        if (
                            isinstance(stage_state, dict)
                            and stage_state.get("status") in {"queued", "running"}
                        ):
                            states[stage_name] = {
                                **stage_state,
                                "status": "interrupted",
                                "reason": (
                                    "Execution retries exceeded after worker lease expired"
                                ),
                            }

                    analysis.stage_states = states
                    interrupted_count += 1

        return rescheduled_count, interrupted_count

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
                    if isinstance(state, dict) and state.get("status") in {"queued", "running"}:
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
