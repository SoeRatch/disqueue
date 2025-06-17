# retry/strategies.py

import abc
import time

class RetryStrategy(abc.ABC):
    @abc.abstractmethod
    def should_retry(self, job_id: str, retries: int) -> bool:
        pass

    @abc.abstractmethod
    def get_delay(self, retries: int) -> float:
        pass


class FixedRetryStrategy(RetryStrategy):
    def __init__(self, max_retries: int, delay: float):
        self.max_retries = max_retries
        self.delay = delay

    def should_retry(self, job_id: str, retries: int) -> bool:
        return retries < self.max_retries

    def get_delay(self, retries: int) -> float:
        return self.delay


class ExponentialBackoffStrategy(RetryStrategy):
    def __init__(self, max_retries: int, base_delay: float = 1.0, factor: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.factor = factor

    def should_retry(self, job_id: str, retries: int) -> bool:
        return retries < self.max_retries

    def get_delay(self, retries: int) -> float:
        delay = self.base_delay * (self.factor ** (retries - 1)) if retries > 0 else 0.0
        return min(60, delay)  # cap at 60 seconds

