from typing import Literal
from urllib.parse import urlsplit

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from sqlalchemy import text

from filingguard.core.config import API_ROOT

router = APIRouter(tags=["health"])


def _credential_configured(value: str | None) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 4096
        and all(33 <= ord(character) <= 126 for character in value)
    )


def _exact_origins(origins: list[str]) -> bool:
    try:
        for origin in origins:
            parsed = urlsplit(origin)
            if (
                not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
                or "*" in origin
                or parsed.scheme not in {"http", "https"}
            ):
                return False
            if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
                return False
            _ = parsed.port
        return bool(origins)
    except ValueError:
        return False


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness only; does not claim database or provider readiness."""
    return HealthResponse()


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: dict[str, bool]
    limitation: str = (
        "Local dependencies only; provider availability and hosted acceptance are separate."
    )


@router.get(
    "/ready", response_model=ReadinessResponse, responses={503: {"model": ReadinessResponse}}
)
def readiness(request: Request, response: Response) -> ReadinessResponse:
    """Fail closed without migrations; no provider request or schema mutation."""
    settings = request.app.state.settings
    runtime = request.app.state.analysis_runtime
    checks = {
        "intake_enabled": settings.intake_enabled,
        "private_storage": settings.private_storage_directory is not None,
        "cleanup": not runtime.cleanup_failed,
        "exact_origins": _exact_origins(settings.cors_origins),
        "database_schema": False,
        "provider_configuration": (
            (
                not settings.semantic_review_enabled
                or _credential_configured(
                    settings.groq_api_key.get_secret_value() if settings.groq_api_key else None
                )
                and settings.groq_model == "openai/gpt-oss-120b"
            )
            and (
                not settings.source_verification_enabled
                or _credential_configured(settings.courtlistener_api_token)
            )
        ),
    }
    # Maintenance owns lazy recovery. Readiness only reads its existing connection.
    with runtime._lock:
        if runtime._engine is not None and runtime.lifecycle is not None:
            try:
                config = Config()
                config.set_main_option("script_location", str(API_ROOT / "migrations"))
                heads = set(ScriptDirectory.from_config(config).get_heads())
                with runtime._engine.connect() as connection:
                    versions = set(
                        connection.execute(
                            text("SELECT version_num FROM alembic_version")
                        ).scalars()
                    )
                    checks["database_schema"] = bool(heads) and versions == heads
            except Exception:
                pass  # Do not expose database errors or configuration values.
    ready = all(checks.values())
    response.status_code = 200 if ready else 503
    response.headers["Cache-Control"] = "no-store"
    return ReadinessResponse(status="ready" if ready else "not_ready", checks=checks)
