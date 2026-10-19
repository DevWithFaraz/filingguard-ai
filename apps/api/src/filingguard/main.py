from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from filingguard.api.errors import install_error_boundary
from filingguard.api.routes.demos import router as demos_router
from filingguard.api.routes.health import router as health_router
from filingguard.api.routes.identity import router as identity_router
from filingguard.api.routes.intake import router as intake_router
from filingguard.core.admission import Admission, IntakeGuard
from filingguard.core.config import Settings
from filingguard.core.runtime import application_lifespan
from filingguard.modules.analyses.runners import local_runners
from filingguard.modules.batches.routes import router as batches_router
from filingguard.modules.collaboration.routes import router as collaboration_router
from filingguard.modules.matters.routes import router as matters_router


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=application_lifespan(settings))
    install_error_boundary(app)
    app.state.settings = settings
    app.state.admission = Admission()
    app.state.review_runners = local_runners(settings)
    app.add_middleware(IntakeGuard, settings=settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "PATCH"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID", "X-Document-Name"],
    )
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(demos_router, prefix="/api/v1")
    app.include_router(identity_router, prefix="/api/v1")
    app.include_router(matters_router, prefix="/api/v1")
    app.include_router(collaboration_router, prefix="/api/v1")
    app.include_router(batches_router, prefix="/api/v1")
    app.include_router(intake_router, prefix="/api/v1")
    return app


app = create_app()
