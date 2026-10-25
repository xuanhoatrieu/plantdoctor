"""Small in-memory sliding-window rate limiter (no extra dependency).

TODO(security): counters live in this process only. The API currently runs as a single uvicorn worker,
so this is accurate; if it is scaled to several workers/instances, move the counters to a shared store
(e.g. Redis) or enforce the limits at the reverse proxy (Caddy).
"""
import math
import os
import threading
import time
from collections import deque
from typing import Optional

from cachetools import TTLCache
from fastapi import HTTPException, Request


def client_ip(request: Request) -> str:
    """Best-effort client address behind the reverse proxy.

    Behind Caddy the right-most X-Forwarded-For entry is the address Caddy itself saw, which the client
    cannot forge (left-most entries can be spoofed).
    TODO(security): if the backend port is ever reachable without the proxy, this header becomes
    client-controlled; keep the backend port closed at the firewall.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        last = forwarded.split(",")[-1].strip()
        if last:
            return last
    return request.client.host if request.client else "unknown"


def env_int(name: str, default: int, minimum: int = 1) -> int:
    try:
        return max(minimum, int(os.getenv(name, default)))
    except (TypeError, ValueError):
        return default


class SlidingWindowLimiter:
    """Allow at most `limit` hits per `window_seconds` for each key."""

    def __init__(self, limit: int, window_seconds: int, maxsize: int = 20000):
        self.limit = limit
        self.window = window_seconds
        # Idle keys disappear after one window; maxsize bounds memory under a flood of distinct keys.
        self._hits: TTLCache = TTLCache(maxsize=maxsize, ttl=window_seconds)
        self._lock = threading.Lock()

    def hit(self, key: str) -> Optional[int]:
        """Record a hit. Returns None if allowed, otherwise the number of seconds to wait."""
        now = time.monotonic()
        with self._lock:
            q = self._hits.get(key)
            if q is None:
                q = deque()
            while q and q[0] <= now - self.window:
                q.popleft()
            if len(q) >= self.limit:
                retry_after = max(1, math.ceil(q[0] + self.window - now))
                self._hits[key] = q
                return retry_after
            q.append(now)
            self._hits[key] = q
            return None

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()

    def enforce(self, key: str, message: str) -> None:
        retry_after = self.hit(key)
        if retry_after is not None:
            raise HTTPException(status_code=429, detail=message, headers={"Retry-After": str(retry_after)})
