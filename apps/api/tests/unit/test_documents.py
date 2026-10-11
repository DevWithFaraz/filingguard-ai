from io import BytesIO
from pathlib import Path

import pytest
from pydantic import ValidationError
from pypdf import PdfReader, PdfWriter

from filingguard.integrations.storage.service import PDFValidationError
from filingguard.modules.documents.extraction import extract_text
from filingguard.modules.documents.schemas import ExtractedDocument
from filingguard.modules.documents.service import extract_pdf
from filingguard.modules.privacy.service import mask_excerpt

PDF = Path(__file__).resolve().parents[4] / "data/demo/curated-v1/filing.pdf"


def test_original_unicode_paragraphs_and_whitespace_are_not_normalized():
    original = "  A \U0001f600 claim.\ncontinued line\n\n  Second paragraph.  \n"
    document = extract_text(original)
    assert document.text == original
    assert len(document.paragraphs) == 2
    for paragraph in document.paragraphs:
        assert original[paragraph.start : paragraph.end] == paragraph.text
        assert paragraph.page_number is None
    with pytest.raises(ValidationError):
        ExtractedDocument.model_validate({**document.model_dump(), "text_sha256": "0" * 64})


@pytest.mark.parametrize(
    "value",
    ["", "   ", "x" * 100001, "a\x00b", "bad\ud800"],
    ids=["empty", "blank", "too-long", "nul", "invalid-unicode"],
)
def test_invalid_text_rejected(value):
    with pytest.raises(PDFValidationError):
        extract_text(value)


def test_real_worker_pdf_offsets_pages_and_no_parent_parse():
    document = extract_pdf(PDF.read_bytes())
    assert document.pages
    assert document.method == "pypdf-bounded-v1"
    for paragraph in document.paragraphs:
        assert document.text[paragraph.start : paragraph.end] == paragraph.text
        assert paragraph.page_number is not None


def test_real_worker_rejects_scanned_and_encrypted_and_malformed_input():
    for encrypted in (False, True):
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        if encrypted:
            writer.encrypt("synthetic-password")
        stream = BytesIO()
        writer.write(stream)
        with pytest.raises(PDFValidationError) as error:
            extract_pdf(stream.getvalue())
        assert error.value.code == ("encrypted_pdf" if encrypted else "no_text")
    with pytest.raises(PDFValidationError) as error:
        extract_pdf(b"%PDF-1.7\nSYNTHETIC_PRIVATE_SENTINEL")
    assert "SYNTHETIC_PRIVATE_SENTINEL" not in str(error.value)


def test_timeout_kills_worker_and_returns_safe_fallback():
    with pytest.raises(PDFValidationError) as error:
        extract_pdf(PDF.read_bytes(), timeout=0.001)
    assert error.value.code == "parser_timeout"


def test_blank_page_within_text_pdf_keeps_page_positions_and_warning():
    writer = PdfWriter()
    writer.add_page(PdfReader(PDF).pages[0])
    writer.add_blank_page(width=612, height=792)
    writer.add_page(PdfReader(PDF).pages[0])
    stream = BytesIO()
    writer.write(stream)
    document = extract_pdf(stream.getvalue())
    blank = document.pages[1]
    assert blank.warning == "no_text"
    assert blank.start == blank.end
    assert {paragraph.page_number for paragraph in document.paragraphs} == {1, 3}
    assert document.text[blank.start - 1 : blank.end + 1] == "\f\f"


def test_spawn_failure_is_sanitized_and_child_environment_excludes_secrets(monkeypatch):
    captured = []
    monkeypatch.setenv("GROQ_API_KEY", "SYNTHETIC_PRIVATE_SENTINEL")

    def unavailable(*args, **kwargs):
        captured.append(kwargs["env"])
        raise OSError("SYNTHETIC_PRIVATE_SENTINEL")

    monkeypatch.setattr("filingguard.modules.documents.service.subprocess.Popen", unavailable)
    with pytest.raises(PDFValidationError) as error:
        extract_pdf(PDF.read_bytes())
    assert error.value.code == "parser_unavailable"
    assert "SYNTHETIC_PRIVATE_SENTINEL" not in str(error.value)
    assert "GROQ_API_KEY" not in captured[0]


def test_provider_masking_and_clipped_identifiers_preserve_codepoint_mapping():
    text = "\U0001f600 SSN 123-45-6789, account 123456789012 and DOB 2000-01-02. user@example.com"
    masked = mask_excerpt(text, 0, len(text))
    assert len(masked.text) == len(text)
    for value in ("123-45-6789", "123456789012", "2000-01-02", "user@example.com"):
        assert value not in masked.text
    left = text.index("123-45-6789") + 4
    clipped = mask_excerpt(text, left, left + 4)
    assert clipped.text == "****"
    assert clipped.detections[0].start < left


def test_citation_numbers_and_negation_are_not_masked():
    text = "Brown, 347 U.S. 483 (1954), does not establish this claim."
    assert mask_excerpt(text, 0, len(text)).text == text


@pytest.mark.parametrize("suffix", [".", ". ", ".\n", ".,", "...", "?", ".example"])
def test_email_before_sentence_punctuation_is_masked_without_offset_changes(suffix):
    text = "Contact test@example.com" + suffix
    masked = mask_excerpt(text, 0, len(text))
    assert "test@example.com" not in masked.text
    assert len(masked.text) == len(text)
    left = text.index("example.com")
    assert set(mask_excerpt(text, left, left + len("example.com")).text) == {"*"}
