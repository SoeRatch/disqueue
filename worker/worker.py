# worker/worker.py

import json
import time
from task_queues.redis_queue import (
    r,get_job_status, mark_job_status,
    increment_retry_count, clear_retry_count,
    MAX_RETRIES,
    get_last_id, set_last_id
)
from config.settings import settings

import logging
from config.logging_config import configure_logging
configure_logging()

STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_RETRYING = "retrying"
STATUS_FAILED = "failed"

priority_streams = [
    settings.job_stream_high,
    settings.job_stream_medium,
    settings.job_stream_low
]


# Get last_ids of all priority streams
last_ids = {
    stream: get_last_id(stream)
    for stream in priority_streams
}


def process(payload: dict):
    logging.info(f"Processing: {payload}")
    time.sleep(10)
    if payload.get("fail"):
        raise Exception("Simulated failure")


def handle_success(job_id: str):
    mark_job_status(job_id, STATUS_COMPLETED)
    clear_retry_count(job_id)
    logging.info(f"Job {job_id} completed successfully.")


def handle_failure(job_id: str, payload: dict, stream: str, error: Exception):
    logging.warning(f"Job - {job_id} failed: {error}")
    retries = increment_retry_count(job_id)

    if retries < MAX_RETRIES:
        mark_job_status(job_id, STATUS_RETRYING)
        r.xadd(stream, {"job_id": job_id, "payload": json.dumps(payload)})
        logging.info(f"Retrying job {job_id}, attempt - {retries}")
    else:
        mark_job_status(job_id, STATUS_FAILED)
        clear_retry_count(job_id)
        logging.error(f"Job {job_id} reached max retries. Marked as failed.")


def start_worker():
    logging.info("Worker started...")

    while True:
        try:
            job_found = False

            for stream in priority_streams:
                
                # Read from the current priority stream using XREAD.
                # # r.xread({stream: ID}) returns messages with IDs strictly greater than the given ID.
                # # This ensures the same message is not processed twice.
                res = r.xread({stream: last_ids[stream]}, block=1000, count=1)
                if not res:
                    continue

                _, messages = res[0]
                msg_id, msg_data = messages[0]

                job_id = msg_data.get("job_id")
                payload = json.loads(msg_data.get("payload", "{}"))

                logging.info(f"\nReceived job {job_id} from {stream}")

                current_status = get_job_status(job_id)
                if current_status != STATUS_RETRYING:
                    mark_job_status(job_id, STATUS_IN_PROGRESS)
                
                try:
                    process(payload)
                    handle_success(job_id)
                except Exception as e:
                    handle_failure(job_id, payload,stream, e)
                
                # Persist the new last_id for this stream
                last_ids[stream] = msg_id
                set_last_id(stream, msg_id)

                job_found = True

                # Break after processing one job to re-check highest priority stream again
                break
                
            if not job_found:
                time.sleep(0.1)  # small cooldown to avoid CPU spin

        except Exception as e:
            logging.error("Worker error:", e)
            time.sleep(1)

if __name__ == "__main__":
    start_worker()
