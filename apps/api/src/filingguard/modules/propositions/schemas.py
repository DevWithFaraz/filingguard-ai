"""Strict model output and exact, original-source passage references."""

from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class SourcePassage:
    id: str
    text: str
    start: int
    end: int
    snapshot_sha256: str
    truncated: bool = False


class EvidenceCitation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    passage_id: str = Field(min_length=1, max_length=80)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    excerpt: str = Field(min_length=1, max_length=12000)


class ModelVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    status: Literal[
        "supported", "partially_supported", "unclear", "misrepresented", "insufficient_source"
    ]
    explanation: str = Field(min_length=1, max_length=2000)
    confidence: Literal["unknown", "low", "medium", "high"]
    evidence: Annotated[list[EvidenceCitation], Field(max_length=3)]


class WireEvidenceCitation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    evidence_id: str = Field(min_length=1, max_length=100)


class WireModelVerdict(ModelVerdict):
    """The model selects immutable evidence units; the application binds source text."""

    evidence: Annotated[list[WireEvidenceCitation], Field(max_length=3)]


class WireBatchItem(WireModelVerdict):
    claim_id: Literal["claim-0", "claim-1"]


class WireBatchVerdicts(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    verdicts: Annotated[list[WireBatchItem], Field(min_length=2, max_length=2)]


@dataclass(frozen=True)
class GroundedVerdict:
    verdict: ModelVerdict
    model_version: str
    prompt_version: str
    method_version: str
    filing_truncated: bool
    elapsed_seconds: float
    prompt_tokens: int | None
    completion_tokens: int | None
    token_quota: dict[str, int | float] | None = None
    source_passages: tuple[SourcePassage, ...] | None = None
    request_group: str | None = None
    batch_size: int = 1
