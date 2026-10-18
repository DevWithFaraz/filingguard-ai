"""Schemas for Finding-grounded Q&A (FR-260 through FR-264)."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from filingguard.modules.analyses.schemas import Contract


class GroundedQuestionRequest(Contract):
    question: Annotated[str, Field(min_length=1, max_length=500, pattern=r"\S")]


class GroundedAnswerResponse(Contract):
    analysis_id: UUID
    finding_id: UUID
    question: str
    answer: str
    status: Literal["answered", "refused", "no_evidence"] = "answered"
    refusal_reason: Literal["broad_legal_advice", "out_of_scope", "none"] = "none"
    evidence_record_ids: list[UUID] = Field(default_factory=list)
    source_authorities: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    method_version: str = "grounded-qa-v1"
    created_at: datetime


class GroundedQuestionHistory(Contract):
    analysis_id: UUID
    finding_id: UUID
    questions: list[GroundedAnswerResponse] = Field(default_factory=list)
    count: int = 0
    limit: int = 20
