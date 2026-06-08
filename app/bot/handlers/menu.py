"""Главное меню (callback menu:main)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards.common import main_menu_keyboard

router = Router(name="menu")


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(call: CallbackQuery) -> None:
    await call.answer()
    await call.message.answer("🌟 Главное меню Stellarium AI", reply_markup=main_menu_keyboard())
