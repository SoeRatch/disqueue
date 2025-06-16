# task_queues/redis_queue.py

import redis
import json
from config.settings import settings

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

# JOB_STREAM = settings.job_stream
JOB_STATUS_HASH = settings.job_status_hash

JOB_RETRY_HASH = settings.job_retry_hash
MAX_RETRIES = settings.max_retries

JOB_LAST_ID_HASH = settings.job_last_ids_hash
STATUS_CANCELLED = "cancelled"


import logging
from config.logging_config import configure_logging
configure_logging()

def enqueue_job(job_id: str, payload: dict, priority: str = settings.default_priority) -> bool:
    try:
        stream_name = getattr(settings, f"job_stream_{priority}")

        # xadd adds message to stream which has a log-like structure.
        r.xadd(stream_name,{
            "job_id": job_id,
            "payload": json.dumps(payload),
            "priority": priority
            })

        # hset sets field in hash. hashes are efficient for storing per-job metadata (like status)
        r.hset(JOB_STATUS_HASH, job_id, "queued")

        # Initialize retry count
        r.hset(JOB_RETRY_HASH, job_id, 0)
        return True
    except Exception as e:
        logging.error(f"Enqueue error: {e}")
        return False
    

# Reads the job's status from the Redis Hash.
def get_job_status(job_id: str) -> str:
    # hget gets field in hash.
    return r.hget(JOB_STATUS_HASH, job_id)


# Updates the status in the Redis Hash.
def mark_job_status(job_id: str, status: str):
    r.hset(JOB_STATUS_HASH, job_id, status)


# Retry helpers
def increment_retry_count(job_id: str) -> int:
    return r.hincrby(JOB_RETRY_HASH, job_id, 1)

def get_retry_count(job_id: str) -> int:
    retry_count = r.hget(JOB_RETRY_HASH, job_id)
    return int(retry_count) if retry_count else 0

def clear_retry_count(job_id: str):
    r.hdel(JOB_RETRY_HASH, job_id)


# last ids helpers
def get_last_id(stream: str) -> str:
    # "0" reads from the beginning of the stream. Better for fault-tolerant and durability.
    # where as "$" reads only new messages, ones added after this command is run.
    # Initialize last_ids from Redis or fallback to "0"
    return r.hget(JOB_LAST_ID_HASH, stream) or "0"

def set_last_id(stream: str, msg_id: str):
    r.hset(JOB_LAST_ID_HASH, stream, msg_id)


# Clears the saved last IDs for all priority streams.
# Useful during development or testing to reprocess all jobs from the beginning of each stream.
# Should not be used in production unless we are intentionally replaying jobs.
def clear_last_ids():
    r.delete(JOB_LAST_ID_HASH)



def send_to_dlq(job_id: str, payload: dict, reason: str = "Maximum retries exceeded"):
    try:
        dlq_payload = {
            "job_id": job_id,
            "payload": json.dumps(payload),
            "reason": reason,
        }
        r.xadd(settings.job_dlq_stream, dlq_payload)
        logging.info(f"Job {job_id} moved to DLQ: {reason}")
    except Exception as e:
        logging.error(f"Failed to add job {job_id} to DLQ: {e}")


def cancel_job(job_id: str):
    if r.hexists(JOB_STATUS_HASH, job_id):
        r.hset(JOB_STATUS_HASH, job_id, STATUS_CANCELLED)
        logging.info(f"Job {job_id} has been cancelled.")
        return True
    else:
        logging.warning(f"Cancel failed: Job {job_id} not found.")
        return False
