# task_queues/redis_queue.py

import redis
import json
from config.settings import settings

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

JOB_STREAM = settings.job_stream
JOB_STATUS_HASH = settings.job_status_hash

JOB_RETRY_HASH = settings.job_retry_hash
MAX_RETRIES = settings.max_retries


def enqueue_job(job_id: str, payload: dict) -> bool:
    try:
        # xadd adds message to stream which has a log-like structure.
        r.xadd(JOB_STREAM, {"job_id": job_id, "payload": json.dumps(payload)})

        # hset sets field in hash. hashes are efficient for storing per-job metadata (like status)
        r.hset(JOB_STATUS_HASH, job_id, "queued")

        # Initialize retry count
        r.hset(JOB_RETRY_HASH, job_id, 0)
        return True
    except Exception as e:
        print(f"Enqueue error: {e}")
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