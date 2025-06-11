# worker/worker.py

import json
import time
from task_queues.redis_queue import (
    r, JOB_STREAM, get_job_status, mark_job_status,
    increment_retry_count, clear_retry_count,
    MAX_RETRIES
)

STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_RETRYING = "retrying"
STATUS_FAILED = "failed"

import logging
from config.logging_config import configure_logging
configure_logging()

def process(payload: dict):
    logging.info("Processing:", payload)
    time.sleep(10)
    if payload.get("fail"):
        raise Exception("Simulated failure")


def handle_success(job_id: str):
    mark_job_status(job_id, STATUS_COMPLETED)
    clear_retry_count(job_id)
    logging.info(f"Job {job_id} completed successfully.")


def handle_failure(job_id: str, payload: dict, error: Exception):
    logging.warning(f"Job - {job_id} failed: {error}")
    retries = increment_retry_count(job_id)

    if retries < MAX_RETRIES:
        mark_job_status(job_id, STATUS_RETRYING)
        r.xadd(JOB_STREAM, {"job_id": job_id, "payload": json.dumps(payload)})
        logging.info(f"Retrying job {job_id}, attempt - {retries}")
    else:
        mark_job_status(job_id, STATUS_FAILED)
        clear_retry_count(job_id)
        logging.error(f"Job {job_id} reached max retries. Marked as failed.")

def start_worker():
    logging.info("Worker started...")
    last_id = "$" # start with new entries
    while True:
        try:
            # Continuously listens to Redis Stream (XREAD) .
            res = r.xread({JOB_STREAM: last_id}, block=5000, count=1)
            if not res:
                continue

            _, messages = res[0]
            last_id = messages[-1][0] # latest message ID
            for msg_id, msg_data in messages:
                job_id = msg_data.get("job_id")
                payload = json.loads(msg_data.get("payload", "{}"))

                logging.info(f"\nReceived job {job_id}")

                current_status = get_job_status(job_id)
                if current_status != STATUS_RETRYING:
                    mark_job_status(job_id, STATUS_IN_PROGRESS)

                try:
                    process(payload)
                    handle_success(job_id)
                except Exception as e:
                    handle_failure(job_id, payload, e)

        except Exception as e:
            logging.error("Worker error:", e)
            time.sleep(1)

if __name__ == "__main__":
    start_worker()
