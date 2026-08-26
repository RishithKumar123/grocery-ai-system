import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger


class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        method = request.method
        
        logger.info(f"Incoming Request: {method} {path}")
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            logger.info(
                f"Completed Request: {method} {path} - Status: {response.status_code} - Duration: {duration:.4f}s"
            )
            response.headers["X-Process-Time"] = str(duration)
            return response
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Failed Request: {method} {path} - Error: {str(e)} - Duration: {duration:.4f}s"
            )
            raise e
        
