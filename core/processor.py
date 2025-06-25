# jobs/processor.py

import time
import json
import logging

from task_queues.redis_queue import (
    r, mark_job_status, increment_retry_count,
    clear_retry_count, send_to_dlq
)
from config.status_codes import (
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
    STATUS_RETRYING,
    STATUS_FAILED
)
from utils.deduplication import deduplicated, get_dedup_key


class JobProcessor:
    def __init__(self, retry_strategy):
        self.retry_strategy = retry_strategy

    @deduplicated(on_first_attempt=lambda job_id: mark_job_status(job_id, STATUS_IN_PROGRESS))
    def safe_process(self, job_id: str, payload: dict):
        logging.info(f"Processing: {job_id} -> {payload}")
        time.sleep(10)
        if payload.get("fail"):
            raise Exception("Simulated failure")

    def execute(self, job_id: str, payload: dict, stream: str) -> str:
        try:
            result = self.safe_process(job_id, payload)
            if result == "duplicate":
                return "duplicate"
            self._handle_success(job_id)
            return "completed"
        except Exception as e:
            return self._handle_failure(job_id, payload, stream, e)

    def _handle_success(self, job_id: str):
        mark_job_status(job_id, STATUS_COMPLETED)
        clear_retry_count(job_id)
        logging.info(f"Job {job_id} completed successfully.")

    def _handle_failure(self, job_id: str, payload: dict, stream: str, error: Exception):
        logging.warning(f"Job - {job_id} failed: {error}")
        retries = increment_retry_count(job_id)

        if self.retry_strategy.should_retry(retries):
            mark_job_status(job_id, STATUS_RETRYING)

            delay = self.retry_strategy.get_delay(retries)
            if delay > 0:
                time.sleep(delay)

            r.xadd(stream, {"job_id": job_id, "payload": json.dumps(payload)})

            r.delete(get_dedup_key(job_id))  # release deduplication lock so other workers can pick it up if the current is busy.
            logging.info(f"Retrying job {job_id}, attempt - {retries} with delay - {delay} seconds")
            return "retrying"
        else:
            mark_job_status(job_id, STATUS_FAILED)
            clear_retry_count(job_id)
            send_to_dlq(job_id, payload, reason=str(error))
            r.delete(get_dedup_key(job_id))  # cleanup
            logging.error(f"Job {job_id} reached max retries. Marked as failed.")
            return "failed"
