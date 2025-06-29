# core/queue_config.py

import logging
from config.settings import settings
from infrastructure.redis_job_store import RedisJobStore
from typing import Literal


class QueueConfig:
    
    def __init__(
        self,
        name: str,
        priorities: list[str] = None,
        retry_strategy: Literal["fixed", "exponential"] = "fixed",
        retry_limit: int = None,
        enable_dlq: bool = True
    ):
        self.name = name
        self.priorities = [p.lower() for p in (priorities or settings.ALLOWED_PRIORITIES)]
        self.retry_strategy = retry_strategy
        self.retry_limit = retry_limit or settings.max_retries
        self.enable_dlq = enable_dlq

    @property
    def streams(self):
        """Dynamically generate stream names for each priority level."""
        return [f"disqueue:{self.name}:{p}" for p in self.priorities]
    
    def __repr__(self):
        return (f"QueueConfig(name={self.name}, priorities={self.priorities}, "
                f"retry_strategy={self.retry_strategy}, retry_limit={self.retry_limit})")



class DisqueueQueue:
    def __init__(self, config: QueueConfig, job_store: RedisJobStore):
        self.config = config
        self.job_store = job_store
        self.client = job_store.client  # In case anything else needs the raw Redis client
        self.name = config.name
    
    @property
    def streams(self):
        return self.config.streams

    def enqueue(self, job_id: str, payload: dict, priority: str = "default") -> bool:
        priority = priority.lower()
        if priority not in self.config.priorities:
            raise ValueError(
                f"Priority '{priority}' not allowed in queue '{self.name}'. "
                f"Allowed priorities: {self.config.priorities}"
            )
        
        stream_name = f"disqueue:{self.name}:{priority}"
        logging.debug(f"[enqueue] Enqueuing job {job_id} to stream {stream_name} with priority {priority}")
        return self.job_store.enqueue_job(
            stream_name=stream_name,
            job_id=job_id,
            payload=payload,
            priority=priority
        )
