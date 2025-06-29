# retry/factory.py
from config.settings import settings
from retry.strategies import FixedRetryStrategy, ExponentialBackoffStrategy

def get_retry_strategy(strategy_name: str = None, retry_limit: int = None):
    name = strategy_name or settings.retry_strategy
    limit = retry_limit or settings.max_retries

    if name.lower() == "exponential":
        return ExponentialBackoffStrategy(
            max_retries=limit,
            base_delay=settings.exponential_base_delay,
            factor=settings.exponential_factor
        )
    else:
        return FixedRetryStrategy(
            max_retries=limit,
            delay=settings.fixed_retry_delay
        )
