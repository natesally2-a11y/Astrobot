import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


async def search_cities(query: str, limit: int = 5) -> list[dict]:
    if len(query) < 2:
        return []
    async with httpx.AsyncClient() as client:
        response = await client.get(
            NOMINATIM_URL,
            params={
                "q": query,
                "format": "json",
                "limit": limit,
                "addressdetails": 1,
                "accept-language": "ru",
            },
            headers={"User-Agent": "StellariumAI/1.0"},
            timeout=10.0,
        )
        response.raise_for_status()
        results = response.json()

    cities = []
    for item in results:
        cities.append({
            "name": item.get("display_name", ""),
            "short_name": _short_name(item),
            "latitude": float(item["lat"]),
            "longitude": float(item["lon"]),
        })
    return cities


def _short_name(item: dict) -> str:
    address = item.get("address", {})
    parts = []
    for key in ("city", "town", "village", "municipality"):
        if key in address:
            parts.append(address[key])
            break
    if "state" in address:
        parts.append(address["state"])
    if "country" in address:
        parts.append(address["country"])
    if parts:
        return ", ".join(parts)
    return item.get("display_name", "")[:80]


async def geocode_place(place: str) -> dict | None:
    results = await search_cities(place, limit=1)
    return results[0] if results else None


def estimate_timezone(longitude: float) -> str:
    offset = round(longitude / 15)
    if offset >= 0:
        return f"UTC+{offset}"
    return f"UTC{offset}"


def timezone_to_offset(tz_name: str) -> float:
    if tz_name.startswith("UTC"):
        rest = tz_name[3:]
        if rest.startswith("+"):
            return float(rest[1:])
        if rest.startswith("-"):
            return float(rest)
        return 0.0
    return 3.0
