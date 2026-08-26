import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.config import settings
from app.core.redis import redis_client
from app.core.logging import logger


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enterprise Rate-Limiting Middleware using Redis / In-Memory Counter.
    Protects public & internal APIs against scraping, DDoS, and brute force requests.
    """

    EXEMPT_PATHS = {"/docs", "/redoc", "/openapi.json", "/health", "/ready", "/live", "/metrics"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Bypass rate limiting for documentation and health checks
        if any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS):
            return await call_next(request)

        # Obtain client IP
        client_ip = request.client.host if request.client else "127.0.0.1"
        rate_key = f"rate_limit:{client_ip}:{int(time.time() // 60)}"

        current_requests = redis_client.incr(rate_key, ttl=60)

        if current_requests > settings.RATE_LIMIT_PER_MINUTE:
            logger.warning(f"RateLimitMiddleware: Client {client_ip} exceeded rate limit ({current_requests}/{settings.RATE_LIMIT_PER_MINUTE})")
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "TOO_MANY_REQUESTS",
                        "message": f"Rate limit exceeded. Maximum {settings.RATE_LIMIT_PER_MINUTE} requests per minute allowed.",
                        "retry_after_seconds": 60
                    }
                }
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(max(0, settings.RATE_LIMIT_PER_MINUTE - current_requests))
        return response
