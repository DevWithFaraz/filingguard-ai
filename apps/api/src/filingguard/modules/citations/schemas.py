"""Bounded local citation extraction contracts; offsets refer to original text."""

from typing import Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from filingguard.modules.analyses.schemas import Contract

EXTRACTION_LIMITATION = (
    "Local Eyecite reporter coverage is incomplete. A narrow numeric reporter heuristic may "
    "produce false positives; unrecognized formats may be missed. Extraction does not verify "
    "an authority, resolve short references, or check statutes."
)


class CitationVerificationMetadata(Contract):
    method: Literal["courtlistener-v4-v1", "cached-public-source-v1"] = "courtlistener-v4-v1"
    retrieved_at: AwareDatetime
    reason: str | None = Field(default=None, max_length=300)
    limitation: str | None = Field(default=None, max_length=1000)
    cached: bool = False
    cache_hit: bool = False
    cache_version: str | None = None


class CitationExtractionMetadata(Contract):
    method: Literal["eyecite-local-v1"] = "eyecite-local-v1"
    parser_version: str
    kind: Literal[
        "full_case",
        "short_case",
        "id",
        "supra",
        "reference",
        "law",
        "journal",
        "unknown",
        "reporter_candidate",
    ]
    support: Literal["recognized", "ambiguous", "unsupported", "unresolved_reference"]
    reporter_candidates: list[str] = Field(default_factory=list, max_length=16)
    warnings: list[Literal["cross_segment", "cross_page"]] = Field(default_factory=list)
    verification: CitationVerificationMetadata | None = None


class CitationOccurrence(Contract):
    raw_text: str
    normalized_text: str | None
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    extraction: CitationExtractionMetadata

    @model_validator(mode="after")
    def valid_span(self) -> Self:
        if self.end <= self.start or len(self.raw_text) != self.end - self.start:
            raise ValueError("Citation span must match raw text length")
        return self


class CitationExtraction(Contract):
    occurrences: list[CitationOccurrence] = Field(default_factory=list, max_length=200)
    detected_count: int = Field(ge=0)
    truncated: bool
    limitation: str

    @model_validator(mode="after")
    def valid_count(self) -> Self:
        if self.detected_count < len(self.occurrences):
            raise ValueError("Detected count cannot be below retained occurrences")
        if self.truncated != (self.detected_count > len(self.occurrences)):
            raise ValueError("Truncation must reflect omitted occurrences")
        return self
