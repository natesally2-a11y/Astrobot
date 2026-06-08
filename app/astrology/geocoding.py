"""City lookup via OpenStreetMap Nominatim (free, no API key)."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Optional

import httpx
from loguru import logger


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "StellariumAI/0.1 (+https://t.me/stellarium_ai_bot)"


@dataclass
class GeoResult:
    display_name: str
    latitude: float
    longitude: float
    country: Optional[str] = None


async def geocode(query: str, *, limit: int = 5) -> List[GeoResult]:
    if not query or len(query) < 2:
        return []
    params = {
        "q": query,
        "format": "json",
        "limit": str(limit),
        "addressdetails": "1",
        "accept-language": "ru",
    }
    headers = {"User-Agent": USER_AGENT}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(NOMINATIM_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("Geocoding failed for '{}': {}", query, exc)
        return []

    out: List[GeoResult] = []
    for item in data:
        try:
            lat = float(item["lat"])
            lon = float(item["lon"])
        except (KeyError, ValueError):
            continue
        out.append(
            GeoResult(
                display_name=item.get("display_name", query),
                latitude=lat,
                longitude=lon,
                country=(item.get("address") or {}).get("country"),
            )
        )
    return out


def geocode_sync(query: str) -> List[GeoResult]:
    return asyncio.run(geocode(query))
