from config.queue_registry import REGISTERED_QUEUES
from core.queue import DisqueueQueue
from infrastructure.redis_conn import redis_client

def get_registered_queues():
    """
    Loads statically registered queues from config.queue_registry
    and returns a list of initialized DisqueueQueue instances.
    """
    return [DisqueueQueue(config, redis_client) for config in REGISTERED_QUEUES]
