"""Coordinate private bytes with owner-scoped DB transactions and bounded expiry sweeps."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from threading import RLock
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from filingguard.db.repository import AnalysisRepository
from filingguard.integrations.storage.managed import RecoverableTemporaryStorage
from filingguard.integrations.storage.service import StorageError


@dataclass(frozen=True)
class CleanupResult:
    analyses_deleted: int
    files_deleted: int
    failures: int


class AnalysisLifecycle:
    def __init__(self, repository: AnalysisRepository, storage: RecoverableTemporaryStorage):
        self.repository = repository
        self.storage = storage
        self._lock = RLock()

    def create_pdf(self, owner_hash: str, data: bytes, *, document_name: str, expires_at: datetime):
        now = datetime.now(UTC)
        if expires_at.utcoffset() is None or not (
            now < expires_at <= now + timedelta(seconds=self.storage.retention_seconds)
        ):
            raise ValueError("Analysis expiry must fit the private file retention window")
        with self._lock:
            file = self.storage.store(data)
            try:
                return self.repository.create_analysis(
                    owner_hash,
                    document_name=document_name,
                    document_sha256=sha256(data).hexdigest(),
                    expires_at=expires_at,
                    stored_file_id=UUID(file.file_id),
                )
            except Exception:
                self.storage.delete(file.file_id)
                raise

    def delete(self, owner_hash: str, analysis_id: UUID) -> None:
        with self._lock:
            self.repository.delete_analysis(
                owner_hash, analysis_id, delete_file=self.storage.delete
            )

    def recover(self) -> int:
        """Call once before admitting work in this single API process."""
        with self._lock:
            return self.repository.interrupt_pending()

    def cleanup(self, now: datetime | None = None) -> CleanupResult:
        with self._lock:
            now = now or datetime.now(UTC)
            deleted, failures = 0, 0
            for analysis_id in self.repository.expired_ids(now):
                try:
                    deleted += self.repository.delete_expired(
                        analysis_id, now, delete_file=self.storage.delete
                    )
                except (StorageError, SQLAlchemyError):
                    failures += 1
            try:
                files = self.storage.cleanup_expired()
            except StorageError:
                files = 0
                failures += 1
            try:
                self.repository.prune_sessions()
            except SQLAlchemyError:
                failures += 1
            return CleanupResult(deleted, files, failures)
