# core/registry.py

from config.queue_registry import REGISTERED_QUEUES
from core.queue_config import DisqueueQueue
from infrastructure.redis_conn import redis_client
from infrastructure.redis_job_store import RedisJobStore

def get_registered_queues(job_store=None):
    """
    Loads statically registered queues from config.queue_registry
    and returns a list of initialized DisqueueQueue instances.
    Allows injecting a custom job_store for testing and flexibility.
    """
    job_store = job_store or RedisJobStore(redis_client)
    return [DisqueueQueue(config, job_store) for config in REGISTERED_QUEUES]
