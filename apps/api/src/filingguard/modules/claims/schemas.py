"""Local claim contexts, measured in original Unicode code points."""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

METHOD_VERSION = "claims-context-v1"
MAX_CLAIMS = 100
LIMITATION = (
    "Heuristic citation context is a candidate proposition, not a legal support verdict. "
    "Sentence boundaries and citation associations require human review."
)


@dataclass(frozen=True)
class ClaimContext:
    text: str
    start: int
    end: int
    segment_id: UUID
    page_number: int | None
    citation_ids: tuple[UUID, ...]
    context_kind: Literal["sentence", "preceding_sentence", "paragraph", "cross_segment"]


@dataclass(frozen=True)
class ClaimExtraction:
    contexts: tuple[ClaimContext, ...]
    detected_count: int
    associated_count: int
    omitted_citation_ids: tuple[UUID, ...]

    @property
    def truncated(self) -> bool:
        return bool(self.omitted_citation_ids)
