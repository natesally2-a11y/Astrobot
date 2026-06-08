"""REST endpoints consumed by the Mini App front-end."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.calculations import compute_natal_chart, summarize_chart
from app.astrology.chart_renderer import render_chart_svg
from app.bot.utils.access import has_active_premium, plan_label
from app.database import crud
from app.database.base import async_session_maker
from app.webapp.security import InvalidInitData, telegram_id_from_init_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["miniapp"])


async def _session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


async def _current_user_id(x_init_data: Optional[str] = Header(default=None)) -> int:
    if not x_init_data:
        raise HTTPException(status_code=401, detail="Missing X-Init-Data header")
    try:
        return telegram_id_from_init_data(x_init_data)
    except InvalidInitData as exc:
        logger.info("Mini-app auth rejected: %s", exc)
        raise HTTPException(status_code=401, detail=str(exc))


class ProfileResponse(BaseModel):
    telegram_id: int
    first_name: Optional[str]
    plan: str
    plan_active_until: Optional[str]
    has_birth_data: bool
    asked_today: int


class BirthDataResponse(BaseModel):
    birth_date: str
    birth_time: Optional[str]
    birth_place: str
    latitude: Optional[float]
    longitude: Optional[float]
    timezone: Optional[str]


@router.get("/profile", response_model=ProfileResponse)
async def profile(
    telegram_id: int = Depends(_current_user_id),
    session: AsyncSession = Depends(_session),
) -> ProfileResponse:
    user = await crud.get_user(session, telegram_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found. Open the bot first.")
    birth = await crud.get_birth_data(session, telegram_id)
    asked = await crud.count_questions_today(session, telegram_id)
    return ProfileResponse(
        telegram_id=user.telegram_id,
        first_name=user.first_name,
        plan=plan_label(user) if has_active_premium(user) else "Free",
        plan_active_until=(
            user.subscription_expires_at.isoformat()
            if user.subscription_expires_at
            else None
        ),
        has_birth_data=birth is not None,
        asked_today=asked,
    )


@router.get("/birth", response_model=BirthDataResponse)
async def birth(
    telegram_id: int = Depends(_current_user_id),
    session: AsyncSession = Depends(_session),
) -> BirthDataResponse:
    data = await crud.get_birth_data(session, telegram_id)
    if data is None:
        raise HTTPException(status_code=404, detail="No birth data")
    return BirthDataResponse(
        birth_date=data.birth_date.isoformat(),
        birth_time=data.birth_time.isoformat() if data.birth_time else None,
        birth_place=data.birth_place,
        latitude=float(data.latitude) if data.latitude is not None else None,
        longitude=float(data.longitude) if data.longitude is not None else None,
        timezone=data.timezone,
    )


@router.get("/chart.svg")
async def chart_svg(
    telegram_id: int = Depends(_current_user_id),
    session: AsyncSession = Depends(_session),
):
    birth = await crud.get_birth_data(session, telegram_id)
    if birth is None:
        raise HTTPException(status_code=404, detail="No birth data")
    chart = compute_natal_chart(
        birth_date=birth.birth_date,
        birth_time=birth.birth_time,
        latitude=float(birth.latitude) if birth.latitude is not None else None,
        longitude=float(birth.longitude) if birth.longitude is not None else None,
        tz_name=birth.timezone,
    )
    return Response(
        content=render_chart_svg(chart, size=520),
        media_type="image/svg+xml",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/chart/summary")
async def chart_summary(
    telegram_id: int = Depends(_current_user_id),
    session: AsyncSession = Depends(_session),
) -> dict:
    birth = await crud.get_birth_data(session, telegram_id)
    if birth is None:
        raise HTTPException(status_code=404, detail="No birth data")
    chart = compute_natal_chart(
        birth_date=birth.birth_date,
        birth_time=birth.birth_time,
        latitude=float(birth.latitude) if birth.latitude is not None else None,
        longitude=float(birth.longitude) if birth.longitude is not None else None,
        tz_name=birth.timezone,
    )
    return {
        "summary": summarize_chart(chart, lang="ru"),
        "positions": [
            {
                "name": pos.name,
                "sign": pos.sign,
                "longitude": pos.longitude,
                "degree_in_sign": pos.degree_in_sign,
                "house": pos.house,
                "retrograde": pos.retrograde,
            }
            for pos in chart.positions.values()
        ],
        "aspects": [
            {
                "a": asp.body_a,
                "b": asp.body_b,
                "aspect": asp.aspect,
                "orb": asp.orb,
            }
            for asp in chart.aspects
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/readings")
async def readings(
    telegram_id: int = Depends(_current_user_id),
    session: AsyncSession = Depends(_session),
    limit: int = 20,
) -> list[dict]:
    history = await crud.get_recent_readings(session, telegram_id, limit=limit)
    return [
        {
            "id": r.id,
            "type": r.reading_type,
            "question": r.question,
            "response": r.ai_response,
            "created_at": r.created_at.isoformat(),
        }
        for r in history
    ]


@router.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
