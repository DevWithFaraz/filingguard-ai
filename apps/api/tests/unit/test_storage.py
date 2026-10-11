import os
import stat
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pypdf import PdfWriter, get_configuration
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NumberObject,
)

from filingguard.integrations.storage import (
    InvalidStorageID,
    PDFValidationError,
    PrivateTemporaryStorage,
    StorageError,
    StoredPDFNotFound,
    service,
)


def pdf_bytes(
    texts: tuple[str, ...] = ("Synthetic filing for private storage.",),
    *,
    encrypted: bool = False,
    compressed: bool = False,
    padding: int = 0,
    image_only: bool = False,
) -> bytes:
    writer = PdfWriter()
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_reference = writer._add_object(font)
    for text in texts:
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_reference})}
        )
        contents = DecodedStreamObject()
        if image_only:
            image = DecodedStreamObject()
            image.update(
                {
                    NameObject("/Type"): NameObject("/XObject"),
                    NameObject("/Subtype"): NameObject("/Image"),
                    NameObject("/Width"): NumberObject(1),
                    NameObject("/Height"): NumberObject(1),
                    NameObject("/ColorSpace"): NameObject("/DeviceGray"),
                    NameObject("/BitsPerComponent"): NumberObject(8),
                }
            )
            image.set_data(b"\xff")
            page["/Resources"][NameObject("/XObject")] = DictionaryObject(
                {NameObject("/Im1"): writer._add_object(image)}
            )
            contents.set_data(b"q 1 0 0 1 0 0 cm /Im1 Do Q")
        else:
            contents.set_data(
                b"BT /F1 12 Tf 72 720 Td (" + text.encode("ascii") + b") Tj ET\n"
                + b" " * padding
            )
        page[NameObject("/Contents")] = writer._add_object(
            contents.flate_encode() if compressed else contents
        )
    if encrypted:
        writer.encrypt("synthetic-password")
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.fixture
def storage():
    with PrivateTemporaryStorage() as adapter:
        yield adapter


def test_valid_real_pdf_round_trip_and_opaque_metadata(storage):
    data = pdf_bytes(("Synthetic page one.", "Synthetic page two."))
    result = storage.store(data)
    assert UUID(result.file_id).version == 4
    assert result.size_bytes == len(data)
    assert result.page_count == 2
    assert result.character_count == len("Synthetic page one.Synthetic page two.")
    assert storage.read(result.file_id) == data
    assert sorted(p.name for p in storage._root.iterdir()) == [f"{result.file_id}.pdf"]
    assert not hasattr(result, "path")
    assert not hasattr(result, "text")
    assert not storage._root.is_relative_to(Path(__file__).resolve().parents[4])
    assert storage.delete(result.file_id)
    assert not storage.delete(result.file_id)
    with pytest.raises(StoredPDFNotFound):
        storage.read(result.file_id)


def test_random_filenames_and_separate_storage_instances(storage):
    data = pdf_bytes()
    first = storage.store(data)
    second = storage.store(data)
    assert first.file_id != second.file_id
    with PrivateTemporaryStorage() as other:
        assert storage._root != other._root
        with pytest.raises(StoredPDFNotFound):
            other.read(first.file_id)
        assert not other.delete(first.file_id)
    assert storage.read(first.file_id) == data


def test_no_filename_or_filesystem_path_argument(storage):
    with pytest.raises(TypeError):
        storage.store(pdf_bytes(), filename="../../private.pdf")
    with pytest.raises(TypeError):
        PrivateTemporaryStorage(root="public")
    with pytest.raises(PDFValidationError, match="Supply PDF bytes"):
        storage.store(Path("../../private.pdf"))


@pytest.mark.parametrize(
    "file_id",
    ["../private.pdf", "../../etc/passwd", r"C:\private.pdf", "/tmp/private.pdf",
     "", "private.pdf", "a" * 36, str(uuid4()).upper(), uuid4(), None,
     "00000000-0000-0000-0000-000000000000", f"{uuid4()}.pdf"],
)
def test_invalid_ids_rejected_for_every_operation(storage, file_id):
    for operation in (storage.read, storage.delete):
        with pytest.raises(InvalidStorageID) as error:
            operation(file_id)
        assert str(error.value) == "Invalid temporary file ID."


def test_unregistered_uuid_cannot_access_existing_file(storage):
    unknown = str(uuid4())
    foreign = storage._root / f"{unknown}.pdf"
    foreign.write_bytes(b"foreign synthetic data")
    try:
        with pytest.raises(StoredPDFNotFound):
            storage.read(unknown)
        assert not storage.delete(unknown)
        assert storage.cleanup_expired() == 0
        with pytest.raises(StorageError):
            storage.close()
        assert foreign.read_bytes() == b"foreign synthetic data"
    finally:
        foreign.unlink()


@pytest.mark.parametrize(
    ("data", "code"),
    [(b"", "invalid_signature"), (b"not a PDF", "invalid_signature"),
     (b"%PDF-1.7\nconfidential-synthetic-marker", "malformed_pdf"),
     (bytearray(b"%PDF-1.7"), "invalid_bytes")],
)
def test_invalid_files_leave_no_artifacts_or_document_errors(storage, data, code):
    with pytest.raises(PDFValidationError) as error:
        storage.store(data)
    assert error.value.code == code
    assert "confidential-synthetic-marker" not in str(error.value)
    assert not list(storage._root.iterdir())


def test_size_limit_checked_before_parser(storage, monkeypatch):
    def unexpected_parser(*args, **kwargs):
        pytest.fail("Oversized input reached PDF parser")

    monkeypatch.setattr(service, "PdfReader", unexpected_parser)
    with pytest.raises(PDFValidationError) as error:
        storage.store(b"%PDF-" + b"x" * (service.MAX_FILE_BYTES - 4))
    assert error.value.code == "file_too_large"
    assert not list(storage._root.iterdir())


def test_exact_file_size_boundary_uses_real_pdf(storage):
    # Pad an unused metadata string, keeping xref offsets and EOF valid.
    writer = PdfWriter(BytesIO(pdf_bytes()))
    writer.add_metadata({"/SyntheticPadding": ""})
    output = BytesIO()
    writer.write(output)
    padding = service.MAX_FILE_BYTES - len(output.getvalue())
    writer.add_metadata({"/SyntheticPadding": "x" * padding})
    output = BytesIO()
    writer.write(output)
    data = output.getvalue()
    # The larger startxref changes the serialized length by a few decimal digits.
    padding -= len(data) - service.MAX_FILE_BYTES
    writer.add_metadata({"/SyntheticPadding": "x" * padding})
    output = BytesIO()
    writer.write(output)
    data = output.getvalue()
    assert len(data) == service.MAX_FILE_BYTES
    assert storage.store(data).size_bytes == service.MAX_FILE_BYTES
    with pytest.raises(PDFValidationError) as error:
        storage.store(data + b" ")
    assert error.value.code == "file_too_large"


@pytest.mark.parametrize("encrypted", [False, True])
def test_encrypted_or_textless_pdf_rejected(storage, encrypted):
    with pytest.raises(PDFValidationError) as error:
        storage.store(pdf_bytes(("",), encrypted=encrypted))
    assert error.value.code == ("encrypted_pdf" if encrypted else "no_text")
    assert not list(storage._root.iterdir())


def test_scanned_image_only_pdf_rejected(storage):
    with pytest.raises(PDFValidationError) as error:
        storage.store(pdf_bytes(image_only=True))
    assert error.value.code == "no_text"


def test_page_count_boundary(storage):
    assert storage.store(pdf_bytes(("Synthetic",) * 20)).page_count == 20
    with pytest.raises(PDFValidationError) as error:
        storage.store(pdf_bytes(("Synthetic",) * 21))
    assert error.value.code == "page_limit"


def test_zero_page_pdf_rejected(storage):
    output = BytesIO()
    PdfWriter().write(output)
    with pytest.raises(PDFValidationError) as error:
        storage.store(output.getvalue())
    assert error.value.code == "page_limit"


def test_character_limit_on_one_page_and_across_pages(storage):
    assert storage.store(pdf_bytes(("x" * 100_000,))).character_count == 100_000
    for texts in (("x" * 100_001,), ("x" * 50_001, "x" * 50_000)):
        with pytest.raises(PDFValidationError) as error:
            storage.store(pdf_bytes(texts))
        assert error.value.code == "text_limit"


@pytest.mark.parametrize("compressed", [False, True])
def test_oversized_content_rejected_before_extraction(storage, monkeypatch, compressed):
    data = pdf_bytes(padding=service.MAX_STREAM_BYTES, compressed=compressed)

    def unexpected_extract(*args, **kwargs):
        pytest.fail("Oversized content reached text extraction")

    monkeypatch.setattr("pypdf._page.PageObject.extract_text", unexpected_extract)
    configuration = get_configuration()
    with pytest.raises(PDFValidationError) as error:
        storage.store(data)
    assert error.value.code == "parser_limit"
    assert get_configuration() == configuration
    assert not list(storage._root.iterdir())


def test_document_decoded_budget_across_pages(storage):
    with pytest.raises(PDFValidationError) as error:
        storage.store(pdf_bytes(("Synthetic",) * 5, padding=1_800_000, compressed=True))
    assert error.value.code == "parser_limit"


def pdf_with_form(*, text: str = "Synthetic form text", padding: int = 0) -> bytes:
    writer = PdfWriter(BytesIO(pdf_bytes()))
    page = writer.pages[0]
    form = DecodedStreamObject()
    form.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Form"),
            NameObject("/BBox"): ArrayObject([NumberObject(n) for n in (0, 0, 612, 792)]),
            NameObject("/Resources"): page["/Resources"],
        }
    )
    form.set_data(b"BT /F1 12 Tf (" + text.encode("ascii") + b") Tj ET\n" + b" " * padding)
    # Keep form resources separate from the page's XObject map, avoiding a cycle.
    form[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): page["/Resources"]["/Font"]}
    )
    page["/Resources"][NameObject("/XObject")] = DictionaryObject(
        {NameObject("/Fm1"): writer._add_object(form.flate_encode())}
    )
    contents = DecodedStreamObject()
    contents.set_data(b"BT /F1 12 Tf (Synthetic page text) Tj ET\n/Fm1 Do")
    page[NameObject("/Contents")] = writer._add_object(contents)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_valid_form_pdf_and_swallowed_visitor_limit(storage):
    assert storage.store(pdf_with_form()).character_count > 0
    with pytest.raises(PDFValidationError) as error:
        storage.store(pdf_with_form(text="x" * 100_001))
    assert error.value.code == "text_limit"


def test_oversized_form_stream_rejected_before_extraction(storage, monkeypatch):
    data = pdf_with_form(padding=service.MAX_STREAM_BYTES)

    def unexpected_extract(*args, **kwargs):
        pytest.fail("Oversized form reached text extraction")

    monkeypatch.setattr("pypdf._page.PageObject.extract_text", unexpected_extract)
    with pytest.raises(PDFValidationError) as error:
        storage.store(data)
    assert error.value.code == "parser_limit"


def test_content_array_budget(storage):
    writer = PdfWriter(BytesIO(pdf_bytes()))
    streams = ArrayObject()
    for _ in range(65):
        stream = DecodedStreamObject()
        stream.set_data(b" ")
        streams.append(writer._add_object(stream))
    writer.pages[0][NameObject("/Contents")] = streams
    output = BytesIO()
    writer.write(output)
    with pytest.raises(PDFValidationError) as error:
        storage.store(output.getvalue())
    assert error.value.code == "parser_limit"


def test_exclusive_creation_does_not_overwrite(storage, monkeypatch):
    fixed = uuid4()
    monkeypatch.setattr(service, "uuid4", lambda: fixed)
    first = storage.store(pdf_bytes(("First synthetic filing",)))
    with pytest.raises(StorageError):
        storage.store(pdf_bytes(("Second synthetic filing",)))
    assert storage.read(first.file_id) == pdf_bytes(("First synthetic filing",))


def test_failed_write_removes_partial_file(storage, monkeypatch):
    original_fdopen = os.fdopen

    class FailedOutput:
        def __init__(self, descriptor):
            self.output = original_fdopen(descriptor, "wb")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.output.close()

        def write(self, data):
            self.output.write(data[:10])
            raise OSError("Synthetic disk failure")

    monkeypatch.setattr(service.os, "fdopen", lambda fd, mode: FailedOutput(fd))
    with pytest.raises(StorageError):
        storage.store(pdf_bytes())
    assert not list(storage._root.iterdir())
    assert not storage._entries


def test_retention_sweep_and_expiry_read(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(service.time, "monotonic", lambda: now[0])
    with PrivateTemporaryStorage(retention_seconds=10) as adapter:
        first = adapter.store(pdf_bytes())
        now[0] = 105.0
        second = adapter.store(pdf_bytes())
        now[0] = 110.0
        assert adapter.cleanup_expired() == 1
        assert adapter.read(second.file_id) == pdf_bytes()
        assert not (adapter._root / f"{first.file_id}.pdf").exists()
        now[0] = 115.0
        with pytest.raises(StoredPDFNotFound):
            adapter.read(second.file_id)
        assert adapter.cleanup_expired() == 0
        assert not list(adapter._root.iterdir())


@pytest.mark.parametrize("retention", [0, -1, True, 1.5, float("inf")])
def test_invalid_retention(retention):
    with pytest.raises(ValueError):
        PrivateTemporaryStorage(retention_seconds=retention)


def test_context_close_removes_owned_directory_and_is_idempotent():
    with PrivateTemporaryStorage() as adapter:
        result = adapter.store(pdf_bytes())
        root = adapter._root
    assert not root.exists()
    adapter.close()
    with pytest.raises(StorageError):
        adapter.read(result.file_id)
    with pytest.raises(StorageError):
        adapter.store(pdf_bytes())


def test_context_cleanup_on_exception():
    with pytest.raises(RuntimeError, match="Synthetic failure"):
        with PrivateTemporaryStorage() as adapter:
            adapter.store(pdf_bytes())
            root = adapter._root
            raise RuntimeError("Synthetic failure")
    assert not root.exists()


def test_replaced_file_identity_rejected_without_cross_path_deletion(storage, tmp_path):
    result = storage.store(pdf_bytes())
    path = storage._root / f"{result.file_id}.pdf"
    original = tmp_path / "original.pdf"
    path.rename(original)
    path.write_bytes(pdf_bytes())
    try:
        for operation in (storage.read, storage.delete):
            with pytest.raises(StorageError):
                operation(result.file_id)
        assert path.exists()
        assert original.read_bytes() == pdf_bytes()
    finally:
        path.unlink()
        original.rename(path)


def test_hardlink_rejected(storage, tmp_path):
    result = storage.store(pdf_bytes())
    path = storage._root / f"{result.file_id}.pdf"
    alias = tmp_path / "alias.pdf"
    os.link(path, alias)
    try:
        with pytest.raises(StorageError):
            storage.read(result.file_id)
        with pytest.raises(StorageError):
            storage.delete(result.file_id)
        assert alias.exists()
    finally:
        alias.unlink()


def test_symlink_rejected_without_touching_target(storage, tmp_path):
    result = storage.store(pdf_bytes())
    path = storage._root / f"{result.file_id}.pdf"
    original = tmp_path / "original.pdf"
    target = tmp_path / "outside.pdf"
    target.write_bytes(pdf_bytes())
    path.rename(original)
    try:
        try:
            path.symlink_to(target)
        except OSError:
            pytest.skip("Host does not permit symlink creation")
        for operation in (storage.read, storage.delete):
            with pytest.raises(StorageError):
                operation(result.file_id)
        assert target.read_bytes() == pdf_bytes()
    finally:
        if path.is_symlink():
            path.unlink()
        original.rename(path)


def test_replaced_root_rejected(storage, tmp_path):
    original_root = storage._root
    saved_root = tmp_path / "saved-root"
    original_root.rename(saved_root)
    original_root.mkdir()
    try:
        with pytest.raises(StorageError):
            storage.store(pdf_bytes())
        with pytest.raises(StorageError):
            storage.cleanup_expired()
        assert not list(original_root.iterdir())
    finally:
        original_root.rmdir()
        saved_root.rename(original_root)


def test_windows_reparse_points_are_treated_as_links():
    class ReparseStat:
        st_mode = stat.S_IFDIR
        st_file_attributes = stat.FILE_ATTRIBUTE_REPARSE_POINT

    assert service._is_link(ReparseStat())


@pytest.mark.skipif(os.name == "nt", reason="Windows chmod does not establish POSIX privacy")
def test_posix_private_modes(storage):
    result = storage.store(pdf_bytes())
    assert stat.S_IMODE(storage._root.stat().st_mode) == 0o700
    assert stat.S_IMODE((storage._root / f"{result.file_id}.pdf").stat().st_mode) == 0o600
