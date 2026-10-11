from fastapi import APIRouter, HTTPException, Query, Response

from filingguard.modules.analyses.demo import DemoUnavailable
from filingguard.modules.analyses.demo_preview import FIXTURE_ROOT, DemoPreview, load_demo_preview

router = APIRouter(tags=["Reviewed demo examples"])


@router.get("/demos/{fixture_id}", response_model=DemoPreview)
def demo_preview(response: Response, fixture_id: str, mode: str = Query(...)) -> DemoPreview:
    response.headers["Cache-Control"] = "no-store"
    if mode != "demo":
        raise HTTPException(422, "Explicit demo mode is required")
    if fixture_id != "curated-v1":
        raise HTTPException(404, "Unknown demo fixture")
    try:
        return load_demo_preview(FIXTURE_ROOT, fixture_id, mode=mode)
    except DemoUnavailable as error:
        raise HTTPException(503, "Reviewed demo is unavailable") from error
