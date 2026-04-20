"""Configuration management using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    environment: str = "development"
    log_level: str = "INFO"
    api_key_header: str = "X-API-Key"
    allowed_api_keys: str = "dev-key"

    claims_api_url: str = "http://localhost:9000/api"
    member_api_url: str = "http://localhost:9000/api"
    denial_code_api_url: str = "http://localhost:9000/api"
    mcp_server_url: str = "http://localhost:3001"

    anthropic_api_key: str | None = None
    parse_model: str = "claude-haiku-4-5-20251001"
    explain_model: str = "claude-sonnet-4-6"

    # LangSmith Tracing
    langsmith_api_key: str | None = None
    langchain_tracing_v2: bool = False
    langchain_project: str = "HealthCareStatusClaims"

    chroma_collection_name: str = "policies"
    chroma_persist_dir: str = "./data/chroma"

    mock_mode: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    @property
    def api_keys(self) -> list[str]:
        """Return configured API keys as a list."""
        return [key.strip() for key in self.allowed_api_keys.split(",") if key.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
