from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from analytics.api import DailyStatsViewSet, EventViewSet
from apps.common.views import health
from apps.system.views import SystemHealthView, SystemReadyView
from certificate.api import CertificateViewSet
from doctor_online.api import VisitViewSet
from down.api import APKStatsViewSet
from perf.metrics import metrics_enabled
from sub.api import MeSubscriptionView
from telemedicine import views as telemedicine_views

router = DefaultRouter()
router.register(r"analytics/daily", DailyStatsViewSet, basename="analytics-daily")
router.register(r"analytics/events", EventViewSet, basename="analytics-events")
router.register(r"doctor/visits", VisitViewSet, basename="doctor-visits")
router.register(r"certificates", CertificateViewSet, basename="certificates")
router.register(r"down/apk-stats", APKStatsViewSet, basename="down-apk-stats")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", health, name="health"),
    path("api/v1/system/health", SystemHealthView.as_view(), name="system-health"),
    path("api/v1/system/ready", SystemReadyView.as_view(), name="system-ready"),
    path("api/v1/subscriptions/me", MeSubscriptionView.as_view(), name="subscriptions-me"),
    path("api/v1/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "telemedicine/pay/webhook",
        telemedicine_views.bitpay_webhook,
        name="telemedicine-bitpay-webhook",
    ),
    path(
        "telemedicine/pay/verify",
        telemedicine_views.bitpay_verify,
        name="telemedicine-bitpay-verify",
    ),
    path("chatbot/", include("chatbot.urls")),
]

if metrics_enabled():
    from perf.views import MetricsView
    urlpatterns.append(path("metrics", MetricsView.as_view(), name="metrics"))
