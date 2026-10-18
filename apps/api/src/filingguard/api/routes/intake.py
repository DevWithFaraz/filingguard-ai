import logging
from datetime import datetime
from typing import Annotated, Literal
from urllib.parse import unquote
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from filingguard.api.contracts import (
    AnalysisAccepted,
    CourtProfilesResponse,
    CourtProfileSummary,
    DeleteResponse,
    DemoSubmission,
    GroundedAnswerResponse,
    GroundedQuestionHistory,
    GroundedQuestionRequest,
    RedTeamResponse,
    SafeAuthority,
    SafeCitation,
    SafeCitationsResponse,
    SafeFindingsResponse,
    SavedEvidenceResponse,
    SavedGraphResponse,
    SavedResultsResponse,
    TextSubmission,
)
from filingguard.api.errors import DocumentError
from filingguard.core.admission import issue_session, lifecycle
from filingguard.db.models import Authority, Finding
from filingguard.db.repository import AnalysisNotFound, AnalysisNotReady
from filingguard.integrations.storage.service import PDFValidationError, StorageError
from filingguard.modules.analyses.demo import DemoUnavailable
from filingguard.modules.analyses.demo_preview import FIXTURE_ROOT, load_demo_preview
from filingguard.modules.analyses.schemas import (
    AnalysisSummary,
    Coverage,
    DocumentLocation,
    StageName,
    StageState,
)
from filingguard.modules.citations.schemas import CitationExtractionMetadata
from filingguard.modules.documents.extraction import extract_text
from filingguard.modules.documents.intake import (
    PROFILES,
    DocumentSummary,
    PreparedDocument,
    prepare,
    prepared,
)
from filingguard.modules.documents.service import extract_pdf
from filingguard.modules.grounded_qa.service import (
    ask_finding_question,
    get_finding_qa_history,
)
from filingguard.modules.privacy.service import mask_excerpt
from filingguard.modules.red_team.service import synthesize_red_team
from filingguard.modules.reports.service import (
    render_report,
    saved_evidence,
    saved_graph,
    saved_results,
)
from filingguard.modules.scoring.service import score_review

logger = logging.getLogger(__name__)
router = APIRouter()


class SessionIssued(BaseModel):
    token: str
    expires_at: datetime


class Capabilities(BaseModel):
    intake_enabled: bool
    legal_analysis_enabled: bool = False
    max_file_bytes: int = 10 * 1024 * 1024
    max_characters: int = 100000
    profiles: list[CourtProfileSummary] = []


@router.get("/capabilities", response_model=Capabilities)
def capabilities(request: Request):
    settings = request.app.state.settings
    return Capabilities(
        intake_enabled=settings.intake_enabled and settings.private_storage_directory is not None,
        legal_analysis_enabled=settings.source_verification_enabled
        or settings.semantic_review_enabled,
        profiles=[profile.model_dump() for profile in PROFILES],
    )


@router.get("/court-profiles", response_model=CourtProfilesResponse)
def profiles():
    return CourtProfilesResponse(profiles=PROFILES)


@router.post("/sessions", response_model=SessionIssued, status_code=201)
def create_session(request: Request):
    try:
        return issue_session(request)
    except OverflowError:
        raise HTTPException(429, headers={"Retry-After": "60"}) from None
    except Exception:
        raise HTTPException(503) from None


def store_document(request: Request, document, *, name, court, ai_used, data=None, demo=False):
    try:
        if not name.strip() or len(name) > 255 or any(ord(character) < 32 for character in name):
            raise ValueError("Invalid document label")
        service = lifecycle(request)
        identity = prepare(
            service,
            request.state.owner_hash,
            request.state.session_expiry,
            document,
            name=name,
            court_profile_id=court,
            ai_used=ai_used,
            data=data,
            demo=demo,
        )
        logger.info(
            "analysis.prepared analysis_id=%s correlation_id=%s mode=%s paragraphs=%d",
            identity,
            identity,
            "demo" if demo else "live",
            len(document.paragraphs),
        )
        return prepared(service, request.state.owner_hash, identity)
    except PDFValidationError as error:
        raise DocumentError(error.code) from None
    except OverflowError:
        raise HTTPException(429, headers={"Retry-After": "60"}) from None
    except ValueError:
        raise HTTPException(422) from None
    except (SQLAlchemyError, StorageError) as error:
        logger.error("analysis.prepare_failed error_type=%s", type(error).__name__)
        raise HTTPException(503) from None


@router.post("/analyses/text", response_model=PreparedDocument, status_code=201)
def submit_text(request: Request, body: TextSubmission):
    try:
        document = extract_text(body.text)
    except PDFValidationError as error:
        raise DocumentError(error.code) from None
    return store_document(
        request,
        document,
        name=body.document_name,
        court=body.court_profile_id,
        ai_used=body.ai_used,
    )


@router.post(
    "/analyses/file",
    response_model=PreparedDocument,
    status_code=201,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}},
        }
    },
)
async def submit_file(
    request: Request,
    document_name: Annotated[str, Header(alias="X-Document-Name", min_length=1, max_length=1024)],
    court_profile_id: Annotated[str, Query(min_length=1, max_length=255)],
    ai_used: Literal["true", "false"],
):
    if request.headers.get("content-type", "").split(";", 1)[0] != "application/pdf":
        raise HTTPException(415)
    if court_profile_id not in {"unverified", "us-txnd-lr7-2f-v1"}:
        raise HTTPException(422)
    data = await request.body()
    try:
        name = unquote(document_name, errors="strict")
    except UnicodeError:
        raise HTTPException(422) from None
    if not name.strip() or len(name) > 255 or any(ord(character) < 32 for character in name):
        raise HTTPException(422)
    try:
        document = await run_in_threadpool(extract_pdf, data)
    except PDFValidationError as error:
        raise DocumentError(error.code) from None
    return await run_in_threadpool(
        store_document,
        request,
        document,
        name=name,
        court=court_profile_id,
        ai_used=ai_used == "true",
        data=data,
    )


@router.post("/analyses/demo", response_model=PreparedDocument, status_code=201)
def submit_demo(request: Request, body: DemoSubmission):
    try:
        preview = load_demo_preview(FIXTURE_ROOT, body.fixture_id, mode=body.mode)
        document = extract_text(preview.document)
    except DemoUnavailable:
        raise HTTPException(503) from None
    return store_document(
        request,
        document,
        name="Curated synthetic filing",
        court=body.court_profile_id,
        ai_used=body.ai_used,
        demo=True,
    )


@router.get("/analyses", response_model=list[DocumentSummary])
def activity(request: Request):
    try:
        service = lifecycle(request)
        return [
            DocumentSummary(
                analysis_id=row.id,
                document_name=row.document_name,
                mode=row.mode,
                court_profile_id=row.court_profile_id,
                ai_used=row.ai_used,
                execution_status=row.status,
                expires_at=row.expires_at,
                paragraph_count=len(row.document_snapshot["paragraphs"]),
            )
            for row in service.repository.list_analyses(request.state.owner_hash)
            if row.document_snapshot is not None
        ]
    except (SQLAlchemyError, StorageError):
        raise HTTPException(503) from None


@router.get("/analyses/{analysis_id}", response_model=PreparedDocument)
def get_document(request: Request, analysis_id: UUID):
    try:
        return prepared(lifecycle(request), request.state.owner_hash, analysis_id)
    except (AnalysisNotFound, ValueError):
        raise HTTPException(404) from None
    except (SQLAlchemyError, StorageError):
        raise HTTPException(503) from None


@router.get("/analyses/{analysis_id}/status", response_model=AnalysisSummary)
def review_status(request: Request, analysis_id: UUID):
    try:
        repository = lifecycle(request).repository
        row = repository.get_analysis(request.state.owner_hash, analysis_id)
        stages = [
            StageState.model_validate(state)
            for k, state in row.stage_states.items()
            if k in {stage.value for stage in StageName}
        ]
        coverage = Coverage(
            eligible=sum(stage.coverage.eligible for stage in stages),
            evaluated=sum(stage.coverage.evaluated for stage in stages),
            unavailable=sum(stage.coverage.unavailable for stage in stages),
            pending=sum(stage.coverage.pending for stage in stages),
            truncated=any(stage.coverage.truncated for stage in stages),
            limitation="Some checks covered only part of the material"
            if any(stage.coverage.truncated for stage in stages)
            else None,
        )
        score = score_review(
            stages,
            repository.list_records(request.state.owner_hash, analysis_id, Finding),
            status=row.status,
        )
        return AnalysisSummary(
            analysis_id=row.id,
            status=row.status,
            mode=row.mode,
            demo_fixture_id=row.demo_fixture_id,
            court_profile_id=row.court_profile_id,
            created_at=row.created_at,
            stages=stages,
            coverage=coverage,
            overall_score=score["value"],
            risk_level=score["risk_level"],
            score_is_provisional=True,
        )
    except AnalysisNotFound:
        raise HTTPException(404) from None
    except (SQLAlchemyError, ValueError):
        raise HTTPException(503) from None


@router.get("/analyses/{analysis_id}/findings", response_model=SafeFindingsResponse)
def review_findings(request: Request, analysis_id: UUID):
    try:
        repository = lifecycle(request).repository
        result = saved_results(repository, request.state.owner_hash, analysis_id)
        return SafeFindingsResponse(
            analysis_id=analysis_id,
            findings=result["findings"],
        )
    except AnalysisNotFound:
        raise HTTPException(404) from None
    except (SQLAlchemyError, ValueError):
        raise HTTPException(503) from None


@router.get("/analyses/{analysis_id}/citations", response_model=SafeCitationsResponse)
def review_citations(request: Request, analysis_id: UUID):
    try:
        repository = lifecycle(request).repository
        analysis = repository.get_analysis(request.state.owner_hash, analysis_id)
        stage = StageState.model_validate(
            analysis.stage_states.get(
                "citations", {"name": StageName.CITATIONS, "status": "not_run"}
            )
        )
        # Terminal stage writes commit atomically and reruns use fresh analysis IDs.
        # Do not mix a pre-commit running state with newly committed occurrences.
        records = (
            repository.list_citations(request.state.owner_hash, analysis_id)
            if (stage.status in {"partial", "completed"})
            else []
        )
        authorities_list = (
            repository.list_records(request.state.owner_hash, analysis_id, Authority)
            if (stage.status in {"partial", "completed"})
            else []
        )
        safe_authorities_map: dict[UUID, SafeAuthority] = {}
        for auth in authorities_list:
            safe_auth = SafeAuthority(
                id=auth.id,
                source=auth.source,
                external_id=auth.external_id,
                case_name=auth.case_name,
                citation=auth.citation,
                court=auth.court,
                year=auth.year,
                source_url=auth.source_url,
                opinion_text_available=auth.opinion_text_available,
                opinion_text=auth.opinion_text,
                source_sha256=auth.source_sha256,
                retrieved_at=auth.retrieved_at,
                source_metadata=auth.source_metadata,
            )
            safe_authorities_map[auth.id] = safe_auth
        text = analysis.document_snapshot["text"]
        masked = mask_excerpt(text, 0, len(text))
        citation_groups: dict[str, list] = {}
        for row in records:
            key = (row.normalized_text or row.raw_text or "").strip().lower()
            if key:
                citation_groups.setdefault(key, []).append(row)

        citations = []
        for row in records:
            if (
                row.start_offset is None
                or row.end_offset is None
                or not 0 <= row.start_offset < row.end_offset <= len(text)
                or row.raw_text != text[row.start_offset : row.end_offset]
            ):
                raise ValueError("Stored citation span mismatch")

            display = masked.text[row.start_offset : row.end_offset]
            safe_auth = safe_authorities_map.get(row.authority_id) if row.authority_id else None
            key = (row.normalized_text or row.raw_text or "").strip().lower()
            group = citation_groups.get(key, [row])
            dup_count = len(group)
            repeated_locs = (
                [
                    DocumentLocation(
                        start=other.start_offset,
                        end=other.end_offset,
                        page_number=other.page_number,
                        segment_id=other.segment_id,
                    )
                    for other in sorted(group, key=lambda r: r.start_offset)
                ]
                if dup_count > 1
                else []
            )
            citations.append(
                SafeCitation(
                    id=row.id,
                    masked_raw_text=display,
                    normalized_text=row.normalized_text if display == row.raw_text else None,
                    location=DocumentLocation(
                        start=row.start_offset,
                        end=row.end_offset,
                        page_number=row.page_number,
                        segment_id=row.segment_id,
                    ),
                    extraction=CitationExtractionMetadata.model_validate(row.extraction_metadata)
                    if row.extraction_metadata
                    else None,
                    verification_status=row.verification_status,
                    authority_id=row.authority_id,
                    authority=safe_auth,
                    reason=(row.extraction_metadata.get("verification") or {}).get("reason"),
                    limitation=(row.extraction_metadata.get("verification") or {}).get(
                        "limitation"
                    ),
                    duplicate_count=dup_count,
                    repeated_locations=repeated_locs,
                )
            )
        return SafeCitationsResponse(
            analysis_id=analysis_id,
            stage=stage,
            citations=citations,
            detected_count=stage.coverage.eligible,
            authorities=list(safe_authorities_map.values()),
            masking_limitation=masked.limitation,
        )
    except AnalysisNotFound:
        raise HTTPException(404) from None
    except (SQLAlchemyError, ValueError, TypeError, KeyError):
        raise HTTPException(503) from None


def _terminal_results(request, analysis_id):
    repository = lifecycle(request).repository
    row = repository.get_analysis(request.state.owner_hash, analysis_id)
    if row.status in {"queued", "running"}:
        raise HTTPException(409)
    return repository


@router.get("/analyses/{analysis_id}/results", response_model=SavedResultsResponse)
def review_results(request: Request, analysis_id: UUID):
    try:
        repo = _terminal_results(request, analysis_id)
        return saved_results(repo, request.state.owner_hash, analysis_id)
    except AnalysisNotFound:
        raise HTTPException(404) from None
    except (SQLAlchemyError, ValueError, KeyError, TypeError):
        raise HTTPException(503) from None


@router.get("/analyses/{analysis_id}/graph", response_model=SavedGraphResponse)
def review_graph(request: Request, analysis_id: UUID):
    try:
        repo = _terminal_results(request, analysis_id)
        return saved_graph(repo, request.state.owner_hash, analysis_id)
    except AnalysisNotFound:
        raise HTTPException(404) from None
    except (SQLAlchemyError, ValueError, KeyError, TypeError):
        raise HTTPException(503) from None


@router.get(
    "/analyses/{analysis_id}/findings/{finding_id}/evidence", response_model=SavedEvidenceResponse
)
def review_evidence(request: Request, analysis_id: UUID, finding_id: UUID):
    try:
        repo = _terminal_results(request, analysis_id)
        return saved_evidence(repo, request.state.owner_hash, analysis_id, finding_id)
    except LookupError:
        raise HTTPException(404) from None
    except (SQLAlchemyError, ValueError, KeyError, TypeError):
        raise HTTPException(503) from None


@router.post(
    "/analyses/{analysis_id}/findings/{finding_id}/questions",
    response_model=GroundedAnswerResponse,
)
def ask_finding_qa(
    request: Request,
    analysis_id: UUID,
    finding_id: UUID,
    payload: GroundedQuestionRequest,
):
    try:
        repo = _terminal_results(request, analysis_id)
        return ask_finding_question(
            repo,
            request.state.owner_hash,
            analysis_id,
            finding_id,
            payload.question,
        )
    except AnalysisNotFound:
        raise HTTPException(404) from None
    except LookupError:
        raise HTTPException(404) from None
    except OverflowError:
        raise HTTPException(429, headers={"Retry-After": "60"}) from None
    except (SQLAlchemyError, ValueError, KeyError, TypeError) as error:
        logger.error(
            "finding_qa.failed analysis_id=%s correlation_id=%s finding_id=%s error_type=%s",
            analysis_id,
            analysis_id,
            finding_id,
            type(error).__name__,
        )
        raise HTTPException(503) from None


@router.get(
    "/analyses/{analysis_id}/findings/{finding_id}/questions",
    response_model=GroundedQuestionHistory,
)
def get_finding_qa(
    request: Request,
    analysis_id: UUID,
    finding_id: UUID,
):
    try:
        repo = _terminal_results(request, analysis_id)
        return get_finding_qa_history(
            repo,
            request.state.owner_hash,
            analysis_id,
            finding_id,
        )
    except AnalysisNotFound:
        raise HTTPException(404) from None
    except LookupError:
        raise HTTPException(404) from None
    except (SQLAlchemyError, ValueError, KeyError, TypeError) as error:
        logger.error(
            "finding_qa.history_failed analysis_id=%s correlation_id=%s "
            "finding_id=%s error_type=%s",
            analysis_id,
            analysis_id,
            finding_id,
            type(error).__name__,
        )
        raise HTTPException(503) from None


@router.get("/analyses/{analysis_id}/report")
def review_report(
    request: Request,
    analysis_id: UUID,
    format: Literal["markdown", "html", "pdf"] = "markdown",
):
    try:
        repo = _terminal_results(request, analysis_id)
        result = saved_results(repo, request.state.owner_hash, analysis_id)
        if format == "pdf":
            suffix = "pdf"
            media_type = "application/pdf"
        elif format == "html":
            suffix = "html"
            media_type = "text/html"
        else:
            suffix = "md"
            media_type = "text/markdown"

        return Response(
            render_report(result, format=format),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="filingguard-{analysis_id}.{suffix}"',
                "Cache-Control": "no-store",
                "Content-Security-Policy": "default-src 'none'; sandbox",
            },
        )
    except AnalysisNotFound:
        raise HTTPException(404) from None
    except (SQLAlchemyError, ValueError, KeyError, TypeError):
        raise HTTPException(503) from None


@router.post("/analyses/{analysis_id}/red-team", response_model=RedTeamResponse)
@router.get("/analyses/{analysis_id}/red-team", response_model=RedTeamResponse)
def review_red_team(request: Request, analysis_id: UUID):
    try:
        repo = _terminal_results(request, analysis_id)
        return synthesize_red_team(repo, request.state.owner_hash, analysis_id)
    except AnalysisNotFound:
        raise HTTPException(404) from None
    except (SQLAlchemyError, ValueError, KeyError, TypeError) as error:
        logger.error(
            "red_team.failed analysis_id=%s correlation_id=%s error_type=%s",
            analysis_id,
            analysis_id,
            type(error).__name__,
        )
        raise HTTPException(503) from None


@router.post("/analyses/{analysis_id}/run", response_model=AnalysisAccepted, status_code=202)
def run_review(request: Request, analysis_id: UUID):
    runners = request.app.state.review_runners
    if not runners:
        raise HTTPException(503) from None
    try:
        row = lifecycle(request).repository.get_analysis(request.state.owner_hash, analysis_id)
        if row.mode == "demo":
            try:
                preview = load_demo_preview(FIXTURE_ROOT, row.demo_fixture_id, mode="demo")
                fixture = extract_text(preview.document)
            except (DemoUnavailable, ValueError):
                raise HTTPException(503) from None
            if (
                row.demo_fixture_id != "curated-v1"
                or row.document_sha256 != fixture.input_sha256
                or row.document_snapshot.get("text") != fixture.text
            ):
                raise HTTPException(503)
        review = request.app.state.analysis_runtime.get_review(
            request.app.state.admission.slot, runners
        )
        review.start(request.state.owner_hash, analysis_id)
        logger.info(
            "review.queued analysis_id=%s correlation_id=%s mode=%s",
            analysis_id,
            analysis_id,
            row.mode,
        )
        return AnalysisAccepted(analysis_id=analysis_id, status="queued", mode=row.mode)
    except AnalysisNotFound:
        raise HTTPException(404) from None
    except AnalysisNotReady:
        raise HTTPException(409) from None
    except OverflowError:
        raise HTTPException(409) from None
    except (SQLAlchemyError, ValueError, RuntimeError) as error:
        logger.error(
            "review.queue_failed analysis_id=%s correlation_id=%s error_type=%s",
            analysis_id,
            analysis_id,
            type(error).__name__,
        )
        raise HTTPException(503) from None


@router.post("/analyses/{analysis_id}/rerun", response_model=PreparedDocument, status_code=201)
def rerun_review(request: Request, analysis_id: UUID):
    try:
        service = lifecycle(request)
        new_id = service.repository.clone_for_rerun(request.state.owner_hash, analysis_id)
        logger.info(
            "analysis.rerun analysis_id=%s correlation_id=%s new_analysis_id=%s",
            analysis_id,
            analysis_id,
            new_id,
        )
        return prepared(service, request.state.owner_hash, new_id)
    except AnalysisNotFound:
        raise HTTPException(404) from None
    except AnalysisNotReady:
        raise HTTPException(409) from None
    except OverflowError:
        raise HTTPException(429, headers={"Retry-After": "60"}) from None
    except (SQLAlchemyError, ValueError) as error:
        logger.error(
            "analysis.rerun_failed analysis_id=%s correlation_id=%s error_type=%s",
            analysis_id,
            analysis_id,
            type(error).__name__,
        )
        raise HTTPException(503) from None


@router.delete("/analyses/{analysis_id}", response_model=DeleteResponse)
def delete_document(request: Request, analysis_id: UUID):
    try:
        lifecycle(request).delete(request.state.owner_hash, analysis_id)
        logger.info(
            "analysis.deleted analysis_id=%s correlation_id=%s",
            analysis_id,
            analysis_id,
        )
    except AnalysisNotFound:
        raise HTTPException(404) from None
    except AnalysisNotReady:
        raise HTTPException(409) from None
    except (SQLAlchemyError, StorageError) as error:
        logger.error(
            "analysis.delete_failed analysis_id=%s correlation_id=%s error_type=%s",
            analysis_id,
            analysis_id,
            type(error).__name__,
        )
        raise HTTPException(503) from None
    return DeleteResponse(analysis_id=analysis_id, deleted=True)
