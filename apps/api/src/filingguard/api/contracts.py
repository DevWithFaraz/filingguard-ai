"""Planned v1 endpoint boundaries; declaring contracts does not enable submission."""

from datetime import datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, StrictBool, field_validator, model_validator
from pydantic.json_schema import models_json_schema

from filingguard.modules.analyses.schemas import (
    AnalysisMode,
    AnalysisStatus,
    AnalysisSummary,
    CitationResult,
    CitationStatus,
    Contract,
    Coverage,
    DocumentLocation,
    FindingRecord,
    Label,
    PropositionResult,
    PropositionStatus,
    QuoteResult,
    QuoteStatus,
    StageState,
)
from filingguard.modules.citations.schemas import (
    EXTRACTION_LIMITATION,
    CitationExtractionMetadata,
)
from filingguard.modules.claim_corrections.schemas import (
    ClaimCorrectionEntry,
    ClaimCorrectionRequest,
    ClaimCorrectionResponse,
)
from filingguard.modules.evidence.schemas import EvidenceRecord
from filingguard.modules.grounded_qa.schemas import (
    GroundedAnswerResponse,
    GroundedQuestionHistory,
    GroundedQuestionRequest,
)
from filingguard.modules.identity.schemas import (
    IdentityClaimed,
    IdentityClaimRequest,
    IdentityLoginRequest,
    IdentitySessionIssued,
)
from filingguard.modules.red_team.schemas import RedTeamResponse


class TextSubmission(Contract):
    document_name: Label
    text: Annotated[str, Field(min_length=1, max_length=100000, pattern=r"\S")]
    court_profile_id: Label
    ai_used: StrictBool
    mode: Literal["live"] = "live"


class FileSubmissionMetadata(Contract):
    court_profile_id: Label
    ai_used: StrictBool
    mode: Literal["live"] = "live"


class DemoSubmission(Contract):
    fixture_id: Label
    mode: Literal["demo"] = "demo"
    court_profile_id: Literal["synthetic-demo-v1", "unverified"] = "synthetic-demo-v1"
    ai_used: bool = True


class AnalysisAccepted(Contract):
    analysis_id: UUID
    status: Literal[AnalysisStatus.QUEUED]
    mode: AnalysisMode


class SafeFinding(Contract):
    id: UUID
    type: Literal[
        "privacy",
        "court_rule",
        "citation",
        "claim_support",
        "quote",
        "table_of_authorities",
        "system",
    ]
    severity: Literal["info", "low", "medium", "high", "critical"]
    title: Label
    description: str
    masked_excerpt: str | None = None
    start: int | None = None
    end: int | None = None
    evidence_count: int = 0
    ai_assisted: bool = False
    claim_id: UUID | None = None
    citation_id: UUID | None = None
    authority_id: UUID | None = None
    quote_id: UUID | None = None
    segment_id: UUID | None = None
    evidence: list[dict] = Field(default_factory=list, max_length=400)


class SafeFindingsResponse(Contract):
    analysis_id: UUID
    findings: list[SafeFinding]
    limitation: str = "Local checks are not a legal compliance or complete redaction determination."


class SafeAuthority(Contract):
    id: UUID
    source: str
    external_id: str | None = None
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


class SafeCitation(Contract):
    id: UUID
    masked_raw_text: str
    normalized_text: str | None
    location: DocumentLocation
    extraction: CitationExtractionMetadata | None
    verification_status: CitationStatus
    authority_id: UUID | None = None
    authority: SafeAuthority | None = None
    reason: str | None = None
    limitation: str | None = None
    duplicate_count: int | None = None
    repeated_locations: list[DocumentLocation] = Field(default_factory=list)


class SafeCitationsResponse(Contract):
    analysis_id: UUID
    stage: StageState
    citations: list[SafeCitation] = Field(max_length=200)
    detected_count: int = Field(ge=0)
    authorities: list[SafeAuthority] = Field(default_factory=list)
    limitation: str = EXTRACTION_LIMITATION
    masking_limitation: str = "Heuristic masking can miss names and contextual identifiers."


class SafeClaimLink(Contract):
    id: UUID
    citation_id: UUID
    authority_id: UUID | None = None
    support_status: PropositionStatus
    explanation: str | None = None
    confidence: float | None = None


class SafeClaim(Contract):
    id: UUID
    text: str
    location: DocumentLocation
    extraction_method: Literal["heuristic", "ai"]
    links: list[SafeClaimLink] = Field(max_length=200)
    corrected_text: str | None = None
    correction_history: list[ClaimCorrectionEntry] = Field(default_factory=list, max_length=20)
    propositions_stale: bool = False


class SafeQuote(Contract):
    id: UUID
    text: str
    location: DocumentLocation
    citation_id: UUID | None = None
    match_status: QuoteStatus
    similarity: float | None = None
    closest_passage: str | None = None


class ScoreDeduction(Contract):
    finding_id: UUID
    type: str
    severity: str
    points: int = Field(ge=0, le=100)


class ScoreCategory(Contract):
    type: Literal[
        "citation", "claim_support", "quote", "privacy", "court_rule", "table_of_authorities"
    ]
    eligible: int = Field(ge=0)
    evaluated: int = Field(ge=0)
    value: int | None = Field(default=None, ge=0, le=100)
    deducted_points: int = Field(ge=0)


class ReviewScore(Contract):
    value: int | None = Field(default=None, ge=0, le=100)
    risk_level: Literal["needs_review", "high_risk"] | None = None
    provisional: Literal[True] = True
    version: Literal["integrity-v1"] = "integrity-v1"
    deductions: list[ScoreDeduction]
    categories: list[ScoreCategory] = Field(default_factory=list, max_length=6)
    limitation: str


class SavedResultsResponse(Contract):
    analysis_id: UUID
    document_name: str
    created_at: datetime
    court_profile_id: str
    mode: AnalysisMode
    status: AnalysisStatus
    stages: list[StageState]
    coverage: Coverage
    score: ReviewScore
    citations: list[SafeCitation] = Field(max_length=200)
    claims: list[SafeClaim] = Field(max_length=100)
    quotes: list[SafeQuote] = Field(max_length=50)
    findings: list[SafeFinding] = Field(max_length=1000)
    limitation: str


class SavedGraphNode(Contract):
    id: str
    label: str
    kind: Literal["section", "claim", "authority"]
    status: str
    finding_ids: list[UUID]


class SavedGraphEdge(Contract):
    id: str
    source: str
    target: str
    label: str


class SavedGraphResponse(Contract):
    analysis_id: UUID
    nodes: list[SavedGraphNode] = Field(max_length=425)
    edges: list[SavedGraphEdge] = Field(max_length=300)


class SavedEvidenceResponse(Contract):
    analysis_id: UUID
    finding_id: UUID
    evidence: list[dict] = Field(max_length=400)


class FindingsResponse(Contract):
    analysis_id: UUID
    findings: list[FindingRecord]
    evidence: list[EvidenceRecord]

    @model_validator(mode="after")
    def scoped_references(self) -> Self:
        findings = {record.id: record for record in self.findings}
        evidence = {record.id: record for record in self.evidence}
        if len(findings) != len(self.findings) or len(evidence) != len(self.evidence):
            raise ValueError("Response record IDs must be unique")
        if any(
            record.analysis_id != self.analysis_id
            for record in [
                *self.findings,
                *self.evidence,
            ]
        ):
            raise ValueError("Response records must belong to the analysis")
        if any(set(record.evidence_ids) - evidence.keys() for record in self.findings):
            raise ValueError("Every finding evidence reference must resolve")
        if any(
            record.finding_id is not None and record.finding_id not in findings
            for record in self.evidence
        ):
            raise ValueError("Evidence finding references must resolve")
        return self


class GraphNode(Contract):
    id: UUID
    type: Literal["section", "claim", "citation", "authority"]
    label: Label
    status: Literal["not_run", "verified", "warning", "risk", "unavailable"]
    finding_ids: list[UUID] = Field(default_factory=list)


class GraphEdge(Contract):
    id: UUID
    source: UUID
    target: UUID
    type: Literal["contains", "cites", "supports", "contradicts", "unclear"]


class GraphResponse(Contract):
    analysis_id: UUID
    nodes: list[GraphNode]
    edges: list[GraphEdge]

    @model_validator(mode="after")
    def resolvable_edges(self) -> Self:
        node_ids = {node.id for node in self.nodes}
        if len(node_ids) != len(self.nodes) or len({edge.id for edge in self.edges}) != len(
            self.edges
        ):
            raise ValueError("Graph IDs must be unique")
        if any(edge.source not in node_ids or edge.target not in node_ids for edge in self.edges):
            raise ValueError("Graph edge endpoints must resolve to returned nodes")
        return self


class ReportResponse(Contract):
    analysis_id: UUID
    format: Literal["markdown", "html", "pdf", "graph-svg", "graph-png"]
    content: Annotated[str, Field(min_length=1)]
    mode: AnalysisMode


class CourtProfileSummary(Contract):
    id: Label
    version: Label
    name: Label
    is_demo: StrictBool
    applicability: Literal["synthetic", "verified_scope", "verified", "unknown"]

    @model_validator(mode="after")
    def synthetic_scope(self) -> Self:
        if self.is_demo != (self.applicability == "synthetic"):
            raise ValueError("Demo profiles must have synthetic applicability")
        return self


class CourtProfilesResponse(Contract):
    profiles: list[CourtProfileSummary]


class DeleteResponse(Contract):
    analysis_id: UUID
    deleted: Literal[True]

    @field_validator("deleted", mode="before")
    @classmethod
    def strict_true(cls, value):
        if value is not True:
            raise ValueError("Deleted must be a JSON boolean")
        return value


class ApiErrorDetail(Contract):
    code: Label
    message: Label
    request_id: UUID


class ApiError(Contract):
    error: ApiErrorDetail


CONTRACT_MODELS = [
    TextSubmission,
    FileSubmissionMetadata,
    DemoSubmission,
    AnalysisAccepted,
    AnalysisSummary,
    CitationResult,
    SafeCitationsResponse,
    SavedResultsResponse,
    SavedGraphResponse,
    SavedEvidenceResponse,
    PropositionResult,
    QuoteResult,
    FindingsResponse,
    GraphResponse,
    ReportResponse,
    CourtProfilesResponse,
    DeleteResponse,
    RedTeamResponse,
    ClaimCorrectionRequest,
    ClaimCorrectionResponse,
    IdentityClaimRequest,
    IdentityLoginRequest,
    IdentityClaimed,
    IdentitySessionIssued,
    GroundedQuestionRequest,
    GroundedAnswerResponse,
    GroundedQuestionHistory,
    ApiError,
]


def contract_definitions() -> dict:
    _, schema = models_json_schema(
        [(model, "validation") for model in CONTRACT_MODELS],
        ref_template="#/components/schemas/{model}",
    )
    return schema["$defs"]
