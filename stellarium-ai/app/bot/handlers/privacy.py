"""
GDPR privacy command handlers.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile

from app.database import crud
from app.database.models import User

router = Router(name="privacy")

PRIVACY_TEXT = """🔒 <b>Политика конфиденциальности Stellarium AI</b>

<b>Какие данные мы собираем:</b>
• Telegram ID, имя и username
• Дата, время и место рождения
• История чтений и прогнозов
• Данные подписки

<b>Как мы используем данные:</b>
• Астрологические расчёты
• Персонализированные прогнозы
• Обслуживание подписки

<b>Хранение и защита:</b>
• Данные хранятся на защищённых серверах
• Не передаются третьим лицам
• Зашифрованное соединение (TLS)

<b>Ваши права (GDPR/ФЗ-152):</b>
• Доступ к данным: /my_data
• Удаление данных: /delete_data
• Экспорт данных: /export_data

<b>Срок хранения:</b> До удаления аккаунта пользователем.

По вопросам: @stellarium_support"""


@router.message(Command("privacy"))
async def cmd_privacy(message: Message):
    await show_privacy_text(message)


async def show_privacy_text(message: Message):
    await message.answer(PRIVACY_TEXT, parse_mode="HTML")


@router.message(Command("my_data"))
async def cmd_my_data(message: Message, session=None, db_user: Optional[User] = None):
    await show_my_data(message, session, message.from_user.id, db_user)


async def show_my_data(
    message: Message,
    session,
    user_id: int,
    db_user: Optional[User] = None,
):
    user = db_user or await crud.get_user(session, user_id)
    if not user:
        await message.answer("❌ Аккаунт не найден. Используйте /start.")
        return

    birth_data = await crud.get_birth_data(session, user_id)
    readings = await crud.get_user_readings(session, user_id, limit=5)

    birth_info = "Не указаны"
    if birth_data:
        birth_info = (
            f"\n  Дата: {birth_data.birth_date.strftime('%d.%m.%Y')}\n"
            f"  Время: {birth_data.birth_time or 'Не указано'}\n"
            f"  Место: {birth_data.birth_place}\n"
            f"  Координаты: {birth_data.latitude:.4f}, {birth_data.longitude:.4f}"
        ) if birth_data.latitude else f"\n  Дата: {birth_data.birth_date}\n  Место: {birth_data.birth_place}"

    sub_info = f"{user.subscription_type.upper()}"
    if user.subscription_expires_at:
        sub_info += f" (до {user.subscription_expires_at.strftime('%d.%m.%Y')})"

    recent = f"\n  Последние {len(readings)} из {len(readings)} чтений сохранены"

    await message.answer(
        f"📋 <b>Ваши данные в Stellarium AI</b>\n\n"
        f"👤 <b>Профиль:</b>\n"
        f"  ID: {user.telegram_id}\n"
        f"  Имя: {user.display_name}\n"
        f"  Регистрация: {user.created_at.strftime('%d.%m.%Y')}\n"
        f"  GDPR-согласие: {'✅' if user.gdpr_consent else '❌'}\n\n"
        f"🌟 <b>Подписка:</b> {sub_info}\n\n"
        f"📅 <b>Данные рождения:</b>{birth_info}\n\n"
        f"📚 <b>История чтений:</b>{recent}\n\n"
        f"Используйте /delete_data для удаления или /export_data для экспорта.",
        parse_mode="HTML",
    )


@router.message(Command("delete_data"))
async def cmd_delete_data(message: Message):
    from app.bot.keyboards.inline import get_confirm_delete_keyboard
    await message.answer(
        "⚠️ <b>Удаление всех данных</b>\n\n"
        "Это действие необратимо. Будут удалены:\n"
        "• Данные рождения\n"
        "• История чтений\n"
        "• Информация о подписке\n"
        "• Аккаунт\n\n"
        "Вы уверены?",
        parse_mode="HTML",
        reply_markup=get_confirm_delete_keyboard(),
    )


@router.message(Command("export_data"))
async def cmd_export_data(message: Message, session=None, db_user: Optional[User] = None):
    await export_user_data(message, session, message.from_user.id, db_user)


async def export_user_data(
    message: Message,
    session,
    user_id: int,
    db_user: Optional[User] = None,
):
    user = db_user or await crud.get_user(session, user_id)
    if not user:
        await message.answer("❌ Аккаунт не найден.")
        return

    birth_data = await crud.get_birth_data(session, user_id)
    readings = await crud.get_user_readings(session, user_id, limit=100)

    export = {
        "export_date": datetime.utcnow().isoformat(),
        "user": {
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "created_at": user.created_at.isoformat(),
            "subscription_type": user.subscription_type,
            "gdpr_consent": user.gdpr_consent,
            "gdpr_consent_date": user.gdpr_consent_date.isoformat() if user.gdpr_consent_date else None,
        },
        "birth_data": {
            "birth_date": birth_data.birth_date.isoformat() if birth_data else None,
            "birth_time": str(birth_data.birth_time) if birth_data and birth_data.birth_time else None,
            "birth_place": birth_data.birth_place if birth_data else None,
            "latitude": float(birth_data.latitude) if birth_data and birth_data.latitude else None,
            "longitude": float(birth_data.longitude) if birth_data and birth_data.longitude else None,
            "timezone": birth_data.timezone if birth_data else None,
        },
        "readings": [
            {
                "id": r.id,
                "type": r.reading_type,
                "question": r.question,
                "response": r.ai_response,
                "created_at": r.created_at.isoformat(),
            }
            for r in readings
        ],
    }

    json_bytes = json.dumps(export, ensure_ascii=False, indent=2).encode("utf-8")
    file = BufferedInputFile(json_bytes, filename=f"stellarium_data_{user_id}.json")

    await message.answer_document(
        file,
        caption=(
            "📤 <b>Экспорт данных Stellarium AI</b>\n\n"
            f"Дата экспорта: {datetime.utcnow().strftime('%d.%m.%Y %H:%M')} UTC\n"
            "Формат: JSON"
        ),
        parse_mode="HTML",
    )
