"""Rate limiting middleware."""

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config.settings import get_settings

settings = get_settings()


def get_limiter() -> Limiter:
    """Create rate limiter instance."""
    return Limiter(key_func=get_remote_address)


limiter = get_limiter()


class RateLimitMiddleware:
    """Rate limiting middleware with configurable limits."""

    def __init__(self, app):
        self.app = app
        self._request_counts = defaultdict(lambda: {"count": 0, "reset": 0})

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope=scope, receive=receive)
        client_ip = request.client.host if request.client else "unknown"

        path = scope.get("path", "")
        if not path.startswith("/api/"):
            await self.app(scope, receive, send)
            return

        key = f"{client_ip}:{path}"
        now = time.time()
        window = 60

        if self._request_counts[key]["reset"] < now:
            self._request_counts[key] = {"count": 0, "reset": now + window}

        self._request_counts[key]["count"] += 1

        if settings.environment == "production":
            limits = {
                "/api/subscription": 10,
                "/api/payment": 10,
                "/api/trading": 30,
                "/api/airdrop": 20,
                "/api/dashboard": 60,
            }

            limit = limits.get(path, 30)
            if self._request_counts[key]["count"] > limit:
                response = JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded", "retry_after": window},
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
