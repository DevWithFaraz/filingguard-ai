"""Original extraction spans use half-open Unicode code-point offsets."""

from hashlib import sha256
from typing import Literal, Self

from pydantic import Field, model_validator

from filingguard.modules.analyses.schemas import Contract


class Paragraph(Contract):
    paragraph_index: int = Field(ge=0)
    page_number: int | None = Field(default=None, ge=1, le=20)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str = Field(min_length=1, max_length=100000)


class PageSpan(Contract):
    page_number: int = Field(ge=1, le=20)
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    warning: Literal["no_text", "sparse_text", "replacement_characters"] | None = None


class ExtractedDocument(Contract):
    text: str = Field(min_length=1, max_length=100000)
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    pages: list[PageSpan] = Field(max_length=20)
    paragraphs: list[Paragraph] = Field(min_length=1, max_length=2000)
    method: Literal["original-text-v1", "pypdf-bounded-v1"]

    @model_validator(mode="after")
    def validate_spans(self) -> Self:
        if self.text_sha256 != sha256(self.text.encode("utf-8")).hexdigest():
            raise ValueError("Extracted snapshot hash mismatch")
        for index, paragraph in enumerate(self.paragraphs):
            if (
                paragraph.paragraph_index != index
                or (index > 0 and paragraph.start < self.paragraphs[index - 1].end)
                or paragraph.end > len(self.text)
                or paragraph.end <= paragraph.start
                or self.text[paragraph.start : paragraph.end] != paragraph.text
            ):
                raise ValueError("Paragraph span mismatch")
        cursor = 0
        for index, page in enumerate(self.pages):
            if (
                page.page_number != index + 1
                or page.start != cursor
                or not page.start <= page.end <= len(self.text)
            ):
                raise ValueError("Page span mismatch")
            if index < len(self.pages) - 1 and self.text[page.end : page.end + 1] != "\f":
                raise ValueError("Page separator mismatch")
            cursor = page.end + 1
        if self.pages and self.pages[-1].end != len(self.text):
            raise ValueError("Incomplete page coverage")
        for paragraph in self.paragraphs:
            if self.pages:
                if paragraph.page_number is None or paragraph.page_number > len(self.pages):
                    raise ValueError("Paragraph page missing")
                page = self.pages[paragraph.page_number - 1]
                if not page.start <= paragraph.start < paragraph.end <= page.end:
                    raise ValueError("Paragraph is outside its page")
            elif paragraph.page_number is not None:
                raise ValueError("Text has no PDF page numbers")
        return self
