"""Domain contracts: execution, coverage and legal verdicts are separate signals."""

from enum import StrEnum
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictBool, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class AnalysisStatus(StrEnum):
    NOT_RUN = "not_run"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class StageStatus(StrEnum):
    NOT_RUN = "not_run"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
    SKIPPED = "skipped"


class StageName(StrEnum):
    DOCUMENT = "document"
    CITATIONS = "citations"
    CLAIMS = "claims"
    PROPOSITIONS = "propositions"
    QUOTES = "quotes"
    PRIVACY = "privacy"
    COURT_RULES = "court_rules"
    TABLE_OF_AUTHORITIES = "table_of_authorities"
    STATUTES = "statutes"


class CitationStatus(StrEnum):
    NOT_RUN = "not_run"
    VERIFIED = "verified"
    NOT_FOUND = "not_found"
    INVALID = "invalid"
    AMBIGUOUS = "ambiguous"
    UNAVAILABLE = "unavailable"


class PropositionStatus(StrEnum):
    NOT_RUN = "not_run"
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNCLEAR = "unclear"
    MISREPRESENTED = "misrepresented"
    INSUFFICIENT_SOURCE = "insufficient_source"
    UNAVAILABLE = "unavailable"


class QuoteStatus(StrEnum):
    NOT_RUN = "not_run"
    EXACT = "exact"
    NORMALIZED = "normalized"
    CLOSE = "close"
    NOT_FOUND = "not_found"
    SOURCE_UNAVAILABLE = "source_unavailable"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingType(StrEnum):
    CITATION = "citation"
    CLAIM_SUPPORT = "claim_support"
    QUOTE = "quote"
    PRIVACY = "privacy"
    COURT_RULE = "court_rule"
    TABLE_OF_AUTHORITIES = "table_of_authorities"
    SYSTEM = "system"


class ReviewStatus(StrEnum):
    OPEN = "open"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"


class AnalysisMode(StrEnum):
    LIVE = "live"
    DEMO = "demo"


class RiskLevel(StrEnum):
    READY_FOR_REVIEW = "ready_for_review"
    NEEDS_REVIEW = "needs_review"
    HIGH_RISK = "high_risk"


Probability = Annotated[float, Field(ge=0, le=1, strict=True, allow_inf_nan=False)]
Nonnegative = Annotated[int, Field(ge=0, strict=True)]
Label = Annotated[str, Field(min_length=1, max_length=300, pattern=r"\S")]


class Confidence(Contract):
    level: Literal["unknown", "low", "medium", "high"] = "unknown"
    value: Probability | None = None
    method: Label | None = None
    calibrated: Literal[False] = False

    @model_validator(mode="after")
    def explain_number(self) -> Self:
        if self.value is not None and (self.method is None or self.level == "unknown"):
            raise ValueError("Numerical confidence needs a method and an explicit level")
        return self


class DocumentLocation(Contract):
    """Half-open offsets into original extracted text, measured in Unicode code points."""

    start: Nonnegative
    end: Nonnegative
    offset_unit: Literal["unicode_code_points"] = "unicode_code_points"
    page_number: Annotated[int, Field(ge=1, strict=True)] | None = None
    segment_id: UUID | None = None

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.end <= self.start:
            raise ValueError("Location must identify a nonempty forward span")
        return self


class Coverage(Contract):
    eligible: Nonnegative = 0
    evaluated: Nonnegative = 0
    unavailable: Nonnegative = 0
    pending: Nonnegative = 0
    truncated: StrictBool = False
    limitation: Label | None = None

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if self.evaluated + self.unavailable + self.pending != self.eligible:
            raise ValueError("Coverage counts must partition eligible checks")
        if self.truncated and self.limitation is None:
            raise ValueError("Truncated coverage needs a limitation")
        return self

    @property
    def complete(self) -> bool:
        return self.eligible > 0 and self.evaluated == self.eligible and not self.truncated


class StageState(Contract):
    name: StageName
    status: StageStatus = StageStatus.NOT_RUN
    reason: Label | None = None
    coverage: Coverage = Field(default_factory=Coverage)
    applicable: StrictBool = True

    @model_validator(mode="after")
    def explicit_failure(self) -> Self:
        if self.status == StageStatus.SKIPPED:
            if self.applicable or self.coverage.eligible or self.coverage.truncated:
                raise ValueError("Only inapplicable stages with no eligible checks may be skipped")
        elif not self.applicable:
            raise ValueError("Inapplicable stages must be explicitly skipped")
        if (
            self.status
            in {
                StageStatus.PARTIAL,
                StageStatus.UNAVAILABLE,
                StageStatus.FAILED,
                StageStatus.INTERRUPTED,
                StageStatus.SKIPPED,
            }
            and self.reason is None
        ):
            raise ValueError("Incomplete or skipped stages need a reason")
        if self.status == StageStatus.COMPLETED and (
            self.coverage.pending or self.coverage.unavailable or self.coverage.truncated
        ):
            raise ValueError("Incomplete coverage cannot be a completed stage")
        if self.status == StageStatus.NOT_RUN and self.coverage.evaluated:
            raise ValueError("Not-run stages cannot contain evaluated checks")
        return self


class CitationResult(Contract):
    citation_id: UUID
    status: CitationStatus = CitationStatus.NOT_RUN
    authority_id: UUID | None = None
    evidence_ids: list[UUID] = Field(default_factory=list)
    reason: Label | None = None

    @model_validator(mode="after")
    def grounded_verification(self) -> Self:
        if self.status == CitationStatus.VERIFIED and (
            self.authority_id is None or not self.evidence_ids
        ):
            raise ValueError("Verified citation needs an authority and retrieval evidence")
        if self.status == CitationStatus.UNAVAILABLE and self.reason is None:
            raise ValueError("Unavailable citation needs a reason, not a not-found verdict")
        return self


class PropositionResult(Contract):
    claim_id: UUID
    status: PropositionStatus = PropositionStatus.NOT_RUN
    evidence_ids: list[UUID] = Field(default_factory=list)
    confidence: Confidence = Field(default_factory=Confidence)
    explanation: Annotated[str, Field(max_length=4000)] | None = None
    ai_used: StrictBool = False
    model_version: Label | None = None
    prompt_version: Label | None = None

    @model_validator(mode="after")
    def grounded_verdict(self) -> Self:
        if self.status in {
            PropositionStatus.SUPPORTED,
            PropositionStatus.PARTIALLY_SUPPORTED,
            PropositionStatus.MISREPRESENTED,
        } and (not self.evidence_ids or not self.explanation):
            raise ValueError("Substantive support verdict needs evidence and explanation")
        if self.ai_used and (not self.model_version or not self.prompt_version):
            raise ValueError("AI-assisted results need model and prompt versions")
        if not self.ai_used and (self.model_version or self.prompt_version):
            raise ValueError("Model metadata requires explicit AI attribution")
        if self.status in {
            PropositionStatus.NOT_RUN,
            PropositionStatus.UNAVAILABLE,
            PropositionStatus.INSUFFICIENT_SOURCE,
        } and (self.confidence.level != "unknown" or self.confidence.value is not None):
            raise ValueError("Unexamined support cannot have favorable confidence")
        if self.explanation is not None and not self.explanation.strip():
            raise ValueError("Explanation must be nonblank")
        if (
            self.ai_used
            and self.status
            not in {
                PropositionStatus.NOT_RUN,
                PropositionStatus.UNAVAILABLE,
            }
            and not self.explanation
        ):
            raise ValueError("Evaluated AI results require an explanation")
        return self


class QuoteResult(Contract):
    quote_id: UUID
    status: QuoteStatus = QuoteStatus.NOT_RUN
    evidence_ids: list[UUID] = Field(default_factory=list)
    similarity: Probability | None = None
    method_version: Label | None = None

    @model_validator(mode="after")
    def sourced_match(self) -> Self:
        if self.status == QuoteStatus.EXACT and self.similarity not in {None, 1.0}:
            raise ValueError("Exact quote similarity, when supplied, must be one")
        if self.status in {QuoteStatus.EXACT, QuoteStatus.NORMALIZED, QuoteStatus.CLOSE} and (
            not self.evidence_ids or not self.method_version
        ):
            raise ValueError("Quote match needs source evidence and method version")
        if self.status in {QuoteStatus.NOT_RUN, QuoteStatus.SOURCE_UNAVAILABLE} and (
            self.similarity is not None
        ):
            raise ValueError("Unexamined quotations cannot have a similarity score")
        return self


class FindingRecord(Contract):
    id: UUID
    analysis_id: UUID
    type: FindingType
    severity: Severity
    title: Label
    description: Annotated[str, Field(min_length=1, max_length=8000)]
    review_status: ReviewStatus = ReviewStatus.OPEN
    location: DocumentLocation | None = None
    evidence_ids: list[UUID] = Field(min_length=1)
    confidence: Confidence = Field(default_factory=Confidence)
    ai_used: StrictBool = False


class AnalysisSummary(Contract):
    analysis_id: UUID
    status: AnalysisStatus = AnalysisStatus.NOT_RUN
    mode: AnalysisMode
    demo_fixture_id: Label | None = None
    court_profile_id: Label
    created_at: AwareDatetime
    stages: list[StageState] = Field(default_factory=list)
    coverage: Coverage = Field(default_factory=Coverage)
    overall_score: Annotated[int, Field(ge=0, le=100, strict=True)] | None = None
    risk_level: RiskLevel | None = None
    score_is_provisional: StrictBool = True

    @model_validator(mode="after")
    def truthful_summary(self) -> Self:
        if (self.mode == AnalysisMode.DEMO) != (self.demo_fixture_id is not None):
            raise ValueError("Only explicit demo mode has a fixture ID")
        names = [stage.name for stage in self.stages]
        if len(names) != len(set(names)):
            raise ValueError("Stage names must be unique")
        for field in ("eligible", "evaluated", "unavailable", "pending"):
            if getattr(self.coverage, field) != sum(
                getattr(stage.coverage, field) for stage in self.stages
            ):
                raise ValueError("Analysis coverage must equal the sum of stage coverage")
        if any(stage.coverage.truncated for stage in self.stages) and not self.coverage.truncated:
            raise ValueError("Truncated stages must appear in overall coverage")
        if self.status == AnalysisStatus.COMPLETED and (
            set(names) != set(StageName)
            or any(
                s.status not in {StageStatus.COMPLETED, StageStatus.SKIPPED} for s in self.stages
            )
        ):
            raise ValueError("Completed analysis needs every stage accounted for")
        if self.overall_score is None and self.risk_level is not None:
            raise ValueError("Risk requires an explicitly computed score")
        if self.overall_score is not None and self.coverage.evaluated == 0:
            raise ValueError("No evaluated checks means no score")
        if self.overall_score is not None and self.status in {
            AnalysisStatus.NOT_RUN,
            AnalysisStatus.QUEUED,
        }:
            raise ValueError("Scores cannot precede execution")
        if not self.score_is_provisional and (
            self.status != AnalysisStatus.COMPLETED or not self.coverage.complete
        ):
            raise ValueError("Final score requires complete analysis and coverage")
        if self.risk_level == RiskLevel.READY_FOR_REVIEW and self.score_is_provisional:
            raise ValueError("Provisional or incomplete checks cannot imply readiness")
        return self
