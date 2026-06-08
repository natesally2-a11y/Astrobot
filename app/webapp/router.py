from __future__ import annotations

from datetime import date, time

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology.ai_interpreter import interpret_daily_forecast
from app.astrology.calculations import calculate_natal_chart
from app.astrology.chart_renderer import render_chart_svg
from app.config import DISCLAIMER_TEXT, get_settings
from app.database.crud import export_user_bundle, get_recent_readings
from app.database.models import BirthData
from app.database.session import get_db_session


router = APIRouter()
settings = get_settings()
templates = Jinja2Templates(directory="app/webapp/templates")


def _demo_chart():
    return calculate_natal_chart(
        birth_date=date.fromisoformat(settings.sample_birth_date),
        birth_time=time.fromisoformat(settings.sample_birth_time),
        birth_place=settings.sample_birth_place,
        latitude=55.7558,
        longitude=37.6176,
        timezone_name="Europe/Moscow",
    )


async def _resolve_chart(session: AsyncSession, telegram_id: int | None):
    if telegram_id is None:
        return _demo_chart(), None, []

    birth_data = await session.get(BirthData, telegram_id)
    if birth_data is None:
        return _demo_chart(), None, []

    chart = calculate_natal_chart(
        birth_date=birth_data.birth_date,
        birth_time=birth_data.birth_time,
        birth_place=birth_data.birth_place,
        latitude=birth_data.latitude,
        longitude=birth_data.longitude,
        timezone_name=birth_data.timezone,
    )
    bundle = await export_user_bundle(session, telegram_id)
    readings = await get_recent_readings(session, telegram_id, limit=8)
    return chart, bundle, readings


@router.get("/app", response_class=HTMLResponse)
async def webapp_index(
    request: Request,
    telegram_id: int | None = Query(default=None),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.app_name,
            "base_url": settings.base_url.rstrip("/"),
            "telegram_id": telegram_id,
            "bot_username": settings.bot_username,
            "disclaimer": DISCLAIMER_TEXT,
        },
    )


@router.get("/api/webapp/profile")
async def get_profile(
    telegram_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> JSONResponse:
    chart, bundle, readings = await _resolve_chart(session, telegram_id)
    if bundle is None:
        bundle = {
            "user": {
                "telegram_id": None,
                "first_name": "Demo User",
                "subscription_type": "free",
            },
            "birth_data": {
                "birth_place": chart.birth_place,
                "birth_date": chart.birth_date,
                "birth_time": chart.birth_time,
            },
        }

    payload = {
        "user": bundle["user"],
        "birth_data": bundle.get("birth_data"),
        "chart_summary": chart.summary,
        "plan": bundle["user"].get("subscription_type", "free"),
        "recent_readings": [
            {
                "reading_type": reading.reading_type,
                "excerpt": reading.ai_response[:180],
                "created_at": reading.created_at.isoformat(),
            }
            for reading in readings
        ],
        "disclaimer": DISCLAIMER_TEXT,
    }
    return JSONResponse(payload)


@router.get("/api/webapp/chart")
async def get_chart(
    telegram_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> JSONResponse:
    chart, _, _ = await _resolve_chart(session, telegram_id)
    return JSONResponse(chart.as_dict())


@router.get("/api/webapp/chart.svg")
async def get_chart_svg(
    telegram_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    chart, _, _ = await _resolve_chart(session, telegram_id)
    svg = render_chart_svg(chart)
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/api/webapp/daily")
async def get_daily(
    telegram_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> JSONResponse:
    chart, _, _ = await _resolve_chart(session, telegram_id)
    forecast = await interpret_daily_forecast(chart)
    return JSONResponse({"forecast": forecast, "disclaimer": DISCLAIMER_TEXT})
