"""Table of Authorities audit records; comparison is not a filing-readiness verdict."""

from typing import Literal

from pydantic import Field

from filingguard.modules.analyses.schemas import Contract, Nonnegative

METHOD_VERSION = "toa-audit-v1"
LIMITATION = (
    "Table of Authorities detection is heuristic. Short forms, Id./supra, unnamed "
    "authorities, and non-reporter entries may be omitted. Page leaders are parsed "
    "only when present. Absence of a table is not a pass or a court-rule violation."
)


class ToaSpan(Contract):
    start: Nonnegative
    end: Nonnegative
    heading: Literal["table_of_authorities", "table_of_cases", "index_of_authorities"]


class ToaEntry(Contract):
    key: str = Field(min_length=1, max_length=300)
    display: str = Field(min_length=1, max_length=300)
    start: Nonnegative
    end: Nonnegative
    page_number: int | None = Field(default=None, ge=1, le=20)
    listed_pages: list[int] = Field(default_factory=list, max_length=32)
    kind: str = Field(min_length=1, max_length=40)


class ToaAudit(Contract):
    detected: bool
    span: ToaSpan | None = None
    table_entries: list[ToaEntry] = Field(default_factory=list, max_length=200)
    body_entries: list[ToaEntry] = Field(default_factory=list, max_length=200)
    missing_from_table: list[str] = Field(default_factory=list, max_length=200)
    extra_in_table: list[str] = Field(default_factory=list, max_length=200)
    bound_uncertain: bool = False
    limitation: str = LIMITATION
