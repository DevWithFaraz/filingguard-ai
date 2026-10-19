"""Schemas for saved client matters and case grouping."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator

from filingguard.modules.analyses.schemas import Contract


class MatterCreate(Contract):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    case_number: Annotated[str | None, Field(max_length=64)] = None
    client_id: Annotated[str | None, Field(max_length=64)] = None
    description: Annotated[str | None, Field(max_length=2000)] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Matter name cannot be empty or whitespace")
        return cleaned


class MatterUpdate(Contract):
    name: Annotated[str | None, Field(min_length=1, max_length=255)] = None
    case_number: Annotated[str | None, Field(max_length=64)] = None
    client_id: Annotated[str | None, Field(max_length=64)] = None
    description: Annotated[str | None, Field(max_length=2000)] = None


class MatterSummary(Contract):
    id: UUID
    name: str
    case_number: str | None = None
    client_id: str | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class MatterAnalysisItem(Contract):
    analysis_id: UUID
    document_name: str
    mode: str
    status: str
    created_at: datetime


class MatterDetail(MatterSummary):
    analyses: list[MatterAnalysisItem] = Field(default_factory=list)


class MatterAssignRequest(Contract):
    matter_id: UUID | None = None
