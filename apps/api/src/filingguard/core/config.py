from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=API_ROOT / ".env", extra="ignore")

    app_name: str = "FilingGuard AI"
    private_storage_directory: Path | None = None
    cleanup_interval_seconds: int = Field(default=60, ge=1, le=3600)
    intake_enabled: bool = False
    analysis_timeout_seconds: float = Field(default=90, gt=0, le=300, allow_inf_nan=False)
    review_stage_timeout_seconds: float = Field(default=30, gt=0, le=300, allow_inf_nan=False)
    max_provider_attempts: int = Field(default=60, ge=1, le=60)
    courtlistener_api_token: str | None = None
    statute_source_url: str | None = None
    source_verification_enabled: bool = False
    semantic_review_enabled: bool = False
    groq_api_key: SecretStr | None = None
    groq_model: str = "openai/gpt-oss-120b"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
