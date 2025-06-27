# infrastructure/redis_job_store.py

import json
import logging

from core.status import STATUS_QUEUED, STATUS_CANCELLED
from config.settings import settings
from config.logging_config import configure_logging


configure_logging()


class RedisJobStore:
    def __init__(self, client):
        self.client = client
        self.job_status_hash = settings.job_status_hash
        self.job_retry_hash = settings.job_retry_hash
        self.job_last_id_hash = settings.job_last_ids_hash
        self.dlq_stream = settings.job_dlq_stream


    def enqueue_job(self, stream_name: str, job_id: str, payload: dict, priority: str = settings.default_priority) -> bool:
        try:
            priority = priority.lower()

            # xadd adds message to stream which has a log-like structure.
            self.client.xadd(stream_name,{
                "job_id": job_id,
                "payload": json.dumps(payload),
                "priority": priority
                })
            
            self.client.hset(self.job_status_hash, job_id, STATUS_QUEUED)

            # Initialize retry count
            self.client.hset(self.job_retry_hash, job_id, 0)
            return True
        except Exception as e:
            logging.error(f"[enqueue_job] Error enqueueing job {job_id} to {stream_name}", exc_info=True)
            return False
    
    def get_job_status(self, job_id: str) -> str:
        """Returns job status or None if not found."""
        return self.client.hget(self.job_status_hash, job_id)


    def mark_job_status(self, job_id: str, status: str):
        """Generic method to update the job's status in Redis."""
        self.client.hset(self.job_status_hash, job_id, status)


    # Retry helpers
    def increment_retry_count(self, job_id: str) -> int:
        return self.client.hincrby(self.job_retry_hash, job_id, 1)

    def get_retry_count(self, job_id: str) -> int:
        retry_count = self.client.hget(self.job_retry_hash, job_id)
        return int(retry_count) if retry_count else 0

    def clear_retry_count(self, job_id: str):
        self.client.hdel(self.job_retry_hash, job_id)


    # last ids helpers
    def get_last_id(self, stream: str) -> str:
        """
        "0" reads from the beginning of the stream. Better for fault-tolerant and durability.
        where as "$" reads only new messages, ones added after this command is run.
        Initialize last_ids from Redis or fallback to "0"
        """
        return self.client.hget(self.job_last_id_hash, stream) or "0"

    def set_last_id(self, stream: str, msg_id: str):
        self.client.hset(self.job_last_id_hash, stream, msg_id)

    def clear_all_last_ids(self):
        """
        Clears the saved last IDs for all priority streams.
        Useful during development or testing to reprocess all jobs from the beginning of each stream.
        Should not be used in production unless we are intentionally replaying jobs.
        """
        self.client.delete(self.job_last_id_hash)



    def send_to_dlq(self, job_id: str, payload: dict, reason: str = "Maximum retries exceeded"):
        try:
            dlq_payload = {
                "job_id": job_id,
                "payload": json.dumps(payload),
                "reason": reason,
            }
            self.client.xadd(self.dlq_stream, dlq_payload)
            logging.info(f"[DLQ] Job {job_id} moved to DLQ: {reason}")
        except Exception as e:
            logging.error(f"[DLQ] Failed to enqueue job {job_id} to DLQ: {e}")

    def cancel_job(self, job_id: str):
        if self.client.hexists(self.job_status_hash, job_id):
            self.client.hset(self.job_status_hash, job_id, STATUS_CANCELLED)
            logging.info(f"[cancel_job] Job {job_id} cancelled.")
            return True
        else:
            logging.warning(f"[cancel_job] Job {job_id} not found.")
            return False
