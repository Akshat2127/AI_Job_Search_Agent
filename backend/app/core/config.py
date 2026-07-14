from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "JobAgent AI"
    app_version: str = "1.0.0"
    database_url: str = "sqlite:///./jobagent.db"
    app_env: str = "local"
    llm_provider: str = "mock"
    openai_api_key: str | None = None

settings = Settings()
