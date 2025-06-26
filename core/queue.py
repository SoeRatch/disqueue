import json
import logging
from infrastructure.redis_queue import enqueue_job
from config.settings import settings

class QueueConfig:
    def __init__(
        self,
        name: str,
        priorities=None,
        retry_limit: int = None,
        enable_dlq: bool = True
    ):
        self.name = name
        self.priorities = priorities or ["default"]
        self.retry_limit = retry_limit or settings.max_retries
        self.enable_dlq = enable_dlq
        self.stream = f"disqueue:{self.name}"

    def __repr__(self):
        return f"QueueConfig(name={self.name}, priorities={self.priorities})"


class DisqueueQueue:
    def __init__(self, config: QueueConfig, client):
        self.config = config
        self.client = client
        self.name = config.name
        self.stream = config.stream

    def enqueue(self, job_id: str, payload: dict, priority: str = "default") -> bool:
        logging.debug(f"Enqueuing job {job_id} to stream {self.stream} with priority {priority}")
        return enqueue_job(
            client=self.client,
            stream_name=self.stream,
            job_id=job_id,
            payload=payload,
            priority=priority
        )
