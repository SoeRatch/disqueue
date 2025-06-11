# config/settings.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379/0"
    job_stream: str = "job_stream"
    job_status_hash: str = "job_status"
    job_retry_hash: str = "job_retries"
    max_retries: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow"
    )

settings = Settings()
