# retry/factory.py
from config.settings import settings
from retry.strategies import FixedRetryStrategy, ExponentialBackoffStrategy

def get_retry_strategy(strategy_name: str = None):
    name = strategy_name or settings.retry_strategy
    if name.lower() == "exponential":
        return ExponentialBackoffStrategy(
            max_retries=settings.max_retries,
            base_delay=settings.exponential_base_delay,
            factor=settings.exponential_factor
        )
    else:
        return FixedRetryStrategy(
            max_retries=settings.max_retries,
            delay=settings.fixed_retry_delay
        )
