from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder


def subscription_keyboard(webapp_url: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Купить Stellarium Pro", callback_data="buy:pro")
    builder.button(text="Купить Cosmic Oracle", callback_data="buy:oracle")
    if webapp_url:
        builder.button(text="Открыть Mini App", web_app=WebAppInfo(url=webapp_url))
    builder.adjust(1)
    return builder.as_markup()


def delete_data_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Удалить все данные", callback_data="delete:confirm")
    builder.button(text="Отмена", callback_data="delete:cancel")
    builder.adjust(1)
    return builder.as_markup()
