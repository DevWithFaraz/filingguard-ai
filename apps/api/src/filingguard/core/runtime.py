"""Application-owned cleanup, with no database connection during shell startup."""

import asyncio
import logging
from collections.abc import Mapping
from contextlib import asynccontextmanager
from threading import BoundedSemaphore, RLock

from fastapi import FastAPI

from filingguard.core.config import Settings
from filingguard.db.repository import AnalysisRepository
from filingguard.db.session import create_db_engine, create_session_factory
from filingguard.integrations.storage.managed import RecoverableTemporaryStorage
from filingguard.integrations.storage.service import PrivateTemporaryStorage, StorageError
from filingguard.modules.analyses.execution import ReviewLimits
from filingguard.modules.analyses.lifecycle import AnalysisLifecycle
from filingguard.modules.analyses.orchestrator import ReviewOrchestrator, StageRunner
from filingguard.modules.analyses.schemas import StageName

logger = logging.getLogger(__name__)


class AnalysisRuntime:
    def __init__(
        self,
        storage: PrivateTemporaryStorage,
        *,
        limits: ReviewLimits | None = None,
        credentials: dict[str, str] | None = None,
    ):
        self.storage = storage
        self.limits = limits or ReviewLimits()
        self.credentials = dict(credentials or {})
        self.lifecycle: AnalysisLifecycle | None = None
        self.review: ReviewOrchestrator | None = None
        self._engine = None
        self._lock = RLock()
        self.cleanup_failed = False

    def get_lifecycle(self) -> AnalysisLifecycle:
        """Private authorization/routes and maintenance call this in a worker thread."""
        with self._lock:
            if self.lifecycle is None:
                if not isinstance(self.storage, RecoverableTemporaryStorage):
                    raise ValueError("Recoverable private storage must be configured before intake")
                engine = create_db_engine()
                try:
                    lifecycle = AnalysisLifecycle(
                        AnalysisRepository(create_session_factory(engine)), self.storage
                    )
                    lifecycle.recover()
                except Exception:
                    engine.dispose()
                    raise
                self._engine = engine
                self.lifecycle = lifecycle
            return self.lifecycle

    def get_review(
        self, slot: BoundedSemaphore, runners: Mapping[StageName, StageRunner]
    ) -> ReviewOrchestrator:
        with self._lock:
            if self.review is None:
                self.review = ReviewOrchestrator(
                    self.get_lifecycle().repository,
                    slot,
                    runners,
                    limits=self.limits,
                    credentials=self.credentials,
                )
            return self.review

    def sweep(self) -> None:
        with self._lock:
            # Sweep files before any potentially slow database connection/query.
            file_cleanup_failed = False
            try:
                self.storage.cleanup_expired()
            except StorageError:
                file_cleanup_failed = True
            if self.lifecycle is None and not isinstance(self.storage, RecoverableTemporaryStorage):
                self.cleanup_failed = file_cleanup_failed
            else:
                try:
                    failures = self.get_lifecycle().cleanup().failures
                    self.cleanup_failed = file_cleanup_failed or failures > 0
                except Exception:
                    self.cleanup_failed = True
                    # File retention must not depend on database availability.
                    self.storage.cleanup_expired()
                    raise
            if self.cleanup_failed:
                logger.warning("Private cleanup incomplete; retry scheduled")

    def close(self) -> None:
        with self._lock:
            try:
                if self.review is not None:
                    self.review.close()
                self.storage.close()
            finally:
                if self._engine is not None:
                    self._engine.dispose()


async def run_cleanup(runtime: AnalysisRuntime, stop: asyncio.Event, interval: float) -> None:
    while not stop.is_set():
        try:
            await asyncio.to_thread(runtime.sweep)
        except Exception as error:
            runtime.cleanup_failed = True
            logger.warning("Private cleanup failed (%s); retry scheduled", type(error).__name__)
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except TimeoutError:
            pass


def application_lifespan(settings: Settings):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        def create_storage():
            if settings.private_storage_directory is not None:
                return RecoverableTemporaryStorage(settings.private_storage_directory)
            return PrivateTemporaryStorage()

        storage = await asyncio.to_thread(create_storage)
        runtime = AnalysisRuntime(
            storage,
            credentials={
                **(
                    {"courtlistener": settings.courtlistener_api_token or ""}
                    if settings.source_verification_enabled
                    else {}
                ),
                **(
                    {
                        "groq": settings.groq_api_key.get_secret_value()
                        if settings.groq_api_key
                        else "",
                        "groq_model": settings.groq_model,
                    }
                    if settings.semantic_review_enabled
                    else {}
                ),
            },
            limits=ReviewLimits(
                overall_seconds=settings.analysis_timeout_seconds,
                stage_seconds=settings.review_stage_timeout_seconds,
                max_provider_attempts=settings.max_provider_attempts,
            ),
        )
        app.state.analysis_runtime = runtime
        stop = asyncio.Event()
        task = asyncio.create_task(run_cleanup(runtime, stop, settings.cleanup_interval_seconds))
        try:
            yield
        finally:
            stop.set()
            # Let an in-flight threaded sweep finish before closing its files/engine.
            await task
            await asyncio.to_thread(runtime.close)

    return lifespan
