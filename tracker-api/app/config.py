"""Settings, loaded from environment variables or the repo-root .env (same pattern as CHIA)."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    environment: str = "development"
    log_level: str = "INFO"

    # Which backend writes summaries: claude_code (your Claude subscription, via the Claude Code
    # CLI on this computer), openai, stub, or auto (OpenAI if a key is set, else Claude Code if
    # installed, else stub).
    summarizer: Literal["auto", "claude_code", "openai", "stub"] = "auto"
    claude_cli: str = "claude"
    claude_code_model: str | None = None  # e.g. haiku, sonnet, opus; empty = your CLI default
    claude_code_timeout_seconds: int = 300
    summary_batch_size: int = 8  # items per Claude Code call
    summaries_per_run: int = 80  # cap per refresh, to go easy on subscription usage limits

    # OpenAI: setting AZURE_OPENAI_ENDPOINT routes calls through Azure, like CHIA.
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    summary_model: str = "gpt-5.4-mini"
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_api_version: str = "2025-04-01-preview"
    azure_summary_deployment: str | None = None

    # Forces stub summaries regardless of SUMMARIZER. Used by tests.
    llm_stub: bool = False

    database_path: str = str(REPO_ROOT / "data" / "tracker.db")
    fetch_interval_minutes: int = 360  # 0 disables the background fetch loop
    items_per_query: int = 5
    max_age_days: int = 30
    allowed_origins: str = "http://localhost:4200"


settings = Settings()
