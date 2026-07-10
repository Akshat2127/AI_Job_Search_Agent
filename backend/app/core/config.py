from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "JobAgent AI"
    app_version: str = "1.0.0"
    database_url: str = "sqlite:///./jobagent.db"
    app_env: str = "local"
    llm_provider: str = "mock"
    openai_api_key: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
