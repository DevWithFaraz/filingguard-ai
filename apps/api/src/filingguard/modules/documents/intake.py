"""Preparation saves original segments, but never executes legal review engines."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from filingguard.api.contracts import CourtProfileSummary
from filingguard.db.models import DocumentSegment
from filingguard.modules.analyses.lifecycle import AnalysisLifecycle
from filingguard.modules.analyses.schemas import AnalysisStatus, Contract, Coverage
from filingguard.modules.court_rules.service import load_profile
from filingguard.modules.documents.schemas import ExtractedDocument
from filingguard.modules.privacy.service import mask_excerpt


class DocumentSummary(Contract):
    analysis_id: UUID
    document_name: str
    mode: Literal["live", "demo"]
    court_profile_id: str
    ai_used: bool
    expires_at: datetime
    execution_status: AnalysisStatus = AnalysisStatus.NOT_RUN
    paragraph_count: int = Field(ge=1, le=2000)


class PreparedDocument(DocumentSummary):
    document: ExtractedDocument
    masking_count: int = Field(ge=0)
    masking_limitation: str


_DEMO_PROFILE = load_profile("synthetic-demo-v1")
PROFILES = [
    CourtProfileSummary(
        id="unverified",
        version="unconfigured-v1",
        name="Court rules not configured",
        is_demo=False,
        applicability="unknown",
    ),
    CourtProfileSummary(
        id=_DEMO_PROFILE.id,
        version=_DEMO_PROFILE.version,
        name=_DEMO_PROFILE.name,
        is_demo=True,
        applicability="synthetic",
    ),
]


def prepare(
    lifecycle: AnalysisLifecycle,
    owner: str,
    expires_at: datetime,
    document: ExtractedDocument,
    *,
    name: str,
    court_profile_id: str,
    ai_used: bool,
    data: bytes | None = None,
    demo: bool = False,
) -> UUID:
    repo = lifecycle.repository
    if court_profile_id not in ({"synthetic-demo-v1", "unverified"} if demo else {"unverified"}):
        raise ValueError("Unknown or inapplicable court profile")
    if len(repo.list_analyses(owner)) >= 5:
        raise OverflowError("Session document limit reached")
    file = None
    if data is not None:
        file = lifecycle.storage._store_validated(
            data, len(document.pages), sum(page.end - page.start for page in document.pages)
        )
    try:
        analysis = repo.create_analysis(
            owner,
            document_name=name,
            document_sha256=document.input_sha256,
            expires_at=expires_at,
            stored_file_id=UUID(file.file_id) if file else None,
            court_profile_id=court_profile_id,
            ai_used=ai_used,
            mode="demo" if demo else "live",
            demo_fixture_id="curated-v1" if demo else None,
            status="running",
        )
    except Exception:
        if file:
            lifecycle.storage.delete(file.file_id)
        raise
    try:
        with repo.stage_update(
            owner,
            analysis.id,
            "document",
            "completed",
            coverage=Coverage(eligible=1, evaluated=1),
            analysis_status="not_run",
        ) as writer:
            for paragraph in document.paragraphs:
                writer.add(
                    DocumentSegment(
                        page_number=paragraph.page_number,
                        paragraph_index=paragraph.paragraph_index,
                        text=paragraph.text,
                        start_offset=paragraph.start,
                        end_offset=paragraph.end,
                    )
                )
            # Persist the canonical extracted snapshot and diagnostics, not a second parse.
            writer.analysis.document_snapshot = document.model_dump(mode="json")
        return analysis.id
    except Exception:
        lifecycle.delete(owner, analysis.id)
        raise


def prepared(lifecycle: AnalysisLifecycle, owner: str, analysis_id: UUID) -> PreparedDocument:
    analysis = lifecycle.repository.get_analysis(owner, analysis_id)
    document = ExtractedDocument.model_validate(analysis.document_snapshot)
    masked = mask_excerpt(document.text, 0, len(document.text))
    return PreparedDocument(
        analysis_id=analysis.id,
        execution_status=analysis.status,
        document_name=analysis.document_name,
        mode=analysis.mode,
        court_profile_id=analysis.court_profile_id,
        ai_used=analysis.ai_used,
        expires_at=analysis.expires_at,
        document=document,
        paragraph_count=len(document.paragraphs),
        masking_count=len(masked.detections),
        masking_limitation=masked.limitation,
    )
