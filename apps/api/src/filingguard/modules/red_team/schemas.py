"""Schemas for Legal Red-Team Mode (FR-240 through FR-245)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from filingguard.modules.analyses.schemas import Contract


class RedTeamWeakness(Contract):
    """An adversarial weakness synthesized exclusively from existing analysis findings."""

    id: UUID
    vulnerability_type: Literal[
        "misrepresented_authority",
        "unverified_citation",
        "altered_quotation",
        "privacy_exposure",
        "court_rule_violation",
        "unsupported_claim",
        "unresolved_authority",
    ]
    severity: Literal["critical", "high", "medium", "low"]
    title: str = Field(min_length=1, max_length=255)
    challenge_theory: str = Field(min_length=1)
    impact_summary: str = Field(min_length=1)
    remediation_recommendation: str = Field(min_length=1)
    linked_finding_ids: list[UUID] = Field(default_factory=list, max_length=100)
    linked_citation_ids: list[UUID] = Field(default_factory=list, max_length=100)
    linked_claim_ids: list[UUID] = Field(default_factory=list, max_length=100)
    linked_quote_ids: list[UUID] = Field(default_factory=list, max_length=100)


class RedTeamResponse(Contract):
    """Grounded adversarial critique of filing vulnerabilities."""

    analysis_id: UUID
    generated_at: datetime
    weaknesses: list[RedTeamWeakness] = Field(default_factory=list, max_length=50)
    summary: str = Field(min_length=1)
    total_weaknesses: int = Field(ge=0)
    critical_count: int = Field(ge=0)
    high_count: int = Field(ge=0)
    medium_count: int = Field(ge=0)
    low_count: int = Field(ge=0)
    limitation: str = (
        "Red-Team Mode synthesizes review vulnerabilities exclusively from existing "
        "findings and evidence. It identifies adversarial risks to assist human "
        "review, not legal strategy or legal advice."
    )

