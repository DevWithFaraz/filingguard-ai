from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from filingguard.core.admission import lifecycle
from filingguard.modules.identity.schemas import (
    IdentityClaimed,
    IdentityClaimRequest,
    IdentityLoginRequest,
    IdentityMigrationResponse,
    IdentitySessionIssued,
)
from filingguard.modules.identity.service import (
    IdentityClaimConflict,
    IdentityLoginFailed,
    claim_owner,
    current_identity,
    login_owner,
    migrate_owner_analyses,
)

router = APIRouter()


@router.post("/identities", response_model=IdentityClaimed, status_code=201)
async def claim_identity(request: Request, body: IdentityClaimRequest):
    try:
        return await run_in_threadpool(
            claim_owner,
            lifecycle(request).repository,
            request.state.owner_hash,
            body.username,
            body.secret,
        )
    except IdentityClaimConflict:
        raise HTTPException(409) from None


@router.post("/identities/login", response_model=IdentitySessionIssued, status_code=201)
async def login_identity(request: Request, body: IdentityLoginRequest):
    try:
        return await run_in_threadpool(
            login_owner, lifecycle(request).repository, body.username, body.secret
        )
    except IdentityLoginFailed:
        raise HTTPException(401) from None
    except OverflowError:
        raise HTTPException(429, headers={"Retry-After": "60"}) from None


@router.post(
    "/identities/migrate",
    response_model=IdentityMigrationResponse,
    status_code=200,
)
async def migrate_identity(request: Request, body: IdentityLoginRequest):
    try:
        count, session = await run_in_threadpool(
            migrate_owner_analyses,
            lifecycle(request).repository,
            request.state.owner_hash,
            body.username,
            body.secret,
        )
        return IdentityMigrationResponse(migrated_count=count, session=session)
    except IdentityLoginFailed:
        raise HTTPException(401) from None
    except OverflowError:
        raise HTTPException(429, headers={"Retry-After": "60"}) from None


@router.get("/identities/me", response_model=IdentityClaimed)
async def identity_me(request: Request):
    try:
        return await run_in_threadpool(
            current_identity, lifecycle(request).repository, request.state.owner_hash
        )
    except IdentityLoginFailed:
        raise HTTPException(404) from None
