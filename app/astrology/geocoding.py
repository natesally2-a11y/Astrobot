"""Geocoding via OpenStreetMap Nominatim + timezone resolution."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Lazy singleton — TimezoneFinder loads a fairly large dataset on init.
_tf = None


def _get_tf():
    global _tf
    if _tf is None:
        from timezonefinder import TimezoneFinder

        _tf = TimezoneFinder()
    return _tf


@dataclass
class GeoResult:
    name: str
    latitude: float
    longitude: float
    timezone: Optional[str] = None


def timezone_at(latitude: float, longitude: float) -> Optional[str]:
    try:
        return _get_tf().timezone_at(lat=float(latitude), lng=float(longitude))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("timezonefinder failed: %s", exc)
        return None


async def geocode_city(query: str, limit: int = 5) -> List[GeoResult]:
    """Search for a place by name. Returns up to ``limit`` candidates."""
    params = {
        "q": query,
        "format": "jsonv2",
        "limit": str(limit),
        "addressdetails": "1",
        "accept-language": "ru",
    }
    headers = {"User-Agent": settings.nominatim_user_agent}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(_NOMINATIM_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("Nominatim request failed: %s", exc)
        return []

    results: List[GeoResult] = []
    for item in data:
        try:
            lat = float(item["lat"])
            lon = float(item["lon"])
        except (KeyError, ValueError):
            continue
        name = item.get("display_name", query)
        tz = await asyncio.to_thread(timezone_at, lat, lon)
        results.append(GeoResult(name=name, latitude=lat, longitude=lon, timezone=tz))
    return results
