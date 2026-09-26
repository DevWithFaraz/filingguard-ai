from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from filingguard.api.routes.health import router as health_router
from filingguard.core.config import Settings


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )
    app.include_router(health_router, prefix="/api/v1")
    return app


app = create_app()
