import hashlib
import hmac
import json
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.astrology import ChartCalculator, ChartRenderer
from app.bot.utils.geocoding import timezone_to_offset
from app.config import get_settings
from app.database import crud
from app.database.session import async_session

router = APIRouter()
templates = Jinja2Templates(directory="app/webapp/templates")
calculator = ChartCalculator()
renderer = ChartRenderer()
settings = get_settings()


async def get_session():
    async with async_session() as session:
        yield session


def validate_telegram_init_data(init_data: str) -> dict | None:
    if not init_data:
        return None
    try:
        parsed = dict(item.split("=", 1) for item in init_data.split("&") if "=" in item)
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None
        data_check_string = "\n".join(f"{k}={unquote(v)}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
        calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if calculated != received_hash:
            return None
        user_data = parsed.get("user")
        if user_data:
            return json.loads(unquote(user_data))
        return parsed
    except Exception:
        return None


@router.get("/app", response_class=HTMLResponse)
async def mini_app(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "webapp_url": settings.webapp_url})


@router.get("/app/chart")
async def get_chart(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    user_info = validate_telegram_init_data(init_data)
    if not user_info:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user_info.get("id")
    user = await crud.get_user(session, user_id)
    if not user or not user.birth_data:
        return JSONResponse({"error": "no_chart", "message": "Создайте карту через /start"})

    bd = user.birth_data
    tz_offset = timezone_to_offset(bd.timezone or "UTC+3")
    chart = calculator.calculate_natal_chart(
        bd.birth_date,
        bd.birth_time,
        float(bd.latitude),
        float(bd.longitude),
        tz_offset,
    )
    chart_data = renderer.render_json(chart)
    plan = crud.get_effective_plan(user)

    return JSONResponse({
        "chart": chart_data,
        "birth_place": bd.birth_place,
        "birth_date": str(bd.birth_date),
        "subscription": plan,
        "subscription_expires": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
    })


@router.get("/app/readings")
async def get_readings(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    user_info = validate_telegram_init_data(init_data)
    if not user_info:
        raise HTTPException(status_code=401, detail="Unauthorized")

    readings = await crud.get_readings(session, user_info["id"], limit=20)
    return JSONResponse({
        "readings": [
            {
                "type": r.reading_type,
                "question": r.question,
                "response": r.ai_response[:500] if r.ai_response else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in readings
        ]
    })


@router.get("/app/profile")
async def get_profile(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    user_info = validate_telegram_init_data(init_data)
    if not user_info:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = await crud.get_user(session, user_info["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return JSONResponse({
        "first_name": user.first_name,
        "subscription": crud.get_effective_plan(user),
        "subscription_expires": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
        "has_chart": user.birth_data is not None,
        "gdpr_consent": user.gdpr_consent,
    })
