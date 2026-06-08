"""REST API for the Mini App."""
from __future__ import annotations

from datetime import date, time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query, Response
from pydantic import BaseModel

from app.astrology.calculations import compute_chart, NatalChart
from app.astrology.chart_renderer import render_svg
from app.database import session_factory
from app.database.crud import get_birth_data, get_user, has_active_subscription
from app.webapp.api.auth import verify_init_data

router = APIRouter(prefix="/api", tags=["miniapp"])


async def _resolve_user_id(init_data: Optional[str]) -> int:
    user_id = verify_init_data(init_data or "")
    if user_id is None:
        raise HTTPException(status_code=401, detail="invalid_init_data")
    return user_id


class PlanetOut(BaseModel):
    name: str
    name_ru: str
    glyph: str
    longitude: float
    sign: str
    sign_glyph: str
    sign_degree: float
    house: Optional[int] = None
    retrograde: bool


class AspectOut(BaseModel):
    planet_a: str
    planet_b: str
    name: str
    name_ru: str
    angle: float
    orb: float


class ChartOut(BaseModel):
    sun: str
    moon: str
    ascendant: Optional[str]
    planets: list[PlanetOut]
    aspects: list[AspectOut]
    houses: list[float]
    has_time: bool
    timezone: Optional[str]


def _serialize(chart: NatalChart) -> ChartOut:
    planets = [
        PlanetOut(
            name=p.name,
            name_ru=p.name_ru,
            glyph=p.glyph,
            longitude=round(p.longitude, 3),
            sign=p.sign_ru,
            sign_glyph=p.sign_glyph,
            sign_degree=round(p.sign_degree, 3),
            house=p.house,
            retrograde=p.retrograde,
        )
        for p in chart.planets.values()
    ]
    aspects = [
        AspectOut(
            planet_a=a.planet_a,
            planet_b=a.planet_b,
            name=a.name,
            name_ru=a.name_ru,
            angle=a.angle,
            orb=round(a.orb, 2),
        )
        for a in chart.aspects
    ]
    return ChartOut(
        sun=chart.sun_sign_ru(),
        moon=chart.moon_sign_ru(),
        ascendant=chart.ascendant_sign_ru(),
        planets=planets,
        aspects=aspects,
        houses=[round(h, 3) for h in chart.houses],
        has_time=not chart.time_is_unknown,
        timezone=chart.timezone,
    )


@router.get("/me")
async def get_me(x_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")):
    user_id = await _resolve_user_id(x_init_data)
    async with session_factory() as session:
        user = await get_user(session, user_id)
        bd = await get_birth_data(session, user_id)
        if user is None:
            raise HTTPException(404, "user_not_found")
        return {
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "subscription_type": user.subscription_type,
            "is_premium": has_active_subscription(user),
            "subscription_expires_at": (
                user.subscription_expires_at.isoformat()
                if user.subscription_expires_at
                else None
            ),
            "has_birth_data": bd is not None,
            "birth_place": bd.birth_place if bd else None,
        }


@router.get("/chart", response_model=ChartOut)
async def get_chart(
    x_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
):
    user_id = await _resolve_user_id(x_init_data)
    async with session_factory() as session:
        bd = await get_birth_data(session, user_id)
        if bd is None:
            raise HTTPException(404, "birth_data_required")
        chart = compute_chart(
            birth_date=bd.birth_date,
            birth_time=None if bd.time_is_unknown else bd.birth_time,
            latitude=float(bd.latitude),
            longitude=float(bd.longitude),
            timezone_name=bd.timezone,
        )
        return _serialize(chart)


@router.get("/chart.svg")
async def get_chart_svg(
    x_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
):
    user_id = await _resolve_user_id(x_init_data)
    async with session_factory() as session:
        bd = await get_birth_data(session, user_id)
        if bd is None:
            raise HTTPException(404, "birth_data_required")
        chart = compute_chart(
            birth_date=bd.birth_date,
            birth_time=None if bd.time_is_unknown else bd.birth_time,
            latitude=float(bd.latitude),
            longitude=float(bd.longitude),
            timezone_name=bd.timezone,
        )
        svg = render_svg(chart)
        return Response(content=svg, media_type="image/svg+xml")


@router.get("/preview/chart.svg")
async def preview_chart(
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(12, ge=0, le=23),
    minute: int = Query(0, ge=0, le=59),
    lat: float = Query(55.7558),
    lon: float = Query(37.6173),
):
    """Public preview endpoint — useful for demo & marketing pages."""
    chart = compute_chart(
        birth_date=date(year, month, day),
        birth_time=time(hour, minute),
        latitude=lat,
        longitude=lon,
    )
    svg = render_svg(chart)
    return Response(content=svg, media_type="image/svg+xml")
