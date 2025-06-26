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
        self.streams = [f"disqueue:{self.name}:{p}" for p in self.priorities]

    def __repr__(self):
        return f"QueueConfig(name={self.name}, priorities={self.priorities})"


class DisqueueQueue:
    def __init__(self, config: QueueConfig, client):
        self.config = config
        self.client = client
        self.name = config.name
        self.streams = config.streams

    def enqueue(self, job_id: str, payload: dict, priority: str = "default") -> bool:
        if priority not in self.config.priorities:
            raise ValueError(
                f"Priority '{priority}' not allowed in queue '{self.name}'. "
                f"Allowed priorities: {self.config.priorities}"
            )
        
        stream_name = f"disqueue:{self.name}:{priority}"
        logging.debug(f"Enqueuing job {job_id} to stream {stream_name} with priority {priority}")
        return enqueue_job(
            client=self.client,
            stream_name=stream_name,
            job_id=job_id,
            payload=payload,
            priority=priority
        )
