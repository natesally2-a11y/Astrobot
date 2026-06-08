from timezonefinder import TimezoneFinder

from app.config import get_settings


async def search_cities(query: str, limit: int = 5) -> list[dict[str, str | float | None]]:
    import httpx

    settings = get_settings()
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "jsonv2",
                "addressdetails": 1,
                "limit": limit,
            },
            headers={"User-Agent": settings.nominatim_user_agent},
        )
        response.raise_for_status()
        items = response.json()

    timezone_finder = TimezoneFinder()
    cities: list[dict[str, str | float | None]] = []
    for item in items:
        latitude = float(item["lat"])
        longitude = float(item["lon"])
        address = item.get("address", {})
        label = item.get("display_name") or query
        short_label = ", ".join(
            part
            for part in [
                address.get("city") or address.get("town") or address.get("village") or address.get("municipality"),
                address.get("state"),
                address.get("country"),
            ]
            if part
        )
        cities.append(
            {
                "label": short_label or label,
                "place": label,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone_finder.timezone_at(lat=latitude, lng=longitude),
            }
        )
    return cities
