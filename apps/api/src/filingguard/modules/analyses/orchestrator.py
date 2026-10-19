"""Single-process review handoff; legal stages are supplied by their owning modules."""

import logging
import time
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore, Event
from uuid import UUID, uuid4

from filingguard.db.models import Authority, Citation, Claim, ClaimAuthorityLink, DocumentSegment
from filingguard.db.repository import AnalysisRepository
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.execution import (
    ReviewLimits,
    ReviewSegment,
    StageExecutionError,
    StageRunner,
    execute_stage,
    runner_name,
)
from filingguard.modules.analyses.execution import StageResult as StageResult
from filingguard.modules.analyses.schemas import StageName, StageStatus

logger = logging.getLogger(__name__)
# Local checks survive provider failures and the global work cutoff.
REVIEW_STAGES = (
    StageName.PRIVACY,
    StageName.COURT_RULES,
    StageName.CITATIONS,
    StageName.STATUTES,
    StageName.TABLE_OF_AUTHORITIES,
    StageName.CLAIMS,
    StageName.PROPOSITIONS,
    StageName.QUOTES,
)


class ReviewOrchestrator:
    def __init__(
        self,
        repository: AnalysisRepository,
        slot: BoundedSemaphore,
        runners: Mapping[StageName, StageRunner],
        *,
        limits: ReviewLimits | None = None,
        credentials: dict[str, str] | None = None,
        worker_id: str | None = None,
    ):
        if set(runners) != set(REVIEW_STAGES):
            raise ValueError("All review stages must be registered before jobs are accepted")
        self.repository = repository
        self.slot = slot
        self.runners = dict(runners)
        for stage, runner in self.runners.items():
            if isinstance(runner, StageResult):
                runner.validate(stage)
                if (
                    runner.status not in {StageStatus.UNAVAILABLE, StageStatus.SKIPPED}
                    or runner.records
                ):
                    raise ValueError(
                        "Only unavailable or inapplicable metadata can bypass a worker"
                    )
            else:
                runner_name(runner)
        self.limits = limits or ReviewLimits()
        self.credentials = dict(credentials or {})
        self.worker_id = worker_id or f"worker-{uuid4().hex[:12]}"
        self.stop = Event()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="filingguard-review")

    def start(self, owner_hash: str, analysis_id: UUID) -> None:
        if self.stop.is_set():
            raise RuntimeError("Review worker is shutting down")
        if not self.slot.acquire(blocking=False):
            raise OverflowError("Another review or preparation is active")
        try:
            self.repository.queue_review(owner_hash, analysis_id, REVIEW_STAGES)
            try:
                deadline = time.monotonic() + self.limits.overall_seconds
                self.executor.submit(self._run_and_release, owner_hash, analysis_id, deadline)
            except RuntimeError as error:
                logger.error(
                    "review.submit_failed analysis_id=%s correlation_id=%s error_type=%s",
                    analysis_id,
                    analysis_id,
                    type(error).__name__,
                )
                for stage in REVIEW_STAGES:
                    with self.repository.stage_update(
                        owner_hash,
                        analysis_id,
                        stage,
                        "interrupted",
                        reason="Review worker unavailable",
                        analysis_status="interrupted",
                    ):
                        pass
                raise
        except Exception:
            self.slot.release()
            raise

    def _run_and_release(self, owner_hash: str, analysis_id: UUID, deadline: float) -> None:
        try:
            acquired = self.repository.acquire_lease(
                owner_hash, analysis_id, self.worker_id, lease_seconds=120
            )
            if not acquired:
                logger.warning(
                    "review.lease_acquire_failed analysis_id=%s correlation_id=%s worker_id=%s",
                    analysis_id,
                    analysis_id,
                    self.worker_id,
                )
                return
            self._run(owner_hash, analysis_id, deadline)
        finally:
            try:
                self.repository.release_lease(owner_hash, analysis_id, self.worker_id)
            except Exception as release_error:
                logger.error(
                    "review.lease_release_failed analysis_id=%s correlation_id=%s error_type=%s",
                    analysis_id,
                    analysis_id,
                    type(release_error).__name__,
                )
            try:
                self.slot.release()
            except ValueError:
                pass

    def _run(self, owner_hash: str, analysis_id: UUID, deadline: float) -> None:
        completed = 0
        budget = ProviderBudget(deadline=deadline, max_attempts=self.limits.max_provider_attempts)
        job_started = time.perf_counter()
        logger.info(
            "review.job.start analysis_id=%s correlation_id=%s stage_count=%d",
            analysis_id,
            analysis_id,
            len(REVIEW_STAGES),
        )
        for index, stage in enumerate(REVIEW_STAGES):
            started = time.perf_counter()
            self.repository.renew_lease(
                owner_hash, analysis_id, self.worker_id, lease_seconds=120
            )
            logger.info(
                "review.stage.start analysis_id=%s correlation_id=%s stage=%s",
                analysis_id,
                analysis_id,
                stage.value,
            )
            try:
                with self.repository.stage_update(
                    owner_hash, analysis_id, stage, "running", analysis_status="running"
                ):
                    pass
                analysis = self.repository.get_analysis(owner_hash, analysis_id)
                segments = ()
                context = {}
                if stage in {
                    StageName.CITATIONS,
                    StageName.CLAIMS,
                    StageName.PROPOSITIONS,
                    StageName.QUOTES,
                } and callable(self.runners[stage]):
                    rows = sorted(
                        self.repository.list_records(owner_hash, analysis_id, DocumentSegment),
                        key=lambda row: row.paragraph_index,
                    )
                    text = analysis.document_snapshot["text"]
                    if any(row.text != text[row.start_offset : row.end_offset] for row in rows):
                        raise ValueError("Persisted paragraph text mismatch")
                    segments = tuple(
                        ReviewSegment(
                            id=row.id,
                            start=row.start_offset,
                            end=row.end_offset,
                            page_number=row.page_number,
                        )
                        for row in rows
                    )
                    needed = {
                        StageName.CITATIONS: (),
                        StageName.CLAIMS: (("citations", Citation),),
                        StageName.PROPOSITIONS: (
                            ("citations", Citation),
                            ("authorities", Authority),
                            ("claims", Claim),
                            ("links", ClaimAuthorityLink),
                        ),
                        StageName.QUOTES: (("citations", Citation), ("authorities", Authority)),
                    }[stage]
                    context = {
                        key: tuple(self.repository.list_records(owner_hash, analysis_id, model))
                        for key, model in needed
                    }
                permitted = (
                    ("courtlistener",)
                    if stage == StageName.CITATIONS
                    else (("groq", "groq_model") if stage == StageName.PROPOSITIONS else ())
                )
                result = execute_stage(
                    self.runners[stage],
                    analysis,
                    stage,
                    budget,
                    stage_seconds=self.limits.stage_seconds,
                    stop=self.stop,
                    segments=segments,
                    context=context,
                    credentials={
                        key: self.credentials[key] for key in permitted if key in self.credentials
                    },
                )
                result.validate(stage)
                final_status = "running"
                if stage == REVIEW_STAGES[-1]:
                    final_status = (
                        "completed"
                        if completed == len(REVIEW_STAGES) - 1
                        and result.status in {StageStatus.COMPLETED, StageStatus.SKIPPED}
                        else "partial"
                    )
                with self.repository.stage_update(
                    owner_hash,
                    analysis_id,
                    stage,
                    result.status,
                    coverage=result.coverage,
                    reason=result.reason,
                    applicable=result.status != StageStatus.SKIPPED,
                    analysis_status=final_status,
                ) as writer:
                    writer.add(*result.records)
                    writer.update_propositions(*result.updates)
                self.repository.renew_lease(
                    owner_hash, analysis_id, self.worker_id, lease_seconds=120
                )
                if result.status in {StageStatus.COMPLETED, StageStatus.SKIPPED}:
                    completed += 1
                logger.info(
                    "review.stage.finish analysis_id=%s correlation_id=%s "
                    "stage=%s status=%s duration_ms=%d",
                    analysis_id,
                    analysis_id,
                    stage.value,
                    result.status.value,
                    int((time.perf_counter() - started) * 1000),
                )
            except Exception as error:
                state = (
                    error.status if isinstance(error, StageExecutionError) else StageStatus.FAILED
                )
                reason = (
                    error.reason
                    if isinstance(error, StageExecutionError)
                    else "Review stage failed"
                )
                logger.error(
                    "review.stage.finish analysis_id=%s correlation_id=%s stage=%s status=%s "
                    "error_type=%s duration_ms=%d",
                    analysis_id,
                    analysis_id,
                    stage.value,
                    state.value,
                    type(error).__name__,
                    int((time.perf_counter() - started) * 1000),
                )
                try:
                    with self.repository.stage_update(
                        owner_hash,
                        analysis_id,
                        stage,
                        state,
                        reason=reason,
                        analysis_status=("interrupted" if self.stop.is_set() else "partial")
                        if index == len(REVIEW_STAGES) - 1
                        else "running",
                    ):
                        pass
                except Exception as persist_error:
                    logger.error(
                        "review.stage.persist_failed analysis_id=%s "
                        "correlation_id=%s stage=%s error_type=%s",
                        analysis_id,
                        analysis_id,
                        stage.value,
                        type(persist_error).__name__,
                    )
                    return
        logger.info(
            "review.job.finish analysis_id=%s correlation_id=%s "
            "status=%s completed_stages=%d duration_ms=%d",
            analysis_id,
            analysis_id,
            "interrupted"
            if self.stop.is_set()
            else "completed"
            if completed == len(REVIEW_STAGES)
            else "partial",
            completed,
            int((time.perf_counter() - job_started) * 1000),
        )

    def close(self) -> None:
        self.stop.set()
        self.executor.shutdown(wait=True, cancel_futures=False)
