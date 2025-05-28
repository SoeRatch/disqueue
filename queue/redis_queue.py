# queue/redis_queue.py

import redis
import json
from config.settings import settings

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

JOB_STREAM = "job_stream"
JOB_STATUS_HASH = "job_status"

def enqueue_job(job_id: str, payload: dict) -> bool:
    try:
        r.xadd(JOB_STREAM, {"job_id": job_id, "payload": json.dumps(payload)})
        r.hset(JOB_STATUS_HASH, job_id, "queued")
        return True
    except Exception as e:
        print(f"Enqueue error: {e}")
        return False

def get_job_status(job_id: str) -> str:
    return r.hget(JOB_STATUS_HASH, job_id)

def mark_job_status(job_id: str, status: str):
    r.hset(JOB_STATUS_HASH, job_id, status)
