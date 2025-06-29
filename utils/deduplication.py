# utils/deduplication.py

import logging
from functools import wraps
from infrastructure.redis_conn import redis_client

def deduplicated(ttl_seconds: int = 3600, on_first_attempt=None):
    """
    A decorator function to ensure idempotent job execution.
    
    Args:
        ttl_seconds: How long to keep dedup key (in seconds).
        on_first_attempt: Optional function to call before processing if job is not duplicate.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            # Detect if method or function
            if len(args) == 4:
                # Method: self, job_id, payload, queue_name
                _, job_id, _, _ = args
            elif len(args) == 3:
                # Function: job_id, payload, queue_name
                job_id, _, _= args
            else:
                raise ValueError("Unexpected args format in deduplicated function")
            
            if not job_id:
                logging.error("Missing job_id in payload.")
                raise ValueError("Missing job_id in payload.")

            dedup_key = get_dedup_key(job_id)
            is_first_attempt = redis_client.set(dedup_key, "processing", nx=True, ex=ttl_seconds)
            # logging.info(f"Set dedup key result for {job_id}: {is_first_attempt}")

            if not is_first_attempt:
                logging.info(f"[Deduplication] Duplicate job {job_id}. Skipping.")
                return "duplicate"

            if on_first_attempt:
                try:
                    on_first_attempt(job_id)
                except Exception as hook_error:
                    logging.warning(f"[Deduplication] on_first_attempt failed for {job_id}: {hook_error}")

            try:
                result = func(*args, **kwargs)
                redis_client.set(dedup_key, "done", ex=86400)  # Keep for 1 day
                return result
            except Exception:
                logging.exception(f"[Deduplication] Error processing job {job_id}")
                raise
        return wrapper
    return decorator

def get_dedup_key(job_id: str) -> str:
    return f"dedup:{job_id}"