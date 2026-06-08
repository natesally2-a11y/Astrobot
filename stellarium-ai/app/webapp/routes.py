"""
FastAPI routes for the Telegram Mini App.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import urllib.parse
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.connection import get_db
from app.database import crud
from app.astrology.calculations import NatalChart
from app.astrology.chart_renderer import render_natal_chart_svg

router = APIRouter()
templates = Jinja2Templates(directory="app/webapp/templates")


def _validate_init_data(init_data: str) -> dict | None:
    """Validate Telegram WebApp initData."""
    try:
        parsed = dict(urllib.parse.parse_qsl(init_data))
        hash_value = parsed.pop("hash", None)
        if not hash_value:
            return None

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )
        secret_key = hmac.new(
            b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256
        ).digest()
        expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected, hash_value):
            return None

        if "user" in parsed:
            parsed["user"] = json.loads(parsed["user"])
        return parsed
    except Exception:
        return None


@router.get("/app", response_class=HTMLResponse)
async def webapp_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/api/chart/{user_id}")
async def get_chart_data(
    user_id: int,
    init_data: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
):
    birth_data = await crud.get_birth_data(session, user_id)
    if not birth_data:
        raise HTTPException(status_code=404, detail="Birth data not found")

    chart = NatalChart(
        birth_date=birth_data.birth_date,
        birth_time=birth_data.birth_time,
        latitude=float(birth_data.latitude or 55.75),
        longitude=float(birth_data.longitude or 37.62),
        timezone=birth_data.timezone or "Europe/Moscow",
    )

    return JSONResponse(chart.to_dict())


@router.get("/api/chart/{user_id}/svg")
async def get_chart_svg(
    user_id: int,
    session: AsyncSession = Depends(get_db),
):
    birth_data = await crud.get_birth_data(session, user_id)
    if not birth_data:
        raise HTTPException(status_code=404, detail="Birth data not found")

    user = await crud.get_user(session, user_id)
    user_name = user.display_name if user else "Пользователь"

    chart = NatalChart(
        birth_date=birth_data.birth_date,
        birth_time=birth_data.birth_time,
        latitude=float(birth_data.latitude or 55.75),
        longitude=float(birth_data.longitude or 37.62),
        timezone=birth_data.timezone or "Europe/Moscow",
    )

    svg = render_natal_chart_svg(chart, f"Карта {user_name}")
    from fastapi.responses import Response
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/api/user/{user_id}")
async def get_user_info(
    user_id: int,
    session: AsyncSession = Depends(get_db),
):
    user = await crud.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "telegram_id": user.telegram_id,
        "display_name": user.display_name,
        "subscription_type": user.subscription_type,
        "subscription_expires_at": (
            user.subscription_expires_at.isoformat()
            if user.subscription_expires_at else None
        ),
        "is_pro": user.is_pro,
        "is_oracle": user.is_oracle,
    }


@router.get("/api/readings/{user_id}")
async def get_readings(
    user_id: int,
    limit: int = 10,
    session: AsyncSession = Depends(get_db),
):
    readings = await crud.get_user_readings(session, user_id, limit=limit)
    return [
        {
            "id": r.id,
            "type": r.reading_type,
            "question": r.question,
            "response": r.ai_response,
            "created_at": r.created_at.isoformat(),
        }
        for r in readings
    ]


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "stellarium-ai"}
