"""Single-process, restart-recoverable registry in a dedicated private directory."""

import hashlib
import json
import os
import stat
import time
from pathlib import Path
from threading import RLock

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, StrictInt

from filingguard.integrations.storage.service import (
    DEFAULT_RETENTION_SECONDS,
    MAX_FILE_BYTES,
    PrivateTemporaryStorage,
    StorageError,
    StoredPDF,
    _Entry,
    _identity,
    _is_link,
)


class FileReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: StrictInt = Field(ge=1, le=1)
    file_id: str
    size_bytes: StrictInt = Field(gt=0, le=MAX_FILE_BYTES)
    page_count: StrictInt = Field(ge=1, le=20)
    character_count: StrictInt = Field(gt=0, le=100000)
    expires_at: FiniteFloat = Field(gt=0)
    identity: tuple[StrictInt, StrictInt]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class RecoverableTemporaryStorage(PrivateTemporaryStorage):
    """Server-selected root only; never accept a path from an upload/request."""

    def __init__(
        self, directory: Path, *, retention_seconds: int = DEFAULT_RETENTION_SECONDS
    ) -> None:
        if type(retention_seconds) is not int or retention_seconds <= 0:
            raise ValueError("Retention must be a positive number of seconds.")
        if not directory.is_absolute():
            raise ValueError("Private storage directory must be absolute.")
        self._retention_seconds = retention_seconds
        self._entries = {}
        self._lock = RLock()
        self._closed = False
        self._lease = None
        self._root = directory
        try:
            created = False
            try:
                directory.mkdir(mode=0o700)
                created = True
            except FileExistsError:
                pass
            info = directory.lstat()
            if _is_link(info) or not stat.S_ISDIR(info.st_mode):
                raise StorageError()
            if os.name != "nt" and stat.S_IMODE(info.st_mode) & 0o077:
                raise StorageError()
            self._root = directory.resolve()
            self._root_identity = _identity(info)
            marker = {"version": 1, "identity": list(self._root_identity)}
            if created:
                self._write_json(".owner.json", marker)
            elif self._read_json(".owner.json") != marker:
                raise StorageError()
            self._acquire_lease()
            self._restore()
        except (OSError, ValueError, TypeError, KeyError, StorageError):
            self._release_lease()
            raise StorageError() from None

    def _regular(self, path: Path, limit: int) -> os.stat_result:
        self._check_root()
        info = path.lstat()
        if (
            _is_link(info)
            or not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_size > limit
        ):
            raise StorageError()
        return info

    def _read_json(self, name: str):
        path = self._root / name
        info = self._regular(path, 4096)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
        with os.fdopen(os.open(path, flags), "rb") as source:
            if _identity(os.fstat(source.fileno())) != _identity(info):
                raise StorageError()
            return json.loads(source.read(4097))

    def _write_json(self, name: str, value: dict) -> None:
        self._check_root()
        path = self._root / name
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        flags |= getattr(os, "O_BINARY", 0)
        with os.fdopen(os.open(path, flags, 0o600), "wb") as output:
            output.write(json.dumps(value).encode("utf-8"))
            output.flush()
            os.fsync(output.fileno())

    def _acquire_lease(self) -> None:
        path = self._root / ".lease"
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        self._lease = os.fdopen(os.open(path, flags, 0o600), "r+b")
        self._regular(path, 1)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self._lease.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(self._lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _release_lease(self) -> None:
        if self._lease is not None:
            self._lease.close()
            self._lease = None

    def _restore(self) -> None:
        paths = list(self._root.iterdir())
        if len(paths) > 2002:
            raise StorageError()
        receipts, pdfs = {}, {}
        # Validate the entire flat namespace before deleting any crash leftovers.
        for path in paths:
            if path.name in {".owner.json", ".lease"}:
                self._regular(path, 4096)
                continue
            self._validate_id(path.stem)
            if path.suffix == ".json":
                receipt = FileReceipt.model_validate(self._read_json(path.name))
                if receipt.file_id != path.stem:
                    raise StorageError()
                receipts[path.stem] = receipt
            elif path.suffix == ".pdf":
                pdfs[path.stem] = self._regular(path, MAX_FILE_BYTES)
            else:
                raise StorageError()
        for file_id, receipt in receipts.items():
            if file_id not in pdfs:
                continue
            info = pdfs[file_id]
            if _identity(info) != receipt.identity or info.st_size != receipt.size_bytes:
                raise StorageError()
            metadata = StoredPDF(
                file_id, receipt.size_bytes, receipt.page_count, receipt.character_count
            )
            remaining = max(0.0, min(receipt.expires_at - time.time(), self._retention_seconds))
            self._entries[file_id] = _Entry(
                metadata, time.monotonic() + remaining, receipt.identity
            )
            if remaining > 0:
                data = super().read(file_id)
                if hashlib.sha256(data).hexdigest() != receipt.sha256:
                    raise StorageError()
        for file_id in pdfs.keys() - receipts.keys():
            (self._root / f"{file_id}.pdf").unlink()
        for file_id in receipts.keys() - pdfs.keys():
            (self._root / f"{file_id}.json").unlink()
        self.cleanup_expired()

    @property
    def retention_seconds(self) -> int:
        return self._retention_seconds

    def _store_validated(self, data: bytes, pages: int, characters: int) -> StoredPDF:
        with self._lock:
            if len(self._entries) >= 1000:
                raise StorageError()
            metadata = super()._store_validated(data, pages, characters)
            entry = self._entries[metadata.file_id]
            try:
                receipt = FileReceipt(
                    version=1,
                    file_id=metadata.file_id,
                    size_bytes=metadata.size_bytes,
                    page_count=metadata.page_count,
                    character_count=metadata.character_count,
                    expires_at=time.time() + self._retention_seconds,
                    identity=entry.identity,
                    sha256=hashlib.sha256(data).hexdigest(),
                )
                self._write_json(f"{metadata.file_id}.json", receipt.model_dump(mode="json"))
                return metadata
            except FileExistsError:
                super().delete(metadata.file_id)
                raise StorageError() from None
            except (OSError, ValueError):
                # Retain a registered entry if compensation fails; expiry cleanup can retry it.
                self.delete(metadata.file_id)
                raise StorageError() from None

    def delete(self, file_id: str) -> bool:
        with self._lock:
            self._validate_id(file_id)
            self._check_root()
            entry = self._entries.get(file_id)
            if entry is None:
                return False
            try:
                path = self._root / f"{file_id}.pdf"
                try:
                    path.lstat()
                except FileNotFoundError:
                    pass
                else:
                    super().delete(file_id)
                sidecar = self._root / f"{file_id}.json"
                try:
                    self._regular(sidecar, 4096)
                except FileNotFoundError:
                    pass
                else:
                    sidecar.unlink()
                self._entries.pop(file_id, None)
                return True
            except (OSError, StorageError):
                self._entries[file_id] = entry
                raise StorageError() from None

    def cleanup_expired(self) -> int:
        with self._lock:
            self._check_root()
            now = time.monotonic()
            expired = [key for key, entry in self._entries.items() if now >= entry.expires_at]
            failed = False
            for file_id in expired:
                try:
                    self.delete(file_id)
                except StorageError:
                    failed = True
            if failed:
                raise StorageError()
            return len(expired)

    def close(self, *, purge: bool = True) -> None:
        with self._lock:
            if self._closed:
                return
            try:
                self._check_root()
                if purge:
                    failed = False
                    for file_id in list(self._entries):
                        try:
                            self.delete(file_id)
                        except StorageError:
                            failed = True
                    if failed:
                        raise StorageError()
            finally:
                self._closed = True
                self._release_lease()
