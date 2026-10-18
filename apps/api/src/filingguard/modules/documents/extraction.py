import re
from hashlib import sha256

from filingguard.integrations.storage.service import PDFValidationError, _parse_pdf
from filingguard.modules.documents.schemas import ExtractedDocument, PageSpan, Paragraph


def segment(text: str, pages: list[PageSpan]) -> list[Paragraph]:
    paragraphs = []
    spans = pages or [PageSpan(page_number=1, start=0, end=len(text))]
    for page in spans:
        value = text[page.start : page.end]
        bounds, cursor = [], 0
        for match in re.finditer(r"\n[ \t]*\n+", value):
            bounds.append((cursor, match.start()))
            cursor = match.end()
        bounds.append((cursor, len(value)))
        for left, right in bounds:
            raw = value[left:right]
            content = raw.strip()
            if not content:
                continue
            left += len(raw) - len(raw.lstrip())
            paragraphs.append(
                Paragraph(
                    paragraph_index=len(paragraphs),
                    page_number=page.page_number if pages else None,
                    start=page.start + left,
                    end=page.start + left + len(content),
                    text=content,
                )
            )
            if len(paragraphs) > 2000:
                raise PDFValidationError("segment_limit", "Document exceeds the paragraph limit.")
    return paragraphs


def detect_parsing_diagnostics(
    text: str, pages: list[PageSpan], paragraphs: list[Paragraph]
) -> list[str]:
    diagnostics: list[str] = []
    for page in pages:
        if page.warning == "no_text":
            diagnostics.append(
                f"Page {page.page_number} has no text; possible image or scan without OCR."
            )
        elif page.warning == "sparse_text":
            char_count = max(0, page.end - page.start)
            diagnostics.append(
                f"Page {page.page_number} has sparse text ({char_count} chars); partial scan."
            )
        elif page.warning == "replacement_characters":
            diagnostics.append(
                f"Page {page.page_number} has excessive replacement chars (\ufffd); degraded font."
            )

    if len(pages) >= 2:
        density = len(text.strip()) / len(pages)
        if density < 40:
            diagnostics.append(
                f"Low average character density ({int(density)} chars/page); possible image scan."
            )

    fused = [t for t in re.findall(r"[A-Za-z]{40,}", text)]
    if fused:
        sample = fused[0][:20]
        diagnostics.append(
            f"Detected abnormally long fused words ('{sample}...'); text flow may lack spacing."
        )

    if text.count("\ufffd") >= 5:
        diagnostics.append(
            f"Document contains {text.count('\ufffd')} unresolvable replacement characters."
        )

    return diagnostics[:20]


def extract_text(text: str) -> ExtractedDocument:
    if not isinstance(text, str) or not text.strip() or len(text) > 100000 or "\x00" in text:
        raise PDFValidationError("invalid_text", "Supply nonempty text up to 100,000 characters.")
    try:
        digest = sha256(text.encode("utf-8")).hexdigest()
    except UnicodeEncodeError:
        raise PDFValidationError("invalid_text", "Supply valid Unicode text.") from None
    paragraphs = segment(text, [])
    diagnostics = detect_parsing_diagnostics(text, [], paragraphs)
    return ExtractedDocument(
        text=text,
        input_sha256=digest,
        text_sha256=digest,
        pages=[],
        paragraphs=paragraphs,
        method="original-text-v1",
        diagnostics=diagnostics,
    )


def extract_pdf_in_worker(data: bytes) -> ExtractedDocument:
    texts = _parse_pdf(data)
    text = "\f".join(texts)
    if len(text) > 100000:
        raise PDFValidationError("text_limit", "PDF exceeds 100,000 extracted characters.")
    pages = []
    start = 0
    for number, value in enumerate(texts, 1):
        warning = (
            "no_text"
            if not value.strip()
            else "sparse_text"
            if len(value.strip()) < 20
            else "replacement_characters"
            if value.count("\ufffd") / len(value) > 0.02
            else None
        )
        pages.append(
            PageSpan(page_number=number, start=start, end=start + len(value), warning=warning)
        )
        start += len(value) + 1
    paragraphs = segment(text, pages)
    diagnostics = detect_parsing_diagnostics(text, pages, paragraphs)
    return ExtractedDocument(
        text=text,
        input_sha256=sha256(data).hexdigest(),
        text_sha256=sha256(text.encode("utf-8")).hexdigest(),
        pages=pages,
        paragraphs=paragraphs,
        method="pypdf-bounded-v1",
        diagnostics=diagnostics,
    )
