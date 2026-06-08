from __future__ import annotations

from dataclasses import dataclass

import httpx
from timezonefinder import TimezoneFinder


_timezone_finder = TimezoneFinder()


@dataclass(slots=True)
class GeocodingResult:
    display_name: str
    latitude: float
    longitude: float
    timezone: str
    raw: dict


class GeocodingService:
    base_url = "https://nominatim.openstreetmap.org/search"

    async def search_city(self, query: str, limit: int = 5) -> list[GeocodingResult]:
        params = {
            "q": query,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": limit,
        }
        headers = {"User-Agent": "stellarium-ai-bot/1.0"}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()

        results: list[GeocodingResult] = []
        for item in payload:
            latitude = float(item["lat"])
            longitude = float(item["lon"])
            timezone = _timezone_finder.timezone_at(lat=latitude, lng=longitude) or "UTC"
            results.append(
                GeocodingResult(
                    display_name=item["display_name"],
                    latitude=latitude,
                    longitude=longitude,
                    timezone=timezone,
                    raw=item,
                )
            )
        return results
