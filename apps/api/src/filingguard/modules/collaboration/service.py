"""Business logic for finding comments and reviewer sign-off."""

from datetime import UTC, datetime
from uuid import UUID

from filingguard.db.repository import AnalysisRepository
from filingguard.modules.collaboration.schemas import (
    FindingCommentCreate,
    FindingCommentResponse,
    FindingDispositionRequest,
    FindingDispositionResponse,
)


def add_comment(
    repository: AnalysisRepository,
    owner_hash: str,
    analysis_id: UUID,
    finding_id: UUID,
    payload: FindingCommentCreate,
) -> FindingCommentResponse:
    row = repository.add_finding_comment(
        owner_hash=owner_hash,
        analysis_id=analysis_id,
        finding_id=finding_id,
        author_name=payload.author_name,
        author_role=payload.author_role,
        content=payload.content,
    )
    return FindingCommentResponse(
        id=row.id,
        analysis_id=row.analysis_id,
        finding_id=row.finding_id,
        author_name=row.author_name,
        author_role=row.author_role,
        content=row.content,
        created_at=row.created_at,
    )


def list_comments(
    repository: AnalysisRepository,
    owner_hash: str,
    analysis_id: UUID,
    finding_id: UUID,
) -> list[FindingCommentResponse]:
    rows = repository.list_finding_comments(owner_hash, analysis_id, finding_id)
    return [
        FindingCommentResponse(
            id=r.id,
            analysis_id=r.analysis_id,
            finding_id=r.finding_id,
            author_name=r.author_name,
            author_role=r.author_role,
            content=r.content,
            created_at=r.created_at,
        )
        for r in rows
    ]


def set_disposition(
    repository: AnalysisRepository,
    owner_hash: str,
    analysis_id: UUID,
    finding_id: UUID,
    payload: FindingDispositionRequest,
) -> FindingDispositionResponse:
    disposition_data = {
        "status": payload.status,
        "disposition": payload.status,
        "rationale": payload.rationale,
        "reviewer_name": payload.reviewer_name,
        "reviewer_role": payload.reviewer_role,
        "signed_at": datetime.now(UTC).isoformat(),
    }
    finding = repository.update_finding_disposition(
        owner_hash=owner_hash,
        analysis_id=analysis_id,
        finding_id=finding_id,
        status=payload.status,
        disposition_metadata=disposition_data,
    )
    return FindingDispositionResponse(
        finding_id=finding.id,
        status=payload.status,
        disposition_metadata=finding.disposition_metadata,
    )
