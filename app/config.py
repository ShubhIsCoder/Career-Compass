from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-me")

    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://career:career@localhost:5432/career_compass")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "45"))

    token_ttl_seconds: int = int(os.getenv("TOKEN_TTL_SECONDS", "604800"))


settings = Settings()
