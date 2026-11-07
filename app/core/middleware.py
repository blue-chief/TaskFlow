import logging 
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.request")

class RequestLogMiddleware(BaseHTTPMiddleware):
    """One log line per request, tagged with a request id you can search for
    later - 'a user says X broke around 3pm' becomes grep-able"""

    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("id=%s %s %s -> unhandled error", request_id, request.method, request.url.path)
            raise
        elapsed_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info("id=%s %s %s -> %s %.1fms", request_id, request.method, request.url.path, 
                    response.status_code, elapsed_ms)
        return response