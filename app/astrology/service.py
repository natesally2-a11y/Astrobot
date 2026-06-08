"""High-level helpers bridging stored birth data and the calculation engine."""
from __future__ import annotations

import datetime as dt
from typing import Optional
from zoneinfo import ZoneInfo

from app.astrology.calculations import NatalChart, calculate_natal_chart
from app.astrology.geocoding import timezone_at


def _to_utc(
    birth_date: dt.date,
    birth_time: Optional[dt.time],
    timezone: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float],
) -> tuple[dt.datetime, bool]:
    """Combine local birth date/time into a UTC datetime.

    Returns (utc_datetime, time_was_known). When the time is unknown we default
    to 12:00 local (a common astrological convention for "noon charts").
    """
    time_known = birth_time is not None
    local_time = birth_time or dt.time(12, 0)
    naive = dt.datetime.combine(birth_date, local_time)

    tzname = timezone
    if not tzname and latitude is not None and longitude is not None:
        tzname = timezone_at(float(latitude), float(longitude))

    try:
        tz = ZoneInfo(tzname) if tzname else dt.timezone.utc
    except Exception:
        tz = dt.timezone.utc

    local_dt = naive.replace(tzinfo=tz)
    return local_dt.astimezone(dt.timezone.utc), time_known


def build_chart(
    birth_date: dt.date,
    birth_time: Optional[dt.time],
    latitude: Optional[float],
    longitude: Optional[float],
    timezone: Optional[str] = None,
) -> NatalChart:
    """Build a :class:`NatalChart` from birth parameters."""
    utc_dt, time_known = _to_utc(birth_date, birth_time, timezone, latitude, longitude)
    lat = float(latitude) if latitude is not None else None
    lon = float(longitude) if longitude is not None else None
    return calculate_natal_chart(utc_dt, lat, lon, with_houses=time_known)


def build_chart_from_model(birth_data) -> NatalChart:
    """Build a chart from a :class:`app.database.models.BirthData` instance."""
    return build_chart(
        birth_date=birth_data.birth_date,
        birth_time=birth_data.birth_time,
        latitude=birth_data.latitude,
        longitude=birth_data.longitude,
        timezone=birth_data.timezone,
    )
