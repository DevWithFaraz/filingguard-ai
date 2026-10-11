"""Process-local private storage with conservative PDF admission checks."""

import os
import stat
import tempfile
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from threading import RLock
from types import TracebackType
from uuid import UUID, uuid4

from pypdf import Configuration, PdfReader, apply_configuration
from pypdf.errors import LimitReachedError
from pypdf.generic import ArrayObject, DictionaryObject, NullObject, StreamObject

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_PAGES = 20
MAX_TEXT_CHARACTERS = 100_000
MAX_STREAM_BYTES = 2 * 1024 * 1024
MAX_DOCUMENT_STREAM_BYTES = 8 * 1024 * 1024
DEFAULT_RETENTION_SECONDS = 3600

_PARSER_CONFIGURATION = Configuration(
    maximum_declared_stream_length=MAX_STREAM_BYTES,
    array_based_stream_maximum_output_length=MAX_STREAM_BYTES,
    zlib_maximum_output_length=MAX_STREAM_BYTES,
    zlib_maximum_recovery_input_length=64 * 1024,
    lzw_maximum_output_length=MAX_STREAM_BYTES,
    run_length_maximum_output_length=MAX_STREAM_BYTES,
    jbig2_maximum_output_length=MAX_STREAM_BYTES,
    image_maximum_buffer_size=MAX_STREAM_BYTES,
    flate_maximum_columns=64 * 1024,
    flate_maximum_row_length=MAX_STREAM_BYTES,
    page_tree_maximum_entries=256,
    page_tree_maximum_depth=32,
    xform_maximum_invocations_per_extraction=100,
    jbig2dec_binary=None,
)


class PDFValidationError(ValueError):
    """Safe admission failure, with a stable machine-readable reason."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class InvalidStorageID(ValueError):
    def __init__(self) -> None:
        super().__init__("Invalid temporary file ID.")


class StorageError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Private temporary storage is unavailable.")


class StoredPDFNotFound(LookupError):
    def __init__(self) -> None:
        super().__init__("Temporary file is unavailable or expired.")


@dataclass(frozen=True)
class StoredPDF:
    file_id: str
    size_bytes: int
    page_count: int
    character_count: int


@dataclass(frozen=True)
class _Entry:
    metadata: StoredPDF
    expires_at: float
    identity: tuple[int, int]


def _identity(info: os.stat_result) -> tuple[int, int]:
    return info.st_dev, info.st_ino


def _is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    )


def _parse_pdf(data: bytes) -> list[str]:
    if not isinstance(data, bytes):
        raise PDFValidationError("invalid_bytes", "Supply PDF bytes.")
    if len(data) > MAX_FILE_BYTES:
        raise PDFValidationError("file_too_large", "PDF exceeds the 10 MiB limit.")
    if not data.startswith(b"%PDF-"):
        raise PDFValidationError("invalid_signature", "File must have a PDF signature.")

    # Limits are local to this parsing context, including compressed object streams.
    try:
        with apply_configuration(_PARSER_CONFIGURATION):
            reader = PdfReader(BytesIO(data), strict=True, root_object_recovery_limit=0)
            if reader.is_encrypted:
                raise PDFValidationError("encrypted_pdf", "Encrypted PDFs are unsupported.")
            page_count = len(reader.pages)
            if not 1 <= page_count <= MAX_PAGES:
                raise PDFValidationError("page_limit", "PDF must contain between 1 and 20 pages.")

            decoded_bytes = 0
            stream_count = 0
            seen: set[int] = set()

            def check_stream(value: object, depth: int = 0) -> None:
                nonlocal decoded_bytes, stream_count
                if depth > 16:
                    raise LimitReachedError("Content nesting limit.")
                value = value.get_object()
                if isinstance(value, NullObject):
                    return
                if isinstance(value, ArrayObject):
                    if len(value) > 64:
                        raise LimitReachedError("Content array limit.")
                    for item in value:
                        check_stream(item, depth + 1)
                    return
                if not isinstance(value, StreamObject):
                    raise ValueError("Invalid content stream.")
                if id(value) in seen:
                    return
                seen.add(id(value))
                stream_count += 1
                if stream_count > 256:
                    raise LimitReachedError("Content stream count limit.")
                length = len(value.get_data())
                decoded_bytes += length
                if length > MAX_STREAM_BYTES or decoded_bytes > MAX_DOCUMENT_STREAM_BYTES:
                    raise LimitReachedError("Decoded content limit.")
                check_resources(value.get("/Resources"), depth + 1)

            def check_resources(value: object, depth: int = 0) -> None:
                if value is None:
                    return
                if depth > 16:
                    raise LimitReachedError("Resource nesting limit.")
                resources = value.get_object()
                if not isinstance(resources, DictionaryObject):
                    raise ValueError("Invalid resources.")
                objects = resources.get("/XObject")
                if objects is None:
                    return
                objects = objects.get_object()
                if not isinstance(objects, DictionaryObject) or len(objects) > 128:
                    raise LimitReachedError("Resource count limit.")
                for reference in objects.values():
                    obj = reference.get_object()
                    if not isinstance(obj, StreamObject):
                        raise ValueError("Invalid external object.")
                    if obj.get("/Subtype") == "/Form":
                        check_stream(obj, depth + 1)

            # Preflight every page/form before asking pypdf to build extracted text.
            for page in reader.pages:
                contents = page.get("/Contents")
                if contents is not None:
                    check_stream(contents)
                check_resources(page.get("/Resources"))

            characters = 0
            has_text = False
            texts = []
            for page in reader.pages:
                visited_characters = 0
                text_budget_exceeded = False

                def check_text(text: str, *_: object, previous: int = characters) -> None:
                    nonlocal visited_characters, text_budget_exceeded
                    visited_characters += len(text)
                    if previous + visited_characters > MAX_TEXT_CHARACTERS:
                        text_budget_exceeded = True
                        raise PDFValidationError(
                            "text_limit", "PDF exceeds 100,000 extracted characters."
                        )

                text = page.extract_text(visitor_text=check_text)
                texts.append(text)
                characters += len(text)
                has_text = has_text or bool(text.strip())
                if text_budget_exceeded or characters > MAX_TEXT_CHARACTERS:
                    raise PDFValidationError(
                        "text_limit", "PDF exceeds 100,000 extracted characters."
                    )
            if not has_text:
                raise PDFValidationError(
                    "no_text", "PDF contains no extractable text; paste text instead."
                )
            return texts
    except PDFValidationError:
        raise
    except LimitReachedError:
        raise PDFValidationError("parser_limit", "PDF exceeds parsing resource limits.") from None
    except Exception as error:
        # Some pypdf dictionary reads wrap resource-limit exceptions in PdfReadError.
        cause = error
        for _ in range(8):
            if isinstance(cause, LimitReachedError):
                raise PDFValidationError(
                    "parser_limit", "PDF exceeds parsing resource limits."
                ) from None
            cause = cause.__cause__ or cause.__context__
            if cause is None:
                break
        # Parser exception messages may include document fragments or object values.
        raise PDFValidationError("malformed_pdf", "PDF cannot be parsed safely.") from None


def _validate_pdf(data: bytes) -> tuple[int, int]:
    pages = _parse_pdf(data)
    return len(pages), sum(map(len, pages))


class PrivateTemporaryStorage:
    """Own a fresh OS-temp directory; expose only bytes and registered UUIDs."""

    def __init__(self, *, retention_seconds: int = DEFAULT_RETENTION_SECONDS) -> None:
        if type(retention_seconds) is not int or retention_seconds <= 0:
            raise ValueError("Retention must be a positive number of seconds.")
        self._retention_seconds = retention_seconds
        self._entries: dict[str, _Entry] = {}
        self._lock = RLock()
        self._closed = False
        try:
            self._root = Path(tempfile.mkdtemp(prefix="filingguard-private-")).resolve()
            self._root_identity = _identity(self._root.lstat())
            try:
                self._root.chmod(0o700)
            except OSError:
                if os.name != "nt":
                    raise
        except OSError:
            raise StorageError() from None

    def __enter__(self) -> "PrivateTemporaryStorage":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def _check_root(self) -> None:
        if self._closed:
            raise StorageError()
        try:
            info = self._root.lstat()
            if _is_link(info) or not stat.S_ISDIR(info.st_mode):
                raise StorageError()
            if _identity(info) != self._root_identity:
                raise StorageError()
        except OSError:
            raise StorageError() from None

    def _validate_id(self, file_id: str) -> None:
        try:
            parsed = UUID(file_id) if isinstance(file_id, str) else None
            if parsed is None or parsed.version != 4 or str(parsed) != file_id:
                raise InvalidStorageID()
        except (ValueError, AttributeError):
            raise InvalidStorageID() from None

    def _check_file(self, file_id: str, entry: _Entry) -> Path:
        self._check_root()
        path = self._root / f"{file_id}.pdf"
        try:
            info = path.lstat()
            if (
                _is_link(info)
                or not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or _identity(info) != entry.identity
                or info.st_size != entry.metadata.size_bytes
            ):
                raise StorageError()
        except OSError:
            raise StorageError() from None
        return path

    def store(self, data: bytes) -> StoredPDF:
        """Validate first, then exclusively create a random private filename."""
        pages, characters = _validate_pdf(data)
        return self._store_validated(data, pages, characters)

    def _store_validated(self, data: bytes, pages: int, characters: int) -> StoredPDF:
        """Internal boundary: caller must have validated these bytes in the PDF worker."""
        with self._lock:
            self._check_root()
            if not (
                isinstance(data, bytes)
                and data.startswith(b"%PDF-")
                and len(data) <= MAX_FILE_BYTES
                and 1 <= pages <= MAX_PAGES
                and 1 <= characters <= MAX_TEXT_CHARACTERS
            ):
                raise StorageError()
            self._check_root()
            file_id = str(uuid4())
            path = self._root / f"{file_id}.pdf"
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
            flags |= getattr(os, "O_BINARY", 0)
            created = False
            try:
                descriptor = os.open(path, flags, 0o600)
                created = True
                with os.fdopen(descriptor, "wb") as output:
                    output.write(data)
                    output.flush()
                    identity = _identity(os.fstat(output.fileno()))
                metadata = StoredPDF(file_id, len(data), pages, characters)
                self._entries[file_id] = _Entry(
                    metadata, time.monotonic() + self._retention_seconds, identity
                )
                return metadata
            except OSError:
                if created:
                    try:
                        path.unlink()
                    except OSError:
                        pass
                raise StorageError() from None

    def read(self, file_id: str) -> bytes:
        """Read a registered, unexpired file; never resolve caller paths."""
        with self._lock:
            self._validate_id(file_id)
            self._check_root()
            entry = self._entries.get(file_id)
            if entry is None:
                raise StoredPDFNotFound()
            if time.monotonic() >= entry.expires_at:
                self.delete(file_id)
                raise StoredPDFNotFound()
            path = self._check_file(file_id, entry)
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
            try:
                with os.fdopen(os.open(path, flags), "rb") as source:
                    info = os.fstat(source.fileno())
                    if (
                        _identity(info) != entry.identity
                        or not stat.S_ISREG(info.st_mode)
                        or info.st_nlink != 1
                    ):
                        raise StorageError()
                    data = source.read(MAX_FILE_BYTES + 1)
                    if len(data) != entry.metadata.size_bytes:
                        raise StorageError()
                    return data
            except OSError:
                raise StorageError() from None

    def delete(self, file_id: str) -> bool:
        """Delete only a registered file. Repeated deletion returns False."""
        with self._lock:
            self._validate_id(file_id)
            self._check_root()
            entry = self._entries.get(file_id)
            if entry is None:
                return False
            path = self._check_file(file_id, entry)
            try:
                path.unlink()
            except OSError:
                raise StorageError() from None
            del self._entries[file_id]
            return True

    def cleanup_expired(self) -> int:
        """Explicit sweep; scheduling belongs to the application lifecycle."""
        with self._lock:
            self._check_root()
            now = time.monotonic()
            expired = [key for key, entry in self._entries.items() if now >= entry.expires_at]
            for file_id in expired:
                self.delete(file_id)
            return len(expired)

    def close(self) -> None:
        """Delete owned files and the empty directory; never recursively traverse."""
        with self._lock:
            if self._closed:
                return
            self._check_root()
            for file_id in list(self._entries):
                self.delete(file_id)
            try:
                self._root.rmdir()
            except OSError:
                raise StorageError() from None
            self._closed = True
