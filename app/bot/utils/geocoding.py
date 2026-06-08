"""Geocoding via Nominatim (OpenStreetMap) API."""

import aiohttp
from timezonefinder import TimezoneFinder

from app.config import settings

_tf = TimezoneFinder()


async def geocode_city(city_name: str) -> dict | None:
    """Geocode a city name, returns dict with lat, lon, display_name, timezone."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city_name,
        "format": "json",
        "limit": 1,
        "accept-language": "ru",
    }
    headers = {"User-Agent": settings.nominatim_user_agent}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if not data:
                    return None

                result = data[0]
                lat = float(result["lat"])
                lon = float(result["lon"])
                tz = _tf.timezone_at(lat=lat, lng=lon) or "UTC"

                return {
                    "latitude": lat,
                    "longitude": lon,
                    "display_name": result.get("display_name", city_name),
                    "timezone": tz,
                }
    except Exception:
        return None


async def search_cities(query: str, limit: int = 5) -> list[dict]:
    """Search for cities matching a query."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "accept-language": "ru",
        "featuretype": "city",
    }
    headers = {"User-Agent": settings.nominatim_user_agent}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                results = []
                for item in data:
                    lat = float(item["lat"])
                    lon = float(item["lon"])
                    tz = _tf.timezone_at(lat=lat, lng=lon) or "UTC"
                    results.append({
                        "latitude": lat,
                        "longitude": lon,
                        "display_name": item.get("display_name", ""),
                        "timezone": tz,
                    })
                return results
    except Exception:
        return []
