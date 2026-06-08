from __future__ import annotations

import httpx
from timezonefinder import TimezoneFinder

from app.config import get_settings

settings = get_settings()
timezone_finder = TimezoneFinder()


async def search_places(query: str, limit: int = 5) -> list[dict]:
    if not query.strip():
        return []

    params = {"q": query, "format": "jsonv2", "limit": limit, "accept-language": "ru,en"}
    headers = {"User-Agent": settings.nominatim_user_agent}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(settings.nominatim_url, params=params, headers=headers)
        response.raise_for_status()
        payload = response.json()

    results = []
    for item in payload:
        lat = float(item.get("lat", 0.0))
        lon = float(item.get("lon", 0.0))
        timezone = timezone_finder.timezone_at(lat=lat, lng=lon)
        results.append(
            {
                "display_name": item.get("display_name", "Unknown place"),
                "lat": lat,
                "lon": lon,
                "timezone": timezone,
            }
        )
    return results
