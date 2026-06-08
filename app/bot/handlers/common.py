from __future__ import annotations

import json
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import main_menu_keyboard, settings_keyboard
from app.bot.utils.texts import DISCLAIMER_TEXT, HELP_TEXT
from app.config import get_settings
from app.database import crud

router = Router(name=__name__)
settings = get_settings()


def _app_url_for_user(user_id: int) -> str | None:
    base = settings.webapp_base_url or settings.webhook_url
    if not base:
        return None
    return f"{base.rstrip('/')}/app?user_id={user_id}"


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("privacy"))
async def privacy_command(message: Message) -> None:
    await message.answer(
        "Политика конфиденциальности: сбор минимально необходимых данных рождения и профиля Telegram.\n"
        "Использование данных: астрологические расчёты, персональные прогнозы, подписки.\n"
        "Удаление: /delete_data.\n"
        "Экспорт: /export_data.\n"
        "Полный текст см. в privacy_policy.md."
    )


@router.message(Command("settings"))
async def settings_command(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    user = await crud.get_user(session, message.from_user.id)
    if user is None:
        await message.answer("Сначала запустите /start.")
        return
    expiry = (
        user.subscription_expires_at.strftime("%Y-%m-%d")
        if user.subscription_expires_at
        else "не активна"
    )
    await message.answer(
        f"Текущий план: <b>{user.subscription_type}</b>\n"
        f"Действует до: <b>{expiry}</b>\n\n"
        "Выберите план:",
        reply_markup=settings_keyboard(),
    )


@router.message(Command("my_data"))
async def my_data_command(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    user, birth = await crud.get_user_full_profile(session, message.from_user.id)
    if user is None:
        await message.answer("Данные не найдены. Используйте /start.")
        return
    username_line = f"• Username: @{user.username}" if user.username else "• Username: -"
    await message.answer(
        "Ваши данные:\n"
        f"• Telegram ID: {user.telegram_id}\n"
        f"• Имя: {user.first_name or '-'}\n"
        f"{username_line}"
    )
    await message.answer(
        "Данные рождения:\n"
        f"• Дата: {birth.birth_date if birth else '-'}\n"
        f"• Время: {birth.birth_time if birth and birth.birth_time else '-'}\n"
        f"• Место: {birth.birth_place if birth else '-'}\n"
        f"• Координаты: {birth.latitude if birth else '-'}, {birth.longitude if birth else '-'}\n"
        f"• Согласие GDPR: {'да' if user.gdpr_consent else 'нет'}"
    )


@router.message(Command("export_data"))
async def export_data_command(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    payload = await crud.export_user_data(session, message.from_user.id)
    if not payload:
        await message.answer("Нет данных для экспорта.")
        return
    content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    filename = f"stellarium_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    await message.answer_document(
        BufferedInputFile(content, filename=filename),
        caption="Экспорт данных (GDPR portability).",
    )


@router.message(Command("delete_data"))
async def delete_data_command(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    deleted = await crud.delete_user_data(session, message.from_user.id)
    if deleted:
        await message.answer("✅ Все данные удалены. Для повторной регистрации используйте /start.")
    else:
        await message.answer("Данные не найдены.")


@router.message(Command("disclaimer"))
async def disclaimer_command(message: Message) -> None:
    await message.answer(DISCLAIMER_TEXT)


@router.message(Command("menu"))
async def menu_command(message: Message) -> None:
    if message.from_user is None:
        return
    await message.answer("Главное меню", reply_markup=main_menu_keyboard(_app_url_for_user(message.from_user.id)))
