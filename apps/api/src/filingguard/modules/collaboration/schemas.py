"""Schemas for finding collaboration, reviewer roles, and status sign-off."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, field_validator

from filingguard.modules.analyses.schemas import Contract

ReviewerRole = Literal[
    "lead_attorney",
    "associate_reviewer",
    "paralegal",
    "court_clerk",
    "auditor",
]

DispositionStatus = Literal[
    "open",
    "accepted",
    "dismissed",
    "needs_review",
]


class FindingCommentCreate(Contract):
    author_name: Annotated[str, Field(min_length=1, max_length=64)]
    author_role: Annotated[str, Field(min_length=1, max_length=64)]
    content: Annotated[str, Field(min_length=1, max_length=2000)]

    @field_validator("content")
    @classmethod
    def clean_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Comment content cannot be blank")
        return cleaned


class FindingCommentResponse(Contract):
    id: UUID
    analysis_id: UUID
    finding_id: UUID
    author_name: str
    author_role: str
    content: str
    created_at: datetime


class FindingDispositionRequest(Contract):
    status: DispositionStatus
    rationale: Annotated[str, Field(min_length=1, max_length=1000)]
    reviewer_name: Annotated[str, Field(min_length=1, max_length=64)]
    reviewer_role: Annotated[str, Field(min_length=1, max_length=64)]


class FindingDispositionResponse(Contract):
    finding_id: UUID
    status: str
    disposition_metadata: dict
