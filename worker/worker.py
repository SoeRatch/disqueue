# worker/worker.py

import json
import time
import logging
from task_queues.redis_queue import (
    r, get_job_status, get_last_id, set_last_id
)
from config.status_codes import (
    STATUS_CANCELLED
)
from config.settings import settings
from config.logging_config import configure_logging
from retry.factory import get_retry_strategy
from jobs.processor import JobProcessor

configure_logging()

priority_streams = [
    settings.job_stream_high,
    settings.job_stream_medium,
    settings.job_stream_low
]

retry_strategy = get_retry_strategy()


# Get last_ids of all priority streams
last_ids = {
    stream: get_last_id(stream)
    for stream in priority_streams
}

processor = JobProcessor(retry_strategy)


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
                
                if current_status == STATUS_CANCELLED:
                    logging.info(f"Job {job_id} is cancelled. Skipping.")
                    # Advance last_id even if skipped, so we don't re-read the same cancelled job
                    last_ids[stream] = msg_id
                    set_last_id(stream, msg_id)
                    job_found = True
                    continue  # Skip this job
                
                result = processor.execute(job_id, payload, stream)

                # Regardless of success/failure/duplicate, we mark the message as handled
                last_ids[stream] = msg_id
                set_last_id(stream, msg_id)

                job_found = True 

                break # Break after processing one job to re-check highest priority stream again
                
            if not job_found:
                time.sleep(0.1)  # small cooldown to avoid CPU spin

        except Exception as e:
            logging.error("Worker error:", e)
            time.sleep(1)

if __name__ == "__main__":
    start_worker()
