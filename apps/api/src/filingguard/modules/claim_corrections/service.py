"""Persist user claim corrections without rewriting original extraction."""

from uuid import UUID

from filingguard.db.models import Claim
from filingguard.db.repository import AnalysisRepository
from filingguard.modules.claim_corrections.schemas import (
    LIMITATION,
    ClaimCorrectionEntry,
    ClaimCorrectionResponse,
)
from filingguard.modules.claim_corrections.text import latest_corrected_text
from filingguard.modules.privacy.service import mask_excerpt
from filingguard.modules.reports.service import safe_text


def apply_claim_correction(
    repository: AnalysisRepository,
    owner_hash: str,
    analysis_id: UUID,
    claim_id: UUID,
    corrected_text: str,
) -> ClaimCorrectionResponse:
    text = corrected_text.strip()
    if not text:
        raise ValueError("Invalid claim correction")
    _, history, link_ids = repository.save_claim_correction(
        owner_hash, analysis_id, claim_id, text
    )
    analysis = repository.get_analysis(owner_hash, analysis_id)
    filing = analysis.document_snapshot["text"]
    claim = repository.get_record(owner_hash, analysis_id, Claim, claim_id)
    if claim is None:
        raise LookupError("Claim not found")
    original_display = mask_excerpt(filing, claim.start_offset, claim.end_offset).text
    current = latest_corrected_text(claim) or text
    return ClaimCorrectionResponse(
        analysis_id=analysis_id,
        claim_id=claim_id,
        original_text=original_display,
        corrected_text=safe_text(current, filing),
        history=[
            ClaimCorrectionEntry(
                id=entry["id"],
                corrected_text=safe_text(entry["corrected_text"], filing),
                created_at=entry["created_at"],
            )
            for entry in history
        ],
        affected_link_ids=link_ids,
        limitation=LIMITATION,
    )
