"""REST API routes for the Mini App."""

import hashlib
import hmac
import json
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.database.crud import (
    get_user_with_birth_data,
    get_birth_data,
    check_subscription_level,
    get_readings,
    export_user_data,
)
from app.astrology.calculations import calculate_natal_chart, format_chart_text
from app.astrology.chart_renderer import render_natal_chart_svg

api_router = APIRouter(prefix="/api")


def validate_init_data(init_data: str) -> dict | None:
    """Validate Telegram WebApp init data."""
    try:
        parsed = parse_qs(init_data)
        received_hash = parsed.get("hash", [None])[0]
        if not received_hash:
            return None

        data_check_pairs = []
        for key, values in sorted(parsed.items()):
            if key != "hash":
                data_check_pairs.append(f"{key}={values[0]}")
        data_check_string = "\n".join(data_check_pairs)

        secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if computed_hash != received_hash:
            return None

        user_data = parsed.get("user", [None])[0]
        if user_data:
            return json.loads(user_data)
        return None
    except Exception:
        return None


@api_router.get("/chart/{user_id}")
async def get_chart(user_id: int):
    """Get natal chart data and SVG for a user."""
    bd = await get_birth_data(user_id)
    if not bd:
        raise HTTPException(status_code=404, detail="Birth data not found")

    chart = calculate_natal_chart(
        birth_date=bd.birth_date,
        birth_time=bd.birth_time,
        latitude=float(bd.latitude) if bd.latitude else 55.7558,
        longitude=float(bd.longitude) if bd.longitude else 37.6173,
    )

    return {
        "chart_text": format_chart_text(chart),
        "sun_sign": chart.sun_sign,
        "moon_sign": chart.moon_sign,
        "rising_sign": chart.rising_sign,
        "planets": [
            {
                "name": p.name,
                "symbol": p.symbol,
                "sign": p.sign,
                "sign_symbol": p.sign_symbol,
                "degree": round(p.degree_in_sign, 2),
                "house": p.house,
                "retrograde": p.retrograde,
            }
            for p in chart.planets
        ],
        "houses": [
            {"number": h.number, "sign": h.sign, "degree": round(h.degree, 2)}
            for h in chart.houses
        ],
        "aspects": [
            {
                "planet1": a.planet1,
                "planet2": a.planet2,
                "type": a.aspect_type,
                "orb": round(a.orb, 2),
            }
            for a in chart.aspects[:20]
        ],
    }


@api_router.get("/chart/{user_id}/svg")
async def get_chart_svg(user_id: int):
    """Get natal chart as SVG."""
    from fastapi.responses import Response

    bd = await get_birth_data(user_id)
    if not bd:
        raise HTTPException(status_code=404, detail="Birth data not found")

    chart = calculate_natal_chart(
        birth_date=bd.birth_date,
        birth_time=bd.birth_time,
        latitude=float(bd.latitude) if bd.latitude else 55.7558,
        longitude=float(bd.longitude) if bd.longitude else 37.6173,
    )

    svg = render_natal_chart_svg(chart)
    return Response(content=svg, media_type="image/svg+xml")


@api_router.get("/user/{user_id}")
async def get_user_info(user_id: int):
    """Get user profile and subscription info."""
    user = await get_user_with_birth_data(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    level = await check_subscription_level(user_id)
    result = {
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
        "subscription": level,
        "has_birth_data": user.birth_data is not None,
    }

    if user.birth_data:
        bd = user.birth_data
        result["birth_data"] = {
            "birth_date": bd.birth_date.isoformat(),
            "birth_time": bd.birth_time.isoformat() if bd.birth_time else None,
            "birth_place": bd.birth_place,
        }

    return result


@api_router.get("/readings/{user_id}")
async def get_user_readings(user_id: int, limit: int = Query(default=20, le=50)):
    """Get reading history."""
    readings = await get_readings(user_id, limit=limit)
    return [
        {
            "id": r.id,
            "type": r.reading_type,
            "question": r.question,
            "response": r.ai_response[:200] + "..." if r.ai_response and len(r.ai_response) > 200 else r.ai_response,
            "date": r.created_at.isoformat() if r.created_at else None,
        }
        for r in readings
    ]


@api_router.get("/subscription/plans")
async def get_plans():
    """Get available subscription plans."""
    return {
        "plans": [
            {
                "id": "free",
                "name": "Бесплатный",
                "price": 0,
                "stars": 0,
                "features": [
                    "Натальная карта",
                    "Базовый анализ",
                    "Краткий ежедневный прогноз",
                    "5 вопросов в день",
                ],
            },
            {
                "id": "pro",
                "name": "Stellarium Pro",
                "price": 99,
                "stars": settings.pro_stars_price,
                "features": [
                    "Подробные прогнозы",
                    "Недельные и месячные прогнозы",
                    "Совместимость (3 партнёра)",
                    "Безлимитные вопросы",
                    "Уведомления о транзитах",
                ],
            },
            {
                "id": "oracle",
                "name": "Космический Оракул",
                "price": 299,
                "stars": settings.oracle_stars_price,
                "features": [
                    "Всё из Pro",
                    "Бизнес-астрология",
                    "Годовые прогнозы",
                    "Индивидуальные ритуалы",
                    "Приоритетная поддержка",
                ],
            },
        ]
    }
