"""Rebuild the curated PDF with bundled ReportLab, never an API dependency.

Run with the Python executable returned by load_workspace_dependencies.
Offsets are half-open Unicode character offsets into concatenated pypdf page
text, without an added page separator. Filing and extracted text have different
offset spaces. No legal validation or manifest mutation happens here.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path

import pypdf
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "data" / "demo" / "curated-v1"
FONT = "Times-Roman"
FONT_SIZE = 11
LEADING = 15
MARGIN = 54


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def wrapped_lines(text: str, width: float) -> list[str]:
    """Wrap at whitespace only, preserving every word and punctuation mark."""
    lines = []
    for paragraph in text.splitlines():
        current = ""
        for word in paragraph.split():
            if stringWidth(word, FONT, FONT_SIZE) > width:
                raise ValueError("A filing word exceeds the printable width")
            candidate = f"{current} {word}" if current else word
            if current and stringWidth(candidate, FONT, FONT_SIZE) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    return lines


def build(fixture_root: Path) -> dict:
    filing_bytes = (fixture_root / "filing.txt").read_bytes()
    filing = filing_bytes.decode("utf-8")
    if not filing.strip():
        raise ValueError("The curated filing must not be empty")
    # Standard PDF fonts cannot encode arbitrary Unicode; fail before losing text.
    filing.encode("cp1252")
    stream = io.BytesIO()
    width, height = letter
    canvas = Canvas(stream, pagesize=letter, invariant=1, pageCompression=1)
    canvas.setTitle("FilingGuard AI curated synthetic filing")
    canvas.setAuthor("FilingGuard AI")
    canvas.setCreator("scripts/build_demo_pdf.py")
    canvas.setFont(FONT, FONT_SIZE)
    y = height - MARGIN
    for line in wrapped_lines(filing, width - 2 * MARGIN):
        if y < MARGIN:
            canvas.showPage()
            canvas.setFont(FONT, FONT_SIZE)
            y = height - MARGIN
        if line:
            canvas.drawString(MARGIN, y, line)
        y -= LEADING
    canvas.save()
    pdf_bytes = stream.getvalue()
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes), strict=True)
    page_texts = [page.extract_text() for page in reader.pages]
    extracted = "".join(page_texts)
    if filing.split() != extracted.split():
        raise ValueError("PDF extraction changed the filing words")
    if not 1 <= len(page_texts) <= 20 or len(pdf_bytes) > 10 * 1024 * 1024:
        raise ValueError("PDF exceeds intake page/byte budgets")
    if len(extracted) > 100_000:
        raise ValueError("PDF exceeds the intake text budget")
    pages = []
    start = 0
    for number, text in enumerate(page_texts, 1):
        pages.append({"page_number": number, "start": start, "end": start + len(text)})
        start += len(text)
    extraction = {
        "schema_version": 1,
        "method": "pypdf.extract_text",
        "pypdf_version": pypdf.__version__,
        "filing_sha256": sha256(filing_bytes),
        "pdf_sha256": sha256(pdf_bytes),
        "text_sha256": sha256(extracted.encode("utf-8")),
        "text": extracted,
        "pages": pages,
    }
    (fixture_root / "filing.pdf").write_bytes(pdf_bytes)
    (fixture_root / "pdf-extraction.json").write_text(
        json.dumps(extraction, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    return extraction


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-root", type=Path, default=DEFAULT_ROOT)
    result = build(parser.parse_args().fixture_root)
    print(f"Built curated PDF: {len(result['pages'])} pages; SHA-256 {result['pdf_sha256']}")
