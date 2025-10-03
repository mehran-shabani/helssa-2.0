from django.http import HttpResponse
from django.views import View

from .metrics import build_metrics


class MetricsView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(
            build_metrics(),
            content_type="text/plain; version=0.0.4",
        )
