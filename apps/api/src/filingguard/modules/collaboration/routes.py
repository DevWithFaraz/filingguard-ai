"""FastAPI routes for finding comments and reviewer sign-off."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from filingguard.core.admission import lifecycle
from filingguard.db.repository import AnalysisNotFound
from filingguard.modules.collaboration.schemas import (
    FindingCommentCreate,
    FindingCommentResponse,
    FindingDispositionRequest,
    FindingDispositionResponse,
)
from filingguard.modules.collaboration.service import (
    add_comment,
    list_comments,
    set_disposition,
)

router = APIRouter(tags=["Finding collaboration"])


@router.post(
    "/analyses/{analysis_id}/findings/{finding_id}/comments",
    response_model=FindingCommentResponse,
    status_code=201,
)
async def add_finding_comment_route(
    request: Request,
    analysis_id: UUID,
    finding_id: UUID,
    body: FindingCommentCreate,
):
    try:
        return await run_in_threadpool(
            add_comment,
            lifecycle(request).repository,
            request.state.owner_hash,
            analysis_id,
            finding_id,
            body,
        )
    except AnalysisNotFound:
        raise HTTPException(404, "Finding or analysis not found") from None


@router.get(
    "/analyses/{analysis_id}/findings/{finding_id}/comments",
    response_model=list[FindingCommentResponse],
)
async def list_finding_comments_route(
    request: Request,
    analysis_id: UUID,
    finding_id: UUID,
):
    try:
        return await run_in_threadpool(
            list_comments,
            lifecycle(request).repository,
            request.state.owner_hash,
            analysis_id,
            finding_id,
        )
    except AnalysisNotFound:
        raise HTTPException(404, "Finding or analysis not found") from None


@router.post(
    "/analyses/{analysis_id}/findings/{finding_id}/disposition",
    response_model=FindingDispositionResponse,
    status_code=200,
)
async def set_finding_disposition_route(
    request: Request,
    analysis_id: UUID,
    finding_id: UUID,
    body: FindingDispositionRequest,
):
    try:
        return await run_in_threadpool(
            set_disposition,
            lifecycle(request).repository,
            request.state.owner_hash,
            analysis_id,
            finding_id,
            body,
        )
    except AnalysisNotFound:
        raise HTTPException(404, "Finding or analysis not found") from None
