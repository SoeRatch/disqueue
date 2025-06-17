# config/settings.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Job config
    job_stream_high: str = "job_stream_high"
    job_stream_medium: str = "job_stream_medium"
    job_stream_low: str = "job_stream_low"
    job_status_hash: str = "job_status"
    job_retry_hash: str = "job_retries"
    job_last_ids_hash: str = "job_last_ids"
    default_priority: str = "medium"
    job_dlq_stream: str = "job:dlq"

    # Retry config
    retry_strategy: str = "exponential"  # or "fixed"
    max_retries: int = 3
    fixed_retry_delay: float = 1.0
    exponential_base_delay: float = 1.0
    exponential_factor: float = 2.0

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow"
    )

settings = Settings()

