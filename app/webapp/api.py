"""REST API для Mini App."""
from __future__ import annotations

import datetime as dt
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import interpret_compatibility, interpret_transits
from app.astrology.calculations import NatalChart, compute_transits
from app.astrology.chart_renderer import render_chart_svg
from app.astrology.constants import sign_name
from app.config import settings
from app.database import crud
from app.database.session import get_session
from app.plans import get_plan, is_premium
from app.services.chart_service import chart_from_birth_data, chart_from_raw
from app.services.geocoding import geocode_city
from app.webapp.auth import InitDataError, get_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["miniapp"])


class InitDataBody(BaseModel):
    init_data: str
    dev_user_id: int | None = None


class CompatibilityBody(InitDataBody):
    partner_name: str = "Партнёр"
    birth_date: str  # ISO YYYY-MM-DD
    birth_time: str | None = None  # HH:MM
    city: str


def _resolve_user_id(body: InitDataBody) -> int:
    # Прод: строгая проверка подписи initData.
    if settings.bot_token:
        try:
            return get_user_id(body.init_data)
        except InitDataError as exc:
            raise HTTPException(status_code=401, detail=f"Auth failed: {exc}")
    # Дев-режим без токена: доверяем dev_user_id (только для локальной отладки).
    if body.dev_user_id is not None:
        return body.dev_user_id
    raise HTTPException(status_code=401, detail="No auth available")


def _chart_to_dict(chart: NatalChart) -> dict:
    return {
        "has_time": chart.has_time,
        "ascendant": (
            {"sign": sign_name(chart.ascendant), "degree": chart.ascendant % 30}
            if chart.ascendant is not None
            else None
        ),
        "midheaven": (
            {"sign": sign_name(chart.midheaven)}
            if chart.midheaven is not None
            else None
        ),
        "planets": [
            {
                "key": p.key,
                "name": p.name,
                "symbol": p.symbol,
                "sign": p.sign,
                "degree": round(p.degree, 2),
                "retrograde": p.retrograde,
                "house": p.house,
                "element": p.element,
            }
            for p in chart.planets
        ],
        "aspects": [
            {
                "body1": (chart.planet(a.body1).name if chart.planet(a.body1) else a.body1),
                "body2": (chart.planet(a.body2).name if chart.planet(a.body2) else a.body2),
                "name": a.name,
                "symbol": a.symbol,
                "orb": a.orb,
            }
            for a in chart.aspects
        ],
        "svg": render_chart_svg(chart),
    }


@router.post("/me")
async def api_me(
    body: InitDataBody, session: AsyncSession = Depends(get_session)
) -> dict:
    user_id = _resolve_user_id(body)
    user = await crud.get_user(session, user_id)
    if not user:
        return {"registered": False}

    plan = get_plan(user.subscription_type)
    result: dict = {
        "registered": True,
        "first_name": user.first_name,
        "subscription": {
            "type": user.subscription_type,
            "title": plan.title,
            "active": crud.is_subscription_active(user),
            "is_premium": is_premium(user.subscription_type),
            "expires_at": user.subscription_expires_at.isoformat()
            if user.subscription_expires_at
            else None,
        },
        "referral_count": user.referral_count,
        "chart": None,
    }

    bd = await crud.get_birth_data(session, user_id)
    if bd:
        chart = chart_from_birth_data(bd)
        result["birth"] = {
            "date": bd.birth_date.isoformat(),
            "time": bd.birth_time.isoformat() if bd.birth_time else None,
            "place": bd.birth_place,
        }
        result["chart"] = _chart_to_dict(chart)
    return result


@router.post("/transits")
async def api_transits(
    body: InitDataBody, session: AsyncSession = Depends(get_session)
) -> dict:
    user_id = _resolve_user_id(body)
    user = await crud.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not (is_premium(user.subscription_type) and crud.is_subscription_active(user)):
        raise HTTPException(status_code=403, detail="Premium required")

    bd = await crud.get_birth_data(session, user_id)
    if not bd:
        raise HTTPException(status_code=400, detail="No birth data")

    chart = chart_from_birth_data(bd)
    transits = compute_transits(chart)
    text = await interpret_transits(chart)
    return {
        "transits": [
            {"body1": a.body1, "body2": a.body2, "name": a.name, "orb": a.orb}
            for a in transits
        ],
        "interpretation": text,
    }


@router.post("/compatibility")
async def api_compatibility(
    body: CompatibilityBody, session: AsyncSession = Depends(get_session)
) -> dict:
    user_id = _resolve_user_id(body)
    bd = await crud.get_birth_data(session, user_id)
    if not bd:
        raise HTTPException(status_code=400, detail="No birth data")

    try:
        partner_date = dt.date.fromisoformat(body.birth_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Bad date")
    partner_time = None
    if body.birth_time:
        try:
            partner_time = dt.time.fromisoformat(body.birth_time)
        except ValueError:
            partner_time = None

    cities = await geocode_city(body.city, limit=1)
    if not cities:
        raise HTTPException(status_code=404, detail="City not found")
    city = cities[0]

    user_chart = chart_from_birth_data(bd)
    partner_chart = chart_from_raw(
        partner_date, partner_time, city.latitude, city.longitude, city.timezone
    )
    user = await crud.get_user(session, user_id)
    user_name = (user.first_name if user else None) or "Вы"
    text = await interpret_compatibility(
        user_chart, partner_chart, user_name, body.partner_name
    )
    await crud.save_reading(session, user_id, "compatibility", text)
    return {
        "interpretation": text,
        "partner_chart": _chart_to_dict(partner_chart),
    }
