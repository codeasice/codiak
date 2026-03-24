"""YNAB API rate limiter — sliding window, 200 req/hr."""
import time
import logging
from collections import deque

logger = logging.getLogger("dragon_keeper.rate_limiter")

YNAB_RATE_LIMIT = 200
WINDOW_SECONDS = 3600


class RateLimiter:
    def __init__(self, max_requests: int = YNAB_RATE_LIMIT, window: int = WINDOW_SECONDS):
        self._max = max_requests
        self._window = window
        self._timestamps: deque[float] = deque()

    def _prune(self):
        cutoff = time.monotonic() - self._window
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    def acquire(self) -> bool:
        self._prune()
        if len(self._timestamps) >= self._max:
            return False
        self._timestamps.append(time.monotonic())
        return True

    def wait_and_acquire(self, timeout: float = 60.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.acquire():
                return True
            time.sleep(0.5)
        return False

    @property
    def remaining(self) -> int:
        self._prune()
        return max(0, self._max - len(self._timestamps))


ynab_limiter = RateLimiter()
