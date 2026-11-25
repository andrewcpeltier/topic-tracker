"""Settings, loaded from environment variables or the repo-root .env (same pattern as CHIA)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    environment: str = "development"
    log_level: str = "INFO"

    # LLM: OpenAI by default; setting AZURE_OPENAI_ENDPOINT routes calls through Azure, like CHIA.
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    summary_model: str = "gpt-5.4-mini"
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_api_version: str = "2025-04-01-preview"
    azure_summary_deployment: str | None = None

    # When true (or no API key is set), summaries come from a deterministic stub. Used by tests.
    llm_stub: bool = False

    database_path: str = str(REPO_ROOT / "data" / "tracker.db")
    fetch_interval_minutes: int = 360  # 0 disables the background fetch loop
    items_per_query: int = 5
    max_age_days: int = 30
    allowed_origins: str = "http://localhost:4200"

    @property
    def use_stub(self) -> bool:
        return self.llm_stub or not (self.openai_api_key or self.azure_openai_endpoint)


settings = Settings()
