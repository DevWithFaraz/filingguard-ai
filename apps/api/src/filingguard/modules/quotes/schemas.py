"""Deterministic quote occurrences and string comparison, without legal verdicts."""

from dataclasses import dataclass
from uuid import UUID

from filingguard.modules.analyses.schemas import QuoteStatus

METHOD_VERSION = "quote-forensics-v2"
MAX_QUOTES = 50
MAX_QUOTE_CHARS = 2000
MAX_SOURCE_CHARS = 500000
LIMITATION = (
    "Heuristic quotation extraction and nearby citation association; string similarity "
    "does not establish legal support or equivalent meaning. String similarity is not "
    "meaning-preservation."
)
SEMANTIC_METHOD = "negation-aware-token-overlap-v1"
SEMANTIC_LIMITATION = (
    "The local token-overlap semantic signal is uncalibrated and is not exact quotation, "
    "meaning-preservation, or legal-meaning proof."
)


@dataclass(frozen=True)
class QuoteOccurrence:
    text: str
    start: int
    end: int
    kind: str


@dataclass(frozen=True)
class QuoteAssociation:
    citation_id: UUID | None
    authority_id: UUID | None
    reason: str | None = None
    candidates: tuple[UUID, ...] = ()


@dataclass(frozen=True)
class MeaningAlteration:
    kind: str
    severity: str
    title: str
    description: str
    details: dict | None = None


@dataclass(frozen=True)
class SemanticSimilarity:
    score: float
    method: str
    limitation: str
    negation: bool = False
    omission: bool = False
    material_change: bool = False

    def as_metadata(self) -> dict:
        return {
            "score": self.score,
            "method": self.method,
            "limitation": self.limitation,
            "negation": self.negation,
            "omission": self.omission,
            "material_change": self.material_change,
        }


@dataclass(frozen=True)
class QuoteComparison:
    status: QuoteStatus
    similarity: float | None = None
    passage: str | None = None
    source_start: int | None = None
    source_end: int | None = None
    reason: str | None = None
    meaning_alteration: MeaningAlteration | None = None
    semantic_similarity: SemanticSimilarity | None = None
