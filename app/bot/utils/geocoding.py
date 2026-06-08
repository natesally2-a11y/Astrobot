from __future__ import annotations

from dataclasses import dataclass

import httpx
from timezonefinder import TimezoneFinder


@dataclass(frozen=True)
class GeocodedPlace:
    name: str
    latitude: float | None
    longitude: float | None
    timezone: str | None


timezone_finder = TimezoneFinder()


async def geocode_place(query: str) -> GeocodedPlace:
    place = query.strip()
    if not place:
        raise ValueError("empty place")

    try:
        async with httpx.AsyncClient(timeout=8.0, headers={"User-Agent": "StellariumAI/1.0"}) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": place, "format": "jsonv2", "limit": 1, "addressdetails": 1},
            )
            response.raise_for_status()
            data = response.json()
    except Exception:
        return GeocodedPlace(name=place, latitude=None, longitude=None, timezone=None)

    if not data:
        return GeocodedPlace(name=place, latitude=None, longitude=None, timezone=None)

    item = data[0]
    latitude = float(item["lat"])
    longitude = float(item["lon"])
    timezone_name = timezone_finder.timezone_at(lat=latitude, lng=longitude)
    return GeocodedPlace(
        name=item.get("display_name") or place,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone_name,
    )
