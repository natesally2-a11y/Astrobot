"""REST API endpoints consumed by the Telegram Mini App."""
from __future__ import annotations

import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.calculations import NatalChart, calculate_transits
from app.astrology.chart_renderer import render_natal_chart_svg
from app.astrology.constants import (
    PLANET_NAMES_RU,
    SIGN_NAMES_RU,
    degree_to_sign,
)
from app.astrology.service import build_chart, build_chart_from_model
from app.bot.plans import PLANS
from app.bot.utils import has_premium
from app.config import settings
from app.database import crud
from app.database.base import get_session
from app.database.models import PLAN_FREE
from app.webapp.auth import validate_init_data

router = APIRouter(tags=["miniapp"])


async def authed_user_id(
    x_telegram_init_data: Optional[str] = Header(default=None, alias="X-Telegram-Init-Data"),
) -> int:
    payload = validate_init_data(x_telegram_init_data or "")
    if not payload or not isinstance(payload.get("user"), dict):
        raise HTTPException(status_code=401, detail="Invalid Telegram initData")
    return int(payload["user"]["id"])


def serialize_chart(chart: NatalChart) -> dict:
    return {
        "planets": [
            {
                "key": p.key,
                "name": p.name,
                "longitude": round(p.longitude, 4),
                "sign": SIGN_NAMES_RU[p.sign_index],
                "sign_index": p.sign_index,
                "degree": round(p.degree_in_sign, 2),
                "position": p.position_str,
                "house": p.house,
                "retrograde": p.retrograde,
            }
            for p in chart.planets
        ],
        "aspects": [
            {
                "body1": PLANET_NAMES_RU.get(a.body1, a.body1),
                "body2": PLANET_NAMES_RU.get(a.body2, a.body2),
                "type": a.name,
                "key": a.key,
                "orb": a.orb,
            }
            for a in chart.aspects
        ],
        "ascendant": None
        if chart.ascendant is None
        else {
            "longitude": round(chart.ascendant, 4),
            "sign": SIGN_NAMES_RU[degree_to_sign(chart.ascendant)[0]],
        },
        "midheaven": None if chart.midheaven is None else round(chart.midheaven, 4),
        "has_houses": chart.has_houses,
        "svg": render_natal_chart_svg(chart),
    }


@router.get("/me")
async def get_me(
    user_id: int = Depends(authed_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await crud.get_user(session, user_id)
    if not user:
        return {"registered": False}
    await crud.downgrade_if_expired(session, user)
    bd = await crud.get_birth_data(session, user_id)
    plan = PLANS.get(user.subscription_type)
    return {
        "registered": True,
        "first_name": user.first_name,
        "subscription_type": user.subscription_type,
        "subscription_title": plan.title if plan else "Бесплатный",
        "is_premium": has_premium(user),
        "subscription_expires_at": user.subscription_expires_at.isoformat()
        if user.subscription_expires_at
        else None,
        "has_chart": bd is not None,
        "remaining_questions": await crud.remaining_questions(user, settings.free_daily_questions)
        if user.subscription_type == PLAN_FREE
        else -1,
        "referral_count": user.referral_count,
    }


@router.get("/chart")
async def get_chart(
    user_id: int = Depends(authed_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    bd = await crud.get_birth_data(session, user_id)
    if not bd:
        raise HTTPException(status_code=404, detail="No birth data. Create a chart in the bot first.")
    chart = build_chart_from_model(bd)
    data = serialize_chart(chart)
    data["birth"] = {
        "date": bd.birth_date.isoformat(),
        "time": bd.birth_time.isoformat() if bd.birth_time else None,
        "place": bd.birth_place,
        "time_known": bd.time_known,
    }
    return data


@router.get("/transits")
async def get_transits(
    user_id: int = Depends(authed_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await crud.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    bd = await crud.get_birth_data(session, user_id)
    if not bd:
        raise HTTPException(status_code=404, detail="No birth data")
    chart = build_chart_from_model(bd)
    transits = calculate_transits(chart)
    return {
        "is_premium": has_premium(user),
        "transits": [
            {
                "transiting": PLANET_NAMES_RU.get(a.body1, a.body1),
                "natal": PLANET_NAMES_RU.get(a.body2, a.body2),
                "type": a.name,
                "orb": a.orb,
            }
            for a in transits[:20]
        ],
    }


class PartnerData(BaseModel):
    date: str            # YYYY-MM-DD
    time: Optional[str] = None  # HH:MM
    place: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None


@router.post("/compatibility")
async def post_compatibility(
    partner: PartnerData,
    user_id: int = Depends(authed_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    bd = await crud.get_birth_data(session, user_id)
    if not bd:
        raise HTTPException(status_code=404, detail="No birth data")

    try:
        p_date = dt.date.fromisoformat(partner.date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format (YYYY-MM-DD)")
    p_time = None
    if partner.time:
        try:
            hh, mm = partner.time.split(":")
            p_time = dt.time(int(hh), int(mm))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid time format (HH:MM)")

    if partner.latitude is None or partner.longitude is None:
        if not partner.place:
            raise HTTPException(status_code=422, detail="Provide coordinates or a place name")
        from app.astrology.geocoding import geocode_city

        results = await geocode_city(partner.place, limit=1)
        if not results:
            raise HTTPException(status_code=404, detail="Place not found")
        lat, lon, tz = results[0].latitude, results[0].longitude, results[0].timezone
    else:
        lat, lon, tz = partner.latitude, partner.longitude, partner.timezone

    chart_user = build_chart_from_model(bd)
    chart_partner = build_chart(p_date, p_time, lat, lon, tz)

    # Lightweight element-based score (the bot provides the full AI synastry).
    from app.astrology.constants import SIGNS

    score = _compat_score(chart_user, chart_partner, SIGNS)
    return {
        "score": score,
        "user_chart": serialize_chart(chart_user),
        "partner_chart": serialize_chart(chart_partner),
        "hint": "Полный ИИ-анализ совместимости доступен в чат-боте (/compatibility).",
    }


def _compat_score(chart_a: NatalChart, chart_b: NatalChart, signs) -> int:
    """Rough 0-100 compatibility score from Sun/Moon/Venus element harmony."""
    compatible = {
        "Огонь": {"Огонь", "Воздух"},
        "Воздух": {"Воздух", "Огонь"},
        "Земля": {"Земля", "Вода"},
        "Вода": {"Вода", "Земля"},
    }
    total, count = 0, 0
    for key in ("sun", "moon", "venus"):
        pa, pb = chart_a.planet(key), chart_b.planet(key)
        if not pa or not pb:
            continue
        ea, eb = signs[pa.sign_index][3], signs[pb.sign_index][3]
        count += 1
        if ea == eb:
            total += 100
        elif eb in compatible.get(ea, set()):
            total += 75
        else:
            total += 45
    return round(total / count) if count else 50
