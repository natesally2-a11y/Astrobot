from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.astrology.calculations import build_natal_chart, compatibility_snapshot
from app.astrology.chart_renderer import render_chart_svg
from app.database.crud import get_readings, get_user_with_birth_data
from app.database.session import AsyncSessionLocal

router = APIRouter()
templates = Jinja2Templates(directory="app/webapp/templates")


@router.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    return HTMLResponse("<h3>Stellarium AI is running</h3><p>Open /app for mini app UI.</p>")


@router.get("/app", response_class=HTMLResponse)
async def mini_app(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("app.html", {"request": request})


@router.get("/api/health")
async def api_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/user/{telegram_id}")
async def api_user(telegram_id: int) -> dict:
    async with AsyncSessionLocal() as session:
        user, birth_data = await get_user_with_birth_data(session, telegram_id)
        if not user or not birth_data:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "subscription_type": user.subscription_type,
            "subscription_expires_at": user.subscription_expires_at,
            "birth_data": {
                "birth_date": birth_data.birth_date,
                "birth_time": birth_data.birth_time,
                "birth_place": birth_data.birth_place,
                "latitude": birth_data.latitude,
                "longitude": birth_data.longitude,
            },
        }


@router.get("/api/chart/{telegram_id}")
async def api_chart(telegram_id: int) -> dict[str, str]:
    async with AsyncSessionLocal() as session:
        _, birth_data = await get_user_with_birth_data(session, telegram_id)
        if not birth_data:
            raise HTTPException(status_code=404, detail="Birth data not found")
    chart = build_natal_chart(
        birth_date=birth_data.birth_date,
        birth_time=birth_data.birth_time,
        latitude=birth_data.latitude,
        longitude=birth_data.longitude,
    )
    return {"svg": render_chart_svg(chart), "sun_sign": chart.sun_sign}


@router.get("/api/readings/{telegram_id}")
async def api_readings(telegram_id: int) -> list[dict]:
    async with AsyncSessionLocal() as session:
        rows = await get_readings(session, telegram_id, limit=50)
    return [
        {
            "reading_type": row.reading_type,
            "question": row.question,
            "ai_response": row.ai_response,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/api/compatibility")
async def api_compatibility(first_date: date, second_date: date) -> dict[str, str]:
    first_chart = build_natal_chart(first_date, None, None, None)
    second_chart = build_natal_chart(second_date, None, None, None)
    return {"result": compatibility_snapshot(first_chart, second_chart)}

