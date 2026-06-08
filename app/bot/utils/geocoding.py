from __future__ import annotations

from typing import Any

import httpx


async def search_city(query: str, limit: int = 5) -> list[dict[str, Any]]:
    if not query.strip():
        return []
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "addressdetails": 1, "limit": limit},
            headers={"User-Agent": "stellarium-ai-bot/0.1"},
        )
        response.raise_for_status()
        data = response.json()
        results: list[dict[str, Any]] = []
        for row in data:
            results.append(
                {
                    "display_name": row.get("display_name", query),
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                    "timezone": "UTC",
                }
            )
        return results

