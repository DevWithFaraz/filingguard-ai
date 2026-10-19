"""FastAPI routes for multi-filing batch processing."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from filingguard.core.admission import lifecycle
from filingguard.db.repository import AnalysisNotFound
from filingguard.modules.batches.schemas import (
    BatchCreate,
    BatchDetail,
    BatchSummary,
)
from filingguard.modules.batches.service import (
    cancel_batch,
    create_batch_analyses,
    get_batch,
    list_batches,
)

router = APIRouter(tags=["Batch review"])


@router.post("/batches", response_model=BatchSummary, status_code=201)
async def create_batch_route(request: Request, body: BatchCreate):
    try:
        return await run_in_threadpool(
            create_batch_analyses,
            lifecycle(request),
            request.state.owner_hash,
            request.state.session_expiry,
            body,
        )
    except Exception as error:
        raise HTTPException(422, f"Batch preparation failed: {error}") from error


@router.get("/batches", response_model=list[BatchSummary])
async def list_batches_route(request: Request):
    return await run_in_threadpool(
        list_batches,
        lifecycle(request).repository,
        request.state.owner_hash,
    )


@router.get("/batches/{batch_id}", response_model=BatchDetail)
async def get_batch_route(request: Request, batch_id: UUID):
    try:
        return await run_in_threadpool(
            get_batch,
            lifecycle(request).repository,
            request.state.owner_hash,
            batch_id,
        )
    except AnalysisNotFound:
        raise HTTPException(404, "Batch not found") from None


@router.post("/batches/{batch_id}/cancel", response_model=BatchSummary, status_code=200)
async def cancel_batch_route(request: Request, batch_id: UUID):
    try:
        return await run_in_threadpool(
            cancel_batch,
            lifecycle(request).repository,
            request.state.owner_hash,
            batch_id,
        )
    except AnalysisNotFound:
        raise HTTPException(404, "Batch not found") from None
