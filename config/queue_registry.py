# config/queue_registry.py

from core.queue import QueueConfig

# Users can modify this file to register any number of queues with custom config
# This is business-logic agnostic and suitable for open-source usage

REGISTERED_QUEUES = [
    QueueConfig(name="default"),
    # Example:
    # QueueConfig(name="image_processing", priorities=["high", "low"], retry_limit=5),
    # QueueConfig(name="billing", enable_dlq=False),
]
