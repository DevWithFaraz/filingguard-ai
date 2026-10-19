"""Owner-scoped claim correction contracts (FR-065)."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from filingguard.modules.analyses.schemas import Contract

MAX_CORRECTION_CHARS = 8000
MAX_HISTORY = 20
LIMITATION = (
    "User corrections are stored separately from the original extraction and do not "
    "rewrite document offsets. Proposition support for the corrected claim is marked "
    "stale. POST /analyses/{analysis_id}/rerun clones a new analysis and re-extracts "
    "claims without this correction; in-place proposition-only re-run is not available. "
    "Existing proposition findings from the original extraction are not deleted."
)


class ClaimCorrectionRequest(Contract):
    corrected_text: Annotated[str, Field(min_length=1, max_length=MAX_CORRECTION_CHARS)]


class ClaimCorrectionEntry(Contract):
    id: UUID
    corrected_text: str
    created_at: datetime


class ClaimCorrectionResponse(Contract):
    analysis_id: UUID
    claim_id: UUID
    original_text: str
    corrected_text: str
    history: list[ClaimCorrectionEntry] = Field(max_length=MAX_HISTORY)
    propositions_stale: Literal[True] = True
    affected_link_ids: list[UUID] = Field(max_length=200)
    limitation: str = LIMITATION
