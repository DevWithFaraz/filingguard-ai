"""FastAPI routes for saved matters."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from filingguard.core.admission import lifecycle
from filingguard.db.repository import AnalysisNotFound
from filingguard.modules.matters.schemas import (
    MatterCreate,
    MatterDetail,
    MatterSummary,
)
from filingguard.modules.matters.service import (
    MatterConflict,
    assign_analysis_matter,
    create_matter,
    delete_matter,
    get_matter,
    list_matters,
)

router = APIRouter(tags=["Saved matters"])


@router.post("/matters", response_model=MatterSummary, status_code=201)
async def create_matter_route(request: Request, body: MatterCreate):
    try:
        return await run_in_threadpool(
            create_matter,
            lifecycle(request).repository,
            request.state.owner_hash,
            body,
        )
    except MatterConflict:
        raise HTTPException(409, "Matter name already exists") from None


@router.get("/matters", response_model=list[MatterSummary])
async def list_matters_route(request: Request):
    return await run_in_threadpool(
        list_matters, lifecycle(request).repository, request.state.owner_hash
    )


@router.get("/matters/{matter_id}", response_model=MatterDetail)
async def get_matter_route(request: Request, matter_id: UUID):
    try:
        return await run_in_threadpool(
            get_matter,
            lifecycle(request).repository,
            request.state.owner_hash,
            matter_id,
        )
    except AnalysisNotFound:
        raise HTTPException(404, "Matter not found") from None


@router.delete("/matters/{matter_id}", status_code=200)
async def delete_matter_route(request: Request, matter_id: UUID):
    try:
        await run_in_threadpool(
            delete_matter,
            lifecycle(request).repository,
            request.state.owner_hash,
            matter_id,
        )
        return {"deleted": True}
    except AnalysisNotFound:
        raise HTTPException(404, "Matter not found") from None


@router.post("/matters/{matter_id}/analyses/{analysis_id}", status_code=200)
async def assign_matter_route(request: Request, matter_id: UUID, analysis_id: UUID):
    try:
        await run_in_threadpool(
            assign_analysis_matter,
            lifecycle(request).repository,
            request.state.owner_hash,
            analysis_id,
            matter_id,
        )
        return {"assigned": True}
    except AnalysisNotFound:
        raise HTTPException(404, "Matter or analysis not found") from None


@router.delete("/matters/{matter_id}/analyses/{analysis_id}", status_code=200)
async def unassign_matter_route(request: Request, matter_id: UUID, analysis_id: UUID):
    try:
        await run_in_threadpool(
            assign_analysis_matter,
            lifecycle(request).repository,
            request.state.owner_hash,
            analysis_id,
            None,
        )
        return {"unassigned": True}
    except AnalysisNotFound:
        raise HTTPException(404, "Analysis not found") from None
