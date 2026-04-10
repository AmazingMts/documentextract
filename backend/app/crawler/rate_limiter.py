import asyncio
import time
from collections import defaultdict


class DomainRateLimiter:
    """Token-bucket rate limiter: max 2 requests/sec per domain, burst of 5."""

    def __init__(self, rate: float = 2.0, burst: int = 5):
        self.rate = rate
        self.burst = burst
        self._tokens: dict[str, float] = defaultdict(lambda: float(burst))
        self._last_refill: dict[str, float] = defaultdict(time.monotonic)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def acquire(self, domain: str):
        lock = self._locks[domain]
        async with lock:
            now = time.monotonic()
            elapsed = now - self._last_refill[domain]
            self._tokens[domain] = min(
                self.burst,
                self._tokens[domain] + elapsed * self.rate
            )
            self._last_refill[domain] = now

            if self._tokens[domain] < 1.0:
                wait = (1.0 - self._tokens[domain]) / self.rate
                await asyncio.sleep(wait)
                self._tokens[domain] = 0.0
            else:
                self._tokens[domain] -= 1.0


# Global instances
domain_limiter = DomainRateLimiter(rate=2.0, burst=5)
global_semaphore = asyncio.Semaphore(10)


def extract_domain(url: str) -> str:
    from urllib.parse import urlparse
    return urlparse(url).netloc
