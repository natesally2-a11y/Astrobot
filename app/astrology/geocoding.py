"""Free-text city geocoding via OpenStreetMap Nominatim."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import httpx
from timezonefinder import TimezoneFinder

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "StellariumAI/0.1 (contact: support@stellarium.ai)"

_tz_finder = TimezoneFinder()


@dataclass
class GeoResult:
    display_name: str
    latitude: float
    longitude: float
    timezone: str


async def geocode_city(query: str) -> Optional[GeoResult]:
    if not query or len(query.strip()) < 2:
        return None
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                NOMINATIM_URL,
                params={
                    "q": query.strip(),
                    "format": "json",
                    "addressdetails": 0,
                    "limit": 1,
                    "accept-language": "ru,en",
                },
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            data = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Geocoding request failed: %s", exc)
        return None

    if not data:
        return None

    entry = data[0]
    try:
        lat = float(entry["lat"])
        lon = float(entry["lon"])
    except (KeyError, ValueError):
        return None

    tz = _tz_finder.timezone_at(lat=lat, lng=lon) or "UTC"
    return GeoResult(
        display_name=entry.get("display_name", query),
        latitude=lat,
        longitude=lon,
        timezone=tz,
    )
