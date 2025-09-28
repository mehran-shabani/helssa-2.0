import datetime as dt

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from analytics.models import Event, StatsDaily

pytestmark = pytest.mark.django_db


def test_event_str():
    user = get_user_model().objects.create_user("user@example.com", "pass1234")
    event = Event.objects.create(name="app_open", user=user, props={"key": "value"})
    rep = str(event)
    assert "app_open" in rep
    assert str(event.at.year) in rep


def test_stats_daily_unique_day():
    StatsDaily.objects.create(day=dt.date.today())
    with pytest.raises(IntegrityError):
        StatsDaily.objects.create(day=dt.date.today())
