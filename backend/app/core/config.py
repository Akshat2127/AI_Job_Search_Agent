from typing import Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "JobAgent AI"
    app_version: str = "1.0.0"
    database_url: str = "sqlite:///./jobagent.db"
    app_env: str = "local"
    llm_provider: str = "mock"
    openai_api_key: str | None = None
    log_level: str = "INFO"
    log_format: str = "console"
    cors_origins: list[str] = ["http://localhost:3000"]
    auto_create_tables: bool = False
    auth_mode: str = "development"
    development_user_email: str = "local@jobagent.invalid"
    session_ttl_hours: int = 12
    upload_root: str = "./storage/uploads"
    max_resume_bytes: int = 10 * 1024 * 1024

    @field_validator("app_env")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        value = value.lower()
        if value not in {"local", "test", "production"}:
            raise ValueError("must be local, test, or production")
        return value

    @model_validator(mode="after")
    def reject_insecure_production_defaults(self) -> Self:
        if self.app_env == "production":
            if self.database_url.startswith("sqlite"):
                raise ValueError("production requires PostgreSQL; SQLite is local/test only")
            if self.log_format != "json":
                raise ValueError("production requires LOG_FORMAT=json")
            if self.auto_create_tables:
                raise ValueError("AUTO_CREATE_TABLES must be false in production; use Alembic")
            if self.auth_mode == "development":
                raise ValueError("production cannot use AUTH_MODE=development")
        return self

    @field_validator("auth_mode")
    @classmethod
    def validate_auth_mode(cls, value: str) -> str:
        if value not in {"development", "password"}:
            raise ValueError("must be development or password")
        return value


settings = Settings()
