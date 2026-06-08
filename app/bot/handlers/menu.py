"""Routing for inline main-menu buttons and reply-keyboard shortcuts."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.bot.handlers import chart as chart_handler
from app.bot.handlers import forecast as forecast_handler
from app.bot.keyboards.inline import main_menu_keyboard
from app.bot.states import AskFlow, CompatibilityFlow
from app.bot.handlers._common import get_birth_data_or_prompt
from app.database.models import User

router = Router(name="menu")


@router.callback_query(F.data == "menu:chart")
async def menu_chart(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    await chart_handler.cmd_chart(callback.message, session, user)
    await callback.answer()


@router.callback_query(F.data == "menu:today")
async def menu_today(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    await forecast_handler.cmd_today(callback.message, session, user)
    await callback.answer()


@router.callback_query(F.data == "menu:ask")
async def menu_ask(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AskFlow.waiting_question)
    await callback.message.answer(texts.ASK_PROMPT)
    await callback.answer()


@router.callback_query(F.data == "menu:compat")
async def menu_compat(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User
) -> None:
    bd = await get_birth_data_or_prompt(callback.message, session, user)
    if bd is None:
        await callback.answer()
        return
    await state.set_state(CompatibilityFlow.partner_date)
    await callback.message.answer(texts.ASK_COMPAT_PARTNER, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "menu:back")
async def menu_back(callback: CallbackQuery) -> None:
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()


# --- Reply-keyboard shortcuts ---


@router.message(F.text == "🪐 Карта")
async def rk_chart(message: Message, session: AsyncSession, user: User) -> None:
    await chart_handler.cmd_chart(message, session, user)


@router.message(F.text == "☀️ Сегодня")
async def rk_today(message: Message, session: AsyncSession, user: User) -> None:
    await forecast_handler.cmd_today(message, session, user)


@router.message(F.text == "💬 Спросить")
async def rk_ask(message: Message, state: FSMContext) -> None:
    await state.set_state(AskFlow.waiting_question)
    await message.answer(texts.ASK_PROMPT)


@router.message(F.text == "💞 Совместимость")
async def rk_compat(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    bd = await get_birth_data_or_prompt(message, session, user)
    if bd is None:
        return
    await state.set_state(CompatibilityFlow.partner_date)
    await message.answer(texts.ASK_COMPAT_PARTNER, parse_mode="Markdown")


@router.message(F.text == "⚙️ Настройки")
async def rk_settings(message: Message, user: User) -> None:
    from app.bot.handlers.settings import cmd_settings

    await cmd_settings(message, user)
