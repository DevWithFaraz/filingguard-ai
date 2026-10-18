"""Traceable court-rule research records that cannot enable a runtime check."""

import json
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator, model_validator


class ReferenceCourtRuleSource(BaseModel):
    """An official source assessed for a possible future profile, never an active rule."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    title: str = Field(min_length=1)
    official_source_url: AnyHttpUrl
    source_locator: str = Field(min_length=1)
    issued_on: date
    source_checked_on: date
    court_scope: str = Field(min_length=1)
    judge_scope: str | None
    filing_scope: str = Field(min_length=1)
    trigger_summary: str = Field(min_length=1)
    requirement_summary: str = Field(min_length=1)
    current_effective_status: Literal["unconfirmed"]
    applicability_status: Literal["requires_case_scope_confirmation", "not_a_disclosure_rule"]
    activation_status: Literal["reference_only"]
    runtime_profile_id: None = None
    activation_blockers: tuple[str, ...] = Field(min_length=1)

    @field_validator("official_source_url")
    @classmethod
    def official_source_uses_https(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        if value.scheme != "https":
            raise ValueError("Official rule sources must use HTTPS")
        return value

    @model_validator(mode="after")
    def checked_after_issue_and_never_active(self):
        if self.source_checked_on < self.issued_on:
            raise ValueError("Source cannot be checked before it was issued")
        if self.runtime_profile_id is not None:
            raise ValueError("Reference-only source records cannot have a runtime profile")
        return self


_REFERENCE_SOURCE_IDS = (
    "us-ohsd-jlg-ai-2025-10-21",
    "us-txs-general-order-2025-04",
)
_REFERENCE_SOURCE_DIRECTORY = (
    Path(__file__).parents[2] / "resources" / "courts" / "reference-only"
)


def load_reference_source(source_id: str) -> ReferenceCourtRuleSource:
    """Load an allowlisted research record without making it available to intake."""

    if source_id not in _REFERENCE_SOURCE_IDS:
        raise ValueError("Unsupported court-rule reference source")
    path = _REFERENCE_SOURCE_DIRECTORY / f"{source_id}.json"
    record = ReferenceCourtRuleSource.model_validate(json.loads(path.read_text(encoding="utf-8")))
    if record.id != source_id:
        raise ValueError("Court-rule reference source identity mismatch")
    return record


def load_reference_sources() -> tuple[ReferenceCourtRuleSource, ...]:
    """Return the reviewed, non-active sources in a deterministic order."""

    return tuple(load_reference_source(source_id) for source_id in _REFERENCE_SOURCE_IDS)
