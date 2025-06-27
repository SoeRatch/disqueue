# core/worker.py

import json
import time
import logging
import signal
import threading

from core.processor import JobProcessor
from core.status import STATUS_CANCELLED
from core.registry import get_registered_queues

from infrastructure.redis_conn import redis_client
from infrastructure.redis_job_store import RedisJobStore
from infrastructure.redis_stream import QueueStreamManager

from config.logging_config import configure_logging
from retry.factory import get_retry_strategy


configure_logging()


# Thread-safe event flag for shutdown
shutdown_event = threading.Event()

def handle_shutdown_signal(signum, frame):
    logging.info(f"\n[signal] Received shutdown signal ({signum}). Finishing current job then exiting...")
    shutdown_event.set()

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown_signal)
signal.signal(signal.SIGTERM, handle_shutdown_signal)


def start_worker():
    logging.info("[worker] Starting worker...")

    job_store = RedisJobStore(redis_client)

    queues = get_registered_queues()  # returns list[DisqueueQueue]
    logging.info(f"Registered queues: {[q.name for q in queues]}")
    stream_managers = [(q, QueueStreamManager(q,job_store)) for q in queues]

    
    retry_strategy = get_retry_strategy()
    processor = JobProcessor(job_store, retry_strategy)
    
    while not shutdown_event.is_set():
        try:
            for queue, stream_manager in stream_managers:
                result = stream_manager.get_next_job()
                if not result:
                    time.sleep(0.1)  # small cooldown to avoid CPU spin
                    continue

                stream, msg_id, msg_data = result

                job_id = msg_data.get("job_id")
                payload = json.loads(msg_data.get("payload", "{}"))

                logging.info(f"[worker] Received job {job_id} from {stream}")

                current_status = job_store.get_job_status(job_id)
                if current_status == STATUS_CANCELLED:
                    logging.info(f"[worker] Skipping cancelled job {job_id}")
                    stream_manager.mark_processed(stream, msg_id)
                    continue  # Skip processing this job

                result = processor.execute(queue, job_id, payload, stream)

                # Regardless of success/failure/duplicate, we mark the message as handled
                stream_manager.mark_processed(stream, msg_id)

        except Exception as e:
            logging.error(f"[worker] Error during job processing loop: {e}")
            time.sleep(1)
            
    logging.info("[worker] Graceful shutdown complete.")

if __name__ == "__main__":
    start_worker()
