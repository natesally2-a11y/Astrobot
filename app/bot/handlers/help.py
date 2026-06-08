"""/help command."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot import texts
from app.bot.keyboards.inline import main_menu_keyboard

router = Router(name="help")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(texts.HELP, parse_mode="Markdown", reply_markup=main_menu_keyboard())
