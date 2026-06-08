"""Сборка натальной карты из сохранённых данных рождения."""
from __future__ import annotations

import datetime as dt

from app.astrology.calculations import NatalChart, compute_chart
from app.database.models import BirthData
from app.services.geocoding import local_to_utc


def chart_from_birth_data(bd: BirthData) -> NatalChart:
    lat = float(bd.latitude) if bd.latitude is not None else 0.0
    lon = float(bd.longitude) if bd.longitude is not None else 0.0
    has_time = bd.birth_time is not None and bd.time_is_exact
    utc = local_to_utc(bd.birth_date, bd.birth_time, bd.timezone)
    return compute_chart(utc, lat, lon, has_time=has_time)


def chart_from_raw(
    birth_date: dt.date,
    birth_time: dt.time | None,
    latitude: float,
    longitude: float,
    timezone: str | None,
) -> NatalChart:
    has_time = birth_time is not None
    utc = local_to_utc(birth_date, birth_time, timezone)
    return compute_chart(utc, latitude, longitude, has_time=has_time)
