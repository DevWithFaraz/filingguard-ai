"""Statute and regulation lookup contracts; absence is not fabrication."""

from enum import StrEnum
from typing import Literal

from pydantic import Field

from filingguard.modules.analyses.schemas import Contract

METHOD_VERSION = "statute-lookup-v1"
LIMITATION = (
    "Statute coverage is incomplete. Missing records do not prove fabrication. "
    "Timeout, 429, and 5xx are unavailable, never not-found."
)
UNCONFIGURED_REASON = (
    "No statute or regulation source is configured; those checks are unavailable."
)


class StatuteStatus(StrEnum):
    VERIFIED = "verified"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"
    VERSION_MISMATCH = "version_mismatch"
    INVALID = "invalid"


class LawIdentity(Contract):
    raw_text: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    normalized_key: str
    reporter: str
    title: str | None = None
    section: str
    jurisdiction: str
    cited_year: str | None = None
    kind: Literal["law", "statute_candidate"] = "law"


class StatuteLookupResult(Contract):
    status: StatuteStatus
    query_text: str
    reason: str
    jurisdiction: str | None = None
    version: str | None = None
    effective_date: str | None = None
    coverage_limitation: str = LIMITATION
    source_url: str | None = None
    method: Literal["statute-catalog-v1", "statute-http-v1", "statute-unconfigured-v1"] = (
        "statute-catalog-v1"
    )
