import time
import uuid

from django.utils.deprecation import MiddlewareMixin

from core.logging import request_id_ctx


class RequestIDMiddleware(MiddlewareMixin):
    def process_request(self, request):
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx.set(rid)
        request.request_id = rid
        request._t0 = time.perf_counter()

    def process_response(self, request, response):
        response["X-Request-ID"] = getattr(request, "request_id", "-")
        if hasattr(request, "_t0"):
            response["X-Response-Time-ms"] = int((time.perf_counter() - request._t0) * 1000)
        return response
