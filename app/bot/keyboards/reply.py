"""Persistent reply keyboard with the most-used actions."""
from __future__ import annotations

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="🪐 Карта")
    kb.button(text="☀️ Сегодня")
    kb.button(text="💬 Спросить")
    kb.button(text="💞 Совместимость")
    kb.button(text="⚙️ Настройки")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True, input_field_placeholder="Выберите действие…")
