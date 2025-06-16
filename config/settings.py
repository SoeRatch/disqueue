# config/settings.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379/0"
    job_stream_high: str = "job_stream_high"
    job_stream_medium: str = "job_stream_medium"
    job_stream_low: str = "job_stream_low"
    job_status_hash: str = "job_status"
    job_retry_hash: str = "job_retries"
    max_retries: int = 3
    default_priority: str = "medium"
    job_last_ids_hash: str = "job_last_ids"
    job_dlq_stream: str = "job:dlq"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow"
    )

settings = Settings()
