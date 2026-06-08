"""GDPR-related commands: /privacy, /my_data, /export_data, /delete_data."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.texts import PRIVACY_TEXT
from app.database import crud
from app.database.models import User

router = Router(name="privacy")


def _default_serializer(value):
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Cannot serialize {type(value)}")


@router.message(Command("privacy"))
async def cmd_privacy(message: Message) -> None:
    await message.answer(PRIVACY_TEXT, parse_mode="HTML")


@router.message(Command("my_data"))
async def cmd_my_data(message: Message, session: AsyncSession, user: User) -> None:
    birth = await crud.get_birth_data(session, user.telegram_id)
    readings = await crud.get_recent_readings(session, user.telegram_id, limit=5)
    lines = [
        f"<b>Ваши данные</b>",
        f"Telegram ID: <code>{user.telegram_id}</code>",
        f"Имя: {user.first_name or '—'}",
        f"Username: @{user.username}" if user.username else "Username: —",
        f"Согласие GDPR: {'да' if user.gdpr_consent else 'нет'}",
        f"Подписка: {user.subscription_type}",
    ]
    if birth:
        lines.append("")
        lines.append("<b>Данные рождения</b>")
        lines.append(f"Дата: {birth.birth_date.strftime('%d.%m.%Y')}")
        if birth.birth_time:
            lines.append(f"Время: {birth.birth_time.strftime('%H:%M')}")
        lines.append(f"Место: {birth.birth_place}")
        if birth.latitude is not None and birth.longitude is not None:
            lines.append(f"Координаты: {float(birth.latitude):.4f}, {float(birth.longitude):.4f}")
        if birth.timezone:
            lines.append(f"Часовой пояс: {birth.timezone}")
    if readings:
        lines.append("")
        lines.append("<b>Последние чтения</b>")
        for r in readings:
            lines.append(f"• {r.created_at.strftime('%d.%m %H:%M')} — {r.reading_type}")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("export_data"))
async def cmd_export_data(
    message: Message, session: AsyncSession, user: User
) -> None:
    birth = await crud.get_birth_data(session, user.telegram_id)
    readings = await crud.get_recent_readings(session, user.telegram_id, limit=200)
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": {
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "username": user.username,
            "language_code": user.language_code,
            "created_at": user.created_at,
            "subscription_type": user.subscription_type,
            "subscription_expires_at": user.subscription_expires_at,
            "gdpr_consent": user.gdpr_consent,
            "gdpr_consent_date": user.gdpr_consent_date,
        },
        "birth_data": None
        if birth is None
        else {
            "birth_date": birth.birth_date,
            "birth_time": birth.birth_time,
            "birth_place": birth.birth_place,
            "latitude": birth.latitude,
            "longitude": birth.longitude,
            "timezone": birth.timezone,
        },
        "readings": [
            {
                "id": r.id,
                "type": r.reading_type,
                "question": r.question,
                "response": r.ai_response,
                "created_at": r.created_at,
            }
            for r in readings
        ],
    }
    data = json.dumps(payload, ensure_ascii=False, indent=2, default=_default_serializer)
    file = BufferedInputFile(data.encode("utf-8"), filename="stellarium_export.json")
    await message.answer_document(
        document=file,
        caption="📥 Экспорт данных согласно GDPR Right to Portability.",
    )


@router.message(Command("delete_data"))
async def cmd_delete_data(
    message: Message, session: AsyncSession, user: User
) -> None:
    await crud.delete_user(session, user.telegram_id)
    await message.answer(
        "🗑 Все ваши данные удалены. Если захотите вернуться — нажмите /start."
    )
