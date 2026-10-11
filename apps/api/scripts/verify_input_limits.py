"""Measure accepted maxima and fail-closed boundaries using synthetic/public fixtures."""

import json
import time
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from filingguard.integrations.storage.service import MAX_FILE_BYTES, PDFValidationError
from filingguard.modules.documents.extraction import extract_text
from filingguard.modules.documents.service import extract_pdf

ROOT = Path(__file__).resolve().parents[3]


def pdf(pages):
    writer = PdfWriter()
    page = PdfReader(ROOT / "data/demo/curated-v1/filing.pdf").pages[0]
    for _ in range(pages):
        writer.add_page(page)
    stream = BytesIO()
    writer.write(stream)
    return stream.getvalue()


def main():
    rows = []
    twenty = pdf(20)
    # A legal PDF comment before startxref pads bytes without expanding page streams.
    prefix, suffix = twenty.rsplit(b"startxref", 1)
    padding = MAX_FILE_BYTES - len(twenty)
    maximum_pdf = prefix + b"%" + b"x" * (padding - 2) + b"\nstartxref" + suffix
    maximum_text = "\n\n".join(["Synthetic maximum input. " + "x" * 23] * 2000) + "xx"
    assert len(maximum_pdf) == MAX_FILE_BYTES and len(maximum_text) == 100000
    for label, function, value, expected in (
        ("maximum_text", extract_text, maximum_text, None),
        ("maximum_pdf", extract_pdf, maximum_pdf, None),
        ("over_characters", extract_text, maximum_text + "x", "invalid_text"),
        ("over_paragraphs", extract_text, "\n\n".join(["synthetic"] * 2001), "segment_limit"),
        ("over_pages", extract_pdf, pdf(21), "page_limit"),
        ("over_bytes", extract_pdf, maximum_pdf + b"x", "file_too_large"),
    ):
        began = time.monotonic()
        try:
            document = function(value)
            assert expected is None, label
            if label == "maximum_text":
                assert len(document.paragraphs) == 2000
            else:
                assert len(document.pages) == 20
            row = {
                "case": label,
                "status": "accepted",
                "characters": len(document.text),
                "paragraphs": len(document.paragraphs),
                "pages": len(document.pages),
            }
        except PDFValidationError as error:
            assert error.code == expected, (label, error.code, expected)
            row = {"case": label, "status": "rejected", "code": error.code}
        row["elapsed_seconds"] = round(time.monotonic() - began, 3)
        rows.append(row)
    receipt = {
        "checked_at": datetime.now(UTC).isoformat(),
        "scope": "Windows bounded extraction; trusted synthetic/public fixtures; no provider calls",
        "maximum_file_bytes": MAX_FILE_BYTES,
        "cases": rows,
    }
    target = ROOT / ".runtime/input-limit-verification.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
