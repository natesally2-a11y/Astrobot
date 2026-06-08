from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import compatibility_interpretation, daily_interpretation
from app.astrology.calculations import calculate_daily_transits, calculate_natal_chart, compatibility_score
from app.astrology.chart_renderer import render_natal_chart_svg
from app.astrology.geocoding import search_places
from app.database import crud
from app.database.database import get_session

router = APIRouter(prefix="/api", tags=["webapp"])


class CompatibilityRequest(BaseModel):
    user_id: int = Field(..., description="Telegram ID of current user")
    partner_birth_date: str
    partner_birth_time: str
    partner_place: str


@router.get("/profile/{user_id}")
async def get_profile(user_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    user, birth = await crud.get_user_full_profile(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
        "username": user.username,
        "subscription_type": user.subscription_type,
        "subscription_expires_at": user.subscription_expires_at.isoformat()
        if user.subscription_expires_at
        else None,
        "gdpr_consent": user.gdpr_consent,
        "birth_data": {
            "birth_date": birth.birth_date.isoformat() if birth else None,
            "birth_time": birth.birth_time.isoformat() if birth and birth.birth_time else None,
            "birth_place": birth.birth_place if birth else None,
            "latitude": birth.latitude if birth else None,
            "longitude": birth.longitude if birth else None,
        },
    }


@router.get("/chart/{user_id}")
async def get_chart(user_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    _, birth = await crud.get_user_full_profile(session, user_id)
    if not birth:
        raise HTTPException(status_code=404, detail="Birth data not found")

    chart = calculate_natal_chart(
        birth_date=birth.birth_date,
        birth_time=birth.birth_time,
        latitude=birth.latitude,
        longitude=birth.longitude,
        place=birth.birth_place,
    )
    svg = render_natal_chart_svg(chart)
    return {"chart": chart.to_dict(), "svg": svg}


@router.get("/transits/{user_id}")
async def get_transits(user_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    _, birth = await crud.get_user_full_profile(session, user_id)
    if not birth:
        raise HTTPException(status_code=404, detail="Birth data not found")

    chart = calculate_natal_chart(
        birth_date=birth.birth_date,
        birth_time=birth.birth_time,
        latitude=birth.latitude,
        longitude=birth.longitude,
        place=birth.birth_place,
    )
    transits = calculate_daily_transits(chart, date.today(), birth.latitude, birth.longitude)
    analysis = await daily_interpretation(chart, transits, date.today())
    return {"transits": [t.__dict__ for t in transits], "analysis": analysis}


@router.post("/compatibility")
async def post_compatibility(
    payload: CompatibilityRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    _, birth = await crud.get_user_full_profile(session, payload.user_id)
    if not birth:
        raise HTTPException(status_code=404, detail="Birth data not found")

    user_chart = calculate_natal_chart(
        birth_date=birth.birth_date,
        birth_time=birth.birth_time,
        latitude=birth.latitude,
        longitude=birth.longitude,
        place=birth.birth_place,
    )
    try:
        partner_date = datetime.strptime(payload.partner_birth_date, "%Y-%m-%d").date()
        partner_time = datetime.strptime(payload.partner_birth_time, "%H:%M").time()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Use YYYY-MM-DD and HH:MM format") from exc

    places = await search_places(payload.partner_place, limit=1)
    if not places:
        raise HTTPException(status_code=404, detail="Partner place not found")
    place = places[0]
    partner_chart = calculate_natal_chart(
        birth_date=partner_date,
        birth_time=partner_time,
        latitude=place["lat"],
        longitude=place["lon"],
        place=place["display_name"],
    )
    score, highlights = compatibility_score(user_chart, partner_chart)
    report = await compatibility_interpretation(user_chart, partner_chart, score, highlights)
    return {"score": score, "highlights": highlights, "report": report}
