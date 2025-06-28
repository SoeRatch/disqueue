# core/processor.py

import time
import json
import logging

from core.status import (
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
    STATUS_RETRYING,
    STATUS_FAILED
)
from utils.deduplication import deduplicated, get_dedup_key
from infrastructure.redis_job_store import RedisJobStore

class JobProcessor:
    def __init__(self, job_store: RedisJobStore, retry_strategy):
        self.job_store = job_store
        self.retry_strategy = retry_strategy

    def execute(self, queue, job_id: str, payload: dict, stream: str) -> str:
        @deduplicated(on_first_attempt=lambda job_id: self.job_store.mark_job_status(job_id, STATUS_IN_PROGRESS))
        def safe_process(job_id: str, payload: dict):
            logging.info(f"[processor] Processing: {job_id} -> {payload}")
            # Simulated processing logic
            time.sleep(10)
            if payload.get("fail"):
                raise Exception("Simulated failure")
        try:
            result = safe_process(job_id, payload)
            if result == "duplicate":
                return "duplicate"
            self._handle_success(job_id)
            return "completed"
        except Exception as e:
            return self._handle_failure(queue, job_id, payload, stream, e)

    def _handle_success(self, job_id: str):
        self.job_store.mark_job_status(job_id, STATUS_COMPLETED)
        self.job_store.clear_retry_count(job_id)
        logging.info(f"[processor] Job {job_id} completed successfully.")

    def _handle_failure(self, queue, job_id: str, payload: dict, stream: str, error: Exception):
        logging.warning(f"Job - {job_id} failed: {error}")
        retries = self.job_store.increment_retry_count(job_id)

        if self.retry_strategy.should_retry(retries):
            self.job_store.mark_job_status(job_id, STATUS_RETRYING)

            delay = self.retry_strategy.get_delay(retries)
            if delay > 0:
                logging.info(f"[processor] Retrying job {job_id} after {delay} seconds...")
                time.sleep(delay)

            # Re-enqueue the job to the same stream
            self.job_store.client.xadd(stream, {
                "job_id": job_id,
                "payload": json.dumps(payload)
            })

            # release deduplication lock so other workers can pick it up if the current is busy.
            self.job_store.client.delete(get_dedup_key(job_id))

            logging.info(f"[processor] Retried job {job_id}, attempt {retries}")
            return "retrying"
        else:
            self.job_store.mark_job_status(job_id, STATUS_FAILED)
            self.job_store.clear_retry_count(job_id)
            if queue.config.enable_dlq:
                self.job_store.send_to_dlq(job_id, payload, reason=str(error))
            self.job_store.client.delete(get_dedup_key(job_id))  # cleanup
            logging.error(f"[processor] Job {job_id} failed permanently.")
            return "failed"
