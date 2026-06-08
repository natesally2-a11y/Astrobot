from fastapi import APIRouter, Depends, HTTPException

from app.astrology.ai_interpreter import AstrologyInterpreter
from app.astrology.calculations import calculate_natal_chart, chart_to_dict
from app.astrology.chart_renderer import render_chart_svg
from app.database.crud import get_user_with_birth_data
from app.database.session import async_session
from app.webapp.security import get_webapp_user_id

router = APIRouter(prefix="/api", tags=["mini-app"])


@router.get("/profile")
async def profile(user_id: int = Depends(get_webapp_user_id)) -> dict:
    async with async_session() as session:
        user = await get_user_with_birth_data(session, user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="Profile not found.")
    birth = user.birth_data
    return {
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
        "username": user.username,
        "subscription_type": user.subscription_type,
        "subscription_expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
        "has_birth_data": birth is not None,
        "birth_data": {
            "birth_date": birth.birth_date.isoformat(),
            "birth_time": birth.birth_time.isoformat() if birth.birth_time else None,
            "birth_place": birth.birth_place,
        }
        if birth
        else None,
    }


@router.get("/chart")
async def chart(user_id: int = Depends(get_webapp_user_id)) -> dict:
    natal_chart = await _load_chart(user_id)
    return chart_to_dict(natal_chart)


@router.get("/chart.svg")
async def chart_svg(user_id: int = Depends(get_webapp_user_id)) -> dict:
    natal_chart = await _load_chart(user_id)
    return {"svg": render_chart_svg(natal_chart)}


@router.post("/reading")
async def reading(user_id: int = Depends(get_webapp_user_id)) -> dict:
    natal_chart = await _load_chart(user_id)
    return {"reading": await AstrologyInterpreter().natal_reading(natal_chart)}


async def _load_chart(user_id: int):
    async with async_session() as session:
        user = await get_user_with_birth_data(session, user_id)

    if user is None or user.birth_data is None:
        raise HTTPException(status_code=404, detail="Natal chart not found. Complete onboarding in the bot.")

    birth = user.birth_data
    return calculate_natal_chart(
        birth.birth_date,
        birth.birth_time,
        birth.birth_place,
        float(birth.latitude) if birth.latitude is not None else None,
        float(birth.longitude) if birth.longitude is not None else None,
    )
