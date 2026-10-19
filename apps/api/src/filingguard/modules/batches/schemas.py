"""Schemas for batch filing review and progress tracking."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator

from filingguard.modules.analyses.schemas import Contract


class BatchDocumentItem(Contract):
    document_name: Annotated[str, Field(min_length=1, max_length=255)]
    text: Annotated[str, Field(min_length=1, max_length=500000)]
    court_profile_id: str = "unverified"
    ai_used: bool = False


class BatchCreate(Contract):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    documents: Annotated[list[BatchDocumentItem], Field(min_length=1, max_length=10)]

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Batch name cannot be blank")
        return cleaned


class BatchItemSummary(Contract):
    id: UUID
    analysis_id: UUID
    document_name: str
    status: str
    created_at: datetime


class BatchSummary(Contract):
    id: UUID
    name: str
    status: str
    total_count: int
    completed_count: int
    failed_count: int
    created_at: datetime
    updated_at: datetime


class BatchDetail(BatchSummary):
    items: list[BatchItemSummary] = Field(default_factory=list)
