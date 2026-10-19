"""Service for multi-filing batch review and queue coordination."""

from datetime import datetime
from uuid import UUID

from filingguard.db.repository import AnalysisRepository
from filingguard.modules.analyses.lifecycle import AnalysisLifecycle
from filingguard.modules.batches.schemas import (
    BatchCreate,
    BatchDetail,
    BatchItemSummary,
    BatchSummary,
)
from filingguard.modules.documents.extraction import extract_text
from filingguard.modules.documents.intake import prepare


def create_batch_analyses(
    lifecycle: AnalysisLifecycle,
    owner_hash: str,
    session_expiry: datetime,
    payload: BatchCreate,
) -> BatchSummary:
    items: list[tuple[UUID, str]] = []
    for doc in payload.documents:
        extracted = extract_text(doc.text)
        analysis_id = prepare(
            lifecycle,
            owner_hash,
            session_expiry,
            extracted,
            name=doc.document_name,
            court_profile_id=doc.court_profile_id,
            ai_used=doc.ai_used,
        )
        items.append((analysis_id, doc.document_name))

    batch = lifecycle.repository.create_batch(owner_hash, payload.name, items)
    return BatchSummary(
        id=batch.id,
        name=batch.name,
        status=batch.status,
        total_count=batch.total_count,
        completed_count=batch.completed_count,
        failed_count=batch.failed_count,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
    )


def list_batches(repository: AnalysisRepository, owner_hash: str) -> list[BatchSummary]:
    rows = repository.list_batches(owner_hash)
    return [
        BatchSummary(
            id=r.id,
            name=r.name,
            status=r.status,
            total_count=r.total_count,
            completed_count=r.completed_count,
            failed_count=r.failed_count,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


def get_batch(repository: AnalysisRepository, owner_hash: str, batch_id: UUID) -> BatchDetail:
    batch, items = repository.get_batch(owner_hash, batch_id)
    return BatchDetail(
        id=batch.id,
        name=batch.name,
        status=batch.status,
        total_count=batch.total_count,
        completed_count=batch.completed_count,
        failed_count=batch.failed_count,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        items=[
            BatchItemSummary(
                id=item.id,
                analysis_id=item.analysis_id,
                document_name=item.document_name,
                status=item.status,
                created_at=item.created_at,
            )
            for item in items
        ],
    )


def cancel_batch(repository: AnalysisRepository, owner_hash: str, batch_id: UUID) -> BatchSummary:
    batch = repository.cancel_batch(owner_hash, batch_id)
    return BatchSummary(
        id=batch.id,
        name=batch.name,
        status=batch.status,
        total_count=batch.total_count,
        completed_count=batch.completed_count,
        failed_count=batch.failed_count,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
    )
