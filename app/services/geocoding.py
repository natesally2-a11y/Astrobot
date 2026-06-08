"""Геокодинг городов через бесплатный Nominatim OSM API + определение таймзоны."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import httpx
from timezonefinder import TimezoneFinder

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "StellariumAI/1.0 (Telegram astrology bot)"

_tf = TimezoneFinder()


@dataclass
class GeoResult:
    display_name: str
    latitude: float
    longitude: float
    timezone: str | None


async def geocode_city(query: str, limit: int = 5) -> list[GeoResult]:
    """Найти города по строке запроса."""
    params = {
        "q": query,
        "format": "json",
        "limit": str(limit),
        "addressdetails": "1",
        "accept-language": "ru",
    }
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(NOMINATIM_URL, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    results: list[GeoResult] = []
    for item in data:
        try:
            lat = float(item["lat"])
            lon = float(item["lon"])
        except (KeyError, ValueError):
            continue
        tz = _tf.timezone_at(lat=lat, lng=lon)
        results.append(
            GeoResult(
                display_name=item.get("display_name", query),
                latitude=lat,
                longitude=lon,
                timezone=tz,
            )
        )
    return results


def timezone_for(latitude: float, longitude: float) -> str | None:
    return _tf.timezone_at(lat=latitude, lng=longitude)


def local_to_utc(
    birth_date: dt.date,
    birth_time: dt.time | None,
    timezone: str | None,
) -> dt.datetime:
    """Преобразовать локальные дату/время рождения в UTC.

    Если время не указано — используется полдень (12:00), что минимизирует
    погрешность по знаку Луны. Если таймзона не определена — считаем UTC.
    """
    time_part = birth_time or dt.time(12, 0)
    naive = dt.datetime.combine(birth_date, time_part)

    if timezone:
        try:
            tz = ZoneInfo(timezone)
            local = naive.replace(tzinfo=tz)
            return local.astimezone(dt.timezone.utc)
        except Exception:
            pass
    return naive.replace(tzinfo=dt.timezone.utc)
