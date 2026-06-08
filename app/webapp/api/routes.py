from datetime import date, time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.astrology.ai_interpreter import generate_compatibility_reading
from app.astrology.calculations import BirthInfo, calculate_compatibility, calculate_natal_chart
from app.astrology.chart_renderer import render_chart_svg
from app.database.crud import get_recent_readings, get_user
from app.database.session import async_session_factory
from app.services.geocoding import search_places

router = APIRouter(prefix='/api', tags=['mini-app'])


class CompatibilityRequest(BaseModel):
    telegram_id: int
    partner_name: str
    birth_date: date
    birth_time: time | None = None
    birth_place: str
    is_time_approximate: bool = False


@router.get('/users/{telegram_id}')
async def user_profile(telegram_id: int) -> dict[str, Any]:
    async with async_session_factory() as session:
        user = await get_user(session, telegram_id)
        if user is None:
            raise HTTPException(status_code=404, detail='User not found')
        return {
            'telegram_id': user.telegram_id,
            'first_name': user.first_name,
            'username': user.username,
            'subscription_type': user.subscription_type,
            'subscription_expires_at': user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
            'gdpr_consent': user.gdpr_consent,
        }


@router.get('/chart/{telegram_id}')
async def user_chart(telegram_id: int) -> dict[str, Any]:
    async with async_session_factory() as session:
        user = await get_user(session, telegram_id)
        if user is None or user.birth_data is None:
            raise HTTPException(status_code=404, detail='Birth data not found')
        birth = user.birth_data
        chart = calculate_natal_chart(
            BirthInfo(
                birth_date=birth.birth_date,
                birth_time=birth.birth_time,
                latitude=float(birth.latitude),
                longitude=float(birth.longitude),
                timezone=birth.timezone or 'UTC',
                birth_place=birth.birth_place,
                is_time_approximate=birth.is_time_approximate,
            )
        )
        return {
            'birth_place': birth.birth_place,
            'birth_date': birth.birth_date.isoformat(),
            'birth_time': birth.birth_time.isoformat() if birth.birth_time else None,
            'timezone': birth.timezone,
            'chart': chart,
            'svg': render_chart_svg(chart),
        }


@router.get('/readings/{telegram_id}')
async def readings(telegram_id: int, limit: int = 10) -> list[dict[str, Any]]:
    async with async_session_factory() as session:
        rows = await get_recent_readings(session, telegram_id, limit=min(limit, 20))
    return [
        {
            'id': row.id,
            'reading_type': row.reading_type,
            'question': row.question,
            'ai_response': row.ai_response,
            'created_at': row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


@router.post('/compatibility')
async def compatibility(payload: CompatibilityRequest) -> dict[str, Any]:
    async with async_session_factory() as session:
        user = await get_user(session, payload.telegram_id)
        if user is None or user.birth_data is None:
            raise HTTPException(status_code=404, detail='User birth data not found')
    places = await search_places(payload.birth_place, limit=1)
    if not places:
        raise HTTPException(status_code=422, detail='Partner place not found')
    place = places[0]
    first_chart = calculate_natal_chart(
        BirthInfo(
            birth_date=user.birth_data.birth_date,
            birth_time=user.birth_data.birth_time,
            latitude=float(user.birth_data.latitude),
            longitude=float(user.birth_data.longitude),
            timezone=user.birth_data.timezone or 'UTC',
            birth_place=user.birth_data.birth_place,
            is_time_approximate=user.birth_data.is_time_approximate,
        )
    )
    second_chart = calculate_natal_chart(
        BirthInfo(
            birth_date=payload.birth_date,
            birth_time=payload.birth_time,
            latitude=place['latitude'],
            longitude=place['longitude'],
            timezone=place['timezone'],
            birth_place=place['name'],
            is_time_approximate=payload.is_time_approximate,
        )
    )
    report = calculate_compatibility(first_chart, second_chart, payload.partner_name)
    interpretation = await generate_compatibility_reading(report, payload.partner_name)
    return {'report': report, 'interpretation': interpretation, 'partner_place': place['name']}
