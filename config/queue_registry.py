# config/queue_registry.py

from core.queue_config import QueueConfig

# Users can modify this file to register any number of queues with custom config
# This is business-logic agnostic and suitable for open-source usage

REGISTERED_QUEUES = [
    QueueConfig(name="default"), # implies all allowed priorities
    # Example:
    QueueConfig(name="image_processing", priorities=["high", "medium", "low"], retry_strategy="exponential"), # custom subset
    QueueConfig(name="email", priorities=["high", "default"],retry_strategy="fixed"),  # Custom subset
    QueueConfig(name="billing", retry_strategy="exponential", retry_limit=5, enable_dlq=True),

]
