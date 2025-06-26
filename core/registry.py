from config.queue_registry import REGISTERED_QUEUES
from core.queue import DisqueueQueue
from infrastructure.redis_conn import redis_client

def get_registered_queues():
    return [DisqueueQueue(config, redis_client) for config in REGISTERED_QUEUES]
