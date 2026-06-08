"""
/settings command handler.
"""
from __future__ import annotations

import json
from typing import Optional
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from app.database import crud
from app.database.models import User
from app.bot.keyboards.inline import (
    get_settings_keyboard, get_confirm_delete_keyboard, get_subscription_keyboard,
    get_main_menu_keyboard,
)
from app.bot.states import RegistrationStates

router = Router(name="settings")


@router.message(Command("settings"))
async def cmd_settings_msg(message: Message, session=None, db_user: Optional[User] = None):
    await cmd_settings(message, session, message.from_user.id, db_user)


async def cmd_settings(message: Message, session, user_id: int, db_user: Optional[User] = None):
    user = db_user or await crud.get_user(session, user_id)
    is_pro = user.is_pro if user else False
    is_oracle = user.is_oracle if user else False

    if is_oracle:
        sub_status = "🔮 Космический Оракул"
    elif is_pro:
        sub_status = "⭐ Stellarium Pro"
    else:
        sub_status = "🆓 Бесплатный план"

    expires = ""
    if user and user.subscription_expires_at:
        expires = f"\nДействует до: {user.subscription_expires_at.strftime('%d.%m.%Y')}"

    await message.answer(
        f"⚙️ <b>Настройки</b>\n\n"
        f"👤 {user.display_name if user else 'Пользователь'}\n"
        f"📦 Подписка: {sub_status}{expires}\n\n"
        f"Реферальная ссылка:\n"
        f"<code>https://t.me/stellarium_ai_bot?start=ref_{user_id}</code>\n\n"
        f"<i>Поделитесь ссылкой — получите +7 дней Pro за каждого друга!</i>",
        parse_mode="HTML",
        reply_markup=get_settings_keyboard(is_pro=is_pro),
    )


@router.callback_query(F.data.startswith("settings:"))
async def handle_settings(
    callback: CallbackQuery, state: FSMContext, session=None, db_user: Optional[User] = None
):
    action = callback.data.split(":")[1]
    user_id = callback.from_user.id
    await callback.answer()

    if action == "edit_birth":
        await callback.message.answer(
            "✏️ Давайте обновим данные рождения.\n\n"
            "📅 Выберите год рождения:",
            reply_markup=__import__(
                "app.bot.keyboards.inline", fromlist=["get_year_keyboard"]
            ).get_year_keyboard(),
        )
        await state.set_state(RegistrationStates.waiting_for_birth_year)

    elif action == "my_data":
        from app.bot.handlers.privacy import show_my_data
        await show_my_data(callback.message, session, user_id)

    elif action == "privacy":
        from app.bot.handlers.privacy import show_privacy_text
        await show_privacy_text(callback.message)

    elif action == "export":
        from app.bot.handlers.privacy import export_user_data
        await export_user_data(callback.message, session, user_id)

    elif action == "delete":
        await callback.message.answer(
            "⚠️ <b>Удаление аккаунта</b>\n\n"
            "Все ваши данные будут безвозвратно удалены:\n"
            "• Данные рождения\n"
            "• История чтений\n"
            "• Информация о подписке\n\n"
            "Вы уверены?",
            parse_mode="HTML",
            reply_markup=get_confirm_delete_keyboard(),
        )

    elif action == "subscribe":
        await callback.message.answer(
            "⭐ <b>Выберите подписку</b>",
            parse_mode="HTML",
            reply_markup=get_subscription_keyboard(),
        )


@router.callback_query(F.data == "confirm:delete")
async def confirm_delete(callback: CallbackQuery, session=None):
    await callback.answer()
    user_id = callback.from_user.id
    await crud.delete_user_data(session, user_id)
    await callback.message.answer(
        "✅ Все ваши данные успешно удалены.\n\n"
        "Используйте /start для повторной регистрации.\n\n"
        "До свидания! 🌟"
    )


@router.callback_query(F.data == "confirm:cancel")
async def confirm_cancel(callback: CallbackQuery):
    await callback.answer("Отменено")
    await callback.message.delete()
