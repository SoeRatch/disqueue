# utils/deduplication.py

import logging
from functools import wraps
from task_queues.redis_queue import r

def deduplicated(ttl_seconds: int = 3600):
    def decorator(func):
        @wraps(func)
        def wrapper(job_id: str, payload: dict, *args, **kwargs):
            if not job_id:
                logging.error("Missing job_id in payload.")
                raise ValueError("Missing job_id in payload.")

            dedup_key = f"dedup:{job_id}"
            is_first = r.set(dedup_key, "processing", nx=True, ex=ttl_seconds)

            if not is_first:
                logging.info(f"[Deduplication] Duplicate job {job_id}. Skipping.")
                return "duplicate"

            try:
                result = func(job_id, payload, *args, **kwargs)
                r.set(dedup_key, "done", ex=86400)  # Keep for 1 day
                return result
            except Exception:
                r.delete(dedup_key)  # Remove so retry can happen
                raise
        return wrapper
    return decorator
