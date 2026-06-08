from __future__ import annotations

from typing import Any

import httpx
from timezonefinder import TimezoneFinder

from app.config import settings

tf = TimezoneFinder()


async def search_places(query: str, limit: int = 5) -> list[dict[str, Any]]:
    if not query.strip():
        return []
    headers = {'User-Agent': settings.nominatim_user_agent}
    params = {
        'q': query,
        'format': 'jsonv2',
        'limit': limit,
        'addressdetails': 1,
        'accept-language': 'ru,en',
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get('https://nominatim.openstreetmap.org/search', params=params, headers=headers)
        response.raise_for_status()
        results = response.json()
    normalized = []
    for item in results:
        lat = float(item['lat'])
        lon = float(item['lon'])
        timezone_name = tf.timezone_at(lat=lat, lng=lon) or settings.default_timezone
        normalized.append(
            {
                'name': item.get('display_name', query),
                'latitude': lat,
                'longitude': lon,
                'timezone': timezone_name,
            }
        )
    return normalized
