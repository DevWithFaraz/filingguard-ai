"""Typed schemas for CourtListener citation lookup and authority data."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from filingguard.modules.analyses.schemas import CitationStatus

NOT_FOUND_LIMITATION = (
    "CourtListener coverage is incomplete. An unresolved citation in CourtListener "
    "does not conclusively prove that an authority is fabricated."
)
AMBIGUOUS_LIMITATION = (
    "Multiple authorities matched this citation in CourtListener; human review "
    "is required to disambiguate the authority."
)
INVALID_LIMITATION = "Citation format was rejected as invalid by CourtListener."
UNAVAILABLE_LIMITATION = (
    "Citation verification service is temporarily unavailable. Automated checks "
    "could not be completed."
)
MISSING_TEXT_LIMITATION = (
    "Opinion text is not available in CourtListener for this authority; metadata "
    "and provenance were retrieved, but source passages could not be loaded."
)
DISSENT_ONLY_LIMITATION = (
    "Only dissenting or concurring opinions were found for this cluster; holding text "
    "is unavailable."
)


class CourtListenerCluster(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    case_name: str | None = None
    citation: str | None = None
    court: str | None = None
    year: int | None = None
    date_filed: str | None = None
    sub_opinions: list[int | str] = Field(default_factory=list)
    opinion_ids: list[int] = Field(default_factory=list)
    absolute_url: str | None = None
    source_url: str | None = None


class CourtListenerOpinion(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    cluster_id: int | None = None
    opinion_type: str | None = None
    author: str | None = None
    per_curiam: bool = False
    text: str | None = None
    text_field: str | None = None
    text_conversion: str | None = None
    text_sha256: str | None = None
    raw_sha256: str | None = None
    opinion_text_available: bool = False
    download_url: str | None = None
    source_url: str | None = None
    missing_text: bool = False


class CourtListenerResolvedAuthority(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cluster_id: int
    opinion_id: int | None = None
    case_name: str | None = None
    citation: str | None = None
    court: str | None = None
    year: int | None = None
    source_url: str | None = None
    opinion_text_available: bool = False
    opinion_text: str | None = None
    source_sha256: str | None = None
    retrieved_at: datetime | None = None
    source_metadata: dict = Field(default_factory=dict)


class CourtListenerLookupResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: CitationStatus
    query_text: str
    normalized_citation: str | None = None
    cluster: CourtListenerCluster | None = None
    clusters: list[CourtListenerCluster] = Field(default_factory=list)
    provider_status: int | None = None
    reason: str | None = None
    limitation: str | None = None
