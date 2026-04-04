"""Shared async RPM limiter for LLM calls."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable


logger = logging.getLogger(__name__)

_WINDOW_SECONDS = 60.0
_NO_LIMIT = 0


class AsyncWindowRateLimiter:
    """Simple sliding-window async limiter."""

    def __init__(self, requests_per_minute: int, *, time_fn: Callable[[], float] | None = None) -> None:
        self._rpm = max(_NO_LIMIT, int(requests_per_minute))
        self._time_fn = time_fn or time.monotonic
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Block until a request slot is available."""
        if self._rpm <= _NO_LIMIT:
            return

        while True:
            wait_for = 0.0
            async with self._lock:
                now = self._time_fn()
                self._evict_expired(now)

                if len(self._timestamps) < self._rpm:
                    self._timestamps.append(now)
                    return

                oldest = self._timestamps[0]
                wait_for = max(0.0, _WINDOW_SECONDS - (now - oldest))

            if wait_for > 0:
                logger.debug("LLM RPM limit reached; sleeping %.2fs", wait_for)
                await asyncio.sleep(wait_for)

    def _evict_expired(self, now: float) -> None:
        while self._timestamps and now - self._timestamps[0] >= _WINDOW_SECONDS:
            self._timestamps.popleft()


_limiters: dict[tuple[str, int], AsyncWindowRateLimiter] = {}


def get_llm_rate_limiter(scope: str, requests_per_minute: int) -> AsyncWindowRateLimiter:
    """Return a shared limiter instance for the given scope."""
    key = (scope, max(_NO_LIMIT, int(requests_per_minute)))
    limiter = _limiters.get(key)
    if limiter is None:
        limiter = AsyncWindowRateLimiter(key[1])
        _limiters[key] = limiter
    return limiter
