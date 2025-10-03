from __future__ import annotations

import importlib
import os
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import connection
from django.urls import clear_url_caches

import config.urls
from analytics.models import Event, StatsDaily


@pytest.fixture
def reload_urls():
    def _reload(enable: bool) -> None:
        if enable:
            os.environ["ENABLE_METRICS"] = "true"
        else:
            os.environ.pop("ENABLE_METRICS", None)
        clear_url_caches()
        importlib.reload(config.urls)

    yield _reload

    os.environ.pop("ENABLE_METRICS", None)
    clear_url_caches()
    importlib.reload(config.urls)


@pytest.mark.django_db
def test_event_and_stats_indexes_present():
    with connection.cursor() as cursor:
        event_constraints = connection.introspection.get_constraints(cursor, Event._meta.db_table)
        stats_constraints = connection.introspection.get_constraints(
            cursor, StatsDaily._meta.db_table
        )
    assert "analytics_event_at_idx" in event_constraints
    assert "analytics_statsdaily_day_idx" in stats_constraints


@pytest.mark.django_db
def test_perf_slowlog_graceful_on_sqlite():
    out = StringIO()
    call_command("perf_slowlog", stdout=out)
    text = out.getvalue()
    assert "requires PostgreSQL" in text


@pytest.mark.django_db
def test_metrics_endpoint_disabled(client, reload_urls):
    reload_urls(False)
    response = client.get("/metrics")
    assert response.status_code == 404


@pytest.mark.django_db
def test_metrics_endpoint_enabled(client, reload_urls):
    reload_urls(True)
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.content.decode()
    assert "helssa_app_info" in body
    assert "helssa_events_total" in body
    assert "helssa_statsdays_total" in body
    assert "helssa_ready_last_ok_timestamp" in body
