from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import AIInterpreter
from app.astrology.calculations import build_natal_chart, calculate_transits, planet_table
from app.astrology.chart_renderer import render_chart_svg
from app.astrology.schemas import BirthProfile
from app.bot.utils.geocoding import geocode_place
from app.bot.utils.parsing import parse_birth_date, parse_birth_time
from app.bot.utils.profiles import birth_profile_from_user
from app.config import get_settings
from app.database import crud
from app.database.session import get_session
from app.webapp.security import extract_user_id_from_init_data

router = APIRouter(prefix="/api", tags=["mini-app"])
interpreter = AIInterpreter()


class CompatibilityRequest(BaseModel):
    birth_date: str = Field(..., examples=["24.08.1992"])
    birth_time: str | None = Field(default=None, examples=["14:30"])
    birth_place: str = Field(..., examples=["Москва, Россия"])


async def resolve_user_id(
    init_data: str | None = Query(default=None, alias="initData"),
    telegram_id: int | None = Query(default=None),
) -> int:
    settings = get_settings()
    if init_data:
        try:
            return extract_user_id_from_init_data(init_data, settings.bot_token.get_secret_value())
        except ValueError as exc:
            raise HTTPException(status_code=401, detail="Invalid Telegram initData") from exc
    if telegram_id and settings.environment == "development":
        return telegram_id
    raise HTTPException(status_code=401, detail="Telegram initData is required")


@router.get("/me")
async def get_me(
    user_id: int = Depends(resolve_user_id),
    session: AsyncSession = Depends(get_session),
):
    user = await crud.get_user_with_birth_data(session, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
        "username": user.username,
        "subscription_type": user.subscription_type,
        "subscription_expires_at": user.subscription_expires_at,
        "gdpr_consent": user.gdpr_consent,
        "has_birth_data": user.birth_data is not None,
    }


@router.get("/chart")
async def get_chart(
    user_id: int = Depends(resolve_user_id),
    session: AsyncSession = Depends(get_session),
):
    user = await crud.get_user_with_birth_data(session, user_id)
    if user is None or user.birth_data is None:
        raise HTTPException(status_code=404, detail="Birth data not found")
    chart = build_natal_chart(birth_profile_from_user(user))
    return {
        "profile": {
            "birth_date": user.birth_data.birth_date,
            "birth_time": user.birth_data.birth_time,
            "birth_place": user.birth_data.birth_place,
            "latitude": user.birth_data.latitude,
            "longitude": user.birth_data.longitude,
            "timezone": user.birth_data.timezone,
        },
        "planets": planet_table(chart),
        "aspects": [aspect.__dict__ for aspect in chart.aspects],
        "transits": [transit.__dict__ for transit in calculate_transits(chart)],
        "svg": render_chart_svg(chart),
    }


@router.get("/readings")
async def get_readings(
    user_id: int = Depends(resolve_user_id),
    session: AsyncSession = Depends(get_session),
):
    readings = await crud.get_recent_readings(session, user_id)
    return [
        {
            "id": reading.id,
            "type": reading.reading_type,
            "question": reading.question,
            "response": reading.ai_response,
            "created_at": reading.created_at,
        }
        for reading in readings
    ]


@router.post("/compatibility")
async def create_compatibility(
    request: CompatibilityRequest,
    user_id: int = Depends(resolve_user_id),
    session: AsyncSession = Depends(get_session),
):
    user = await crud.get_user_with_birth_data(session, user_id)
    if user is None or user.birth_data is None:
        raise HTTPException(status_code=404, detail="Birth data not found")
    place = await geocode_place(request.birth_place)
    partner_profile = BirthProfile(
        birth_date=parse_birth_date(request.birth_date),
        birth_time=parse_birth_time(request.birth_time) if request.birth_time else None,
        birth_place=place.name,
        latitude=place.latitude,
        longitude=place.longitude,
        timezone=place.timezone,
    )
    left = build_natal_chart(birth_profile_from_user(user))
    right = build_natal_chart(partner_profile)
    reading = await interpreter.compatibility(left, right)
    await crud.save_reading(session, user_id, "compatibility", reading, question=f"Mini App: {place.name}")
    return {"reading": reading, "partner_place": place.name}


@router.get("/transits")
async def get_transits(
    target_date: date | None = None,
    user_id: int = Depends(resolve_user_id),
    session: AsyncSession = Depends(get_session),
):
    user = await crud.get_user_with_birth_data(session, user_id)
    if user is None or user.birth_data is None:
        raise HTTPException(status_code=404, detail="Birth data not found")
    chart = build_natal_chart(birth_profile_from_user(user))
    return [transit.__dict__ for transit in calculate_transits(chart, target_date)]
