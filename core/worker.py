# core/worker.py

import json
import time
import logging
import signal
import threading

from infrastructure.redis_queue import (
   get_job_status
)
from core.status import (
    STATUS_CANCELLED
)
from config.settings import settings
from config.logging_config import configure_logging
from retry.factory import get_retry_strategy
from core.processor import JobProcessor
from infrastructure.redis_stream import StreamManager

configure_logging()

priority_streams = [
    settings.job_stream_high,
    settings.job_stream_medium,
    settings.job_stream_low
]

retry_strategy = get_retry_strategy()
processor = JobProcessor(retry_strategy)
stream_manager = StreamManager(priority_streams)

# Thread-safe event flag for shutdown
shutdown_event = threading.Event()

def handle_shutdown_signal(signum, frame):
    logging.info(f"\nReceived shutdown signal ({signum}). Finishing current job then exiting...")
    shutdown_event.set()

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown_signal)
signal.signal(signal.SIGTERM, handle_shutdown_signal)

def start_worker():
    logging.info("Worker started...")

    while not shutdown_event.is_set():
        try:

            result = stream_manager.get_next_job()
            if not result:
                time.sleep(0.1)  # small cooldown to avoid CPU spin
                continue

            stream, msg_id, msg_data = result

            job_id = msg_data.get("job_id")
            payload = json.loads(msg_data.get("payload", "{}"))

            logging.info(f"\nReceived job {job_id} from {stream}")

            current_status = get_job_status(job_id)
            if current_status == STATUS_CANCELLED:
                logging.info(f"Job {job_id} is cancelled. Skipping.")
                stream_manager.mark_processed(stream, msg_id)
                continue  # Skip processing this job

            result = processor.execute(job_id, payload, stream)

            # Regardless of success/failure/duplicate, we mark the message as handled
            stream_manager.mark_processed(stream, msg_id)

        except Exception as e:
            logging.error("Worker error:", e)
            time.sleep(1)
            
    logging.info("Graceful shutdown complete. Worker exiting.")

if __name__ == "__main__":
    start_worker()
