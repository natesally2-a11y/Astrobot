"""Inline keyboards used across the bot."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import settings


def start_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✨ Начать создание карты", callback_data="onboard:start")
    kb.adjust(1)
    return kb.as_markup()


def consent_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Согласен", callback_data="gdpr:accept")
    kb.button(text="📄 Политика конфиденциальности", callback_data="gdpr:policy")
    kb.adjust(1)
    return kb.as_markup()


def time_keyboard() -> InlineKeyboardMarkup:
    """Quick time presets + 'unknown time' option."""
    kb = InlineKeyboardBuilder()
    for hour in range(0, 24, 2):
        kb.button(text=f"{hour:02d}:00", callback_data=f"time:{hour:02d}:00")
    kb.button(text="🤷 Не знаю время", callback_data="time:unknown")
    kb.adjust(4, 4, 4, 1)
    return kb.as_markup()


def webapp_keyboard(text: str = "🌌 Открыть мини-приложение") -> InlineKeyboardMarkup | None:
    if not settings.webapp_url:
        return None
    kb = InlineKeyboardBuilder()
    kb.button(text=text, web_app=WebAppInfo(url=settings.webapp_url.rstrip("/") + "/app"))
    return kb.as_markup()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🪐 Натальная карта", callback_data="menu:chart")
    kb.button(text="☀️ Прогноз на сегодня", callback_data="menu:today")
    kb.button(text="💬 Спросить астролога", callback_data="menu:ask")
    kb.button(text="💞 Совместимость", callback_data="menu:compat")
    kb.button(text="⚙️ Настройки и подписка", callback_data="menu:settings")
    if settings.webapp_url:
        kb.button(
            text="🌌 Мини-приложение",
            web_app=WebAppInfo(url=settings.webapp_url.rstrip("/") + "/app"),
        )
    kb.adjust(1, 2, 1, 1, 1)
    return kb.as_markup()


def subscription_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐ Stellarium Pro — 50 ⭐ (≈99₽)", callback_data="buy:pro")
    kb.button(text="🔮 Космический Оракул — 150 ⭐ (≈299₽)", callback_data="buy:oracle")
    kb.button(text="◀️ Назад", callback_data="menu:back")
    kb.adjust(1)
    return kb.as_markup()


def settings_keyboard(referral_link: str | None = None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐ Управление подпиской", callback_data="menu:subscribe")
    kb.button(text="✏️ Изменить данные рождения", callback_data="onboard:start")
    kb.button(text="📂 Мои данные", callback_data="gdpr:mydata")
    kb.button(text="🔐 Приватность", callback_data="gdpr:policy")
    if referral_link:
        kb.button(text="🎁 Пригласить друга (+7 дней Premium)", url=referral_link)
    kb.adjust(1)
    return kb.as_markup()


def delete_confirm_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Да, удалить всё", callback_data="gdpr:delete_confirm")
    kb.button(text="◀️ Отмена", callback_data="menu:back")
    kb.adjust(1)
    return kb.as_markup()


def place_choice_keyboard(places) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for idx, place in enumerate(places):
        short = place.name if len(place.name) <= 60 else place.name[:57] + "…"
        kb.button(text=short, callback_data=f"place:{idx}")
    kb.adjust(1)
    return kb.as_markup()
