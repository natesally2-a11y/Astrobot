"""Reusable inline keyboards."""
from __future__ import annotations

from typing import Iterable

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.astrology.geocoding import GeoResult
from app.config import get_settings
from app.payments import PLANS


def consent_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Согласен", callback_data="gdpr:accept")
    kb.button(text="📄 Политика конфиденциальности", callback_data="gdpr:policy")
    kb.adjust(1)
    return kb.as_markup()


def main_menu_kb() -> InlineKeyboardMarkup:
    settings = get_settings()
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🌟 Натальная карта", callback_data="menu:chart"),
        InlineKeyboardButton(text="📅 На сегодня", callback_data="menu:today"),
    )
    kb.row(
        InlineKeyboardButton(text="💞 Совместимость", callback_data="menu:compat"),
        InlineKeyboardButton(text="🪐 Транзиты", callback_data="menu:transit"),
    )
    kb.row(
        InlineKeyboardButton(text="❓ Задать вопрос", callback_data="menu:ask"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu:settings"),
    )
    if settings.webapp_public_url and settings.webapp_public_url.startswith("https"):
        kb.row(
            InlineKeyboardButton(
                text="🔭 Открыть мини-приложение",
                web_app=WebAppInfo(url=settings.mini_app_url),
            )
        )
    return kb.as_markup()


def skip_time_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🤷 Не знаю точного времени", callback_data="birth:no_time")
    return kb.as_markup()


def place_choice_kb(results: Iterable[GeoResult]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for idx, _ in enumerate(results):
        kb.button(text=f"{idx + 1}", callback_data=f"place:{idx}")
    kb.button(text="🔄 Поискать ещё", callback_data="place:retry")
    kb.adjust(5, 1)
    return kb.as_markup()


def subscription_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for plan in PLANS.values():
        kb.button(
            text=f"⭐ {plan.title.split(' — ')[0]} — {plan.stars}★ / {plan.price_rub}₽",
            callback_data=f"sub:buy:{plan.code}",
        )
    kb.button(text="◀️ Назад", callback_data="menu:back")
    kb.adjust(1)
    return kb.as_markup()


def settings_kb(*, is_premium: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Изменить данные рождения", callback_data="settings:edit")
    kb.button(
        text=("💳 Управление подпиской" if is_premium else "⭐ Оформить подписку"),
        callback_data="settings:subscribe",
    )
    kb.button(text="🤝 Реферальная программа", callback_data="settings:ref")
    kb.button(text="🛡️ Конфиденциальность", callback_data="settings:privacy")
    kb.button(text="◀️ Меню", callback_data="menu:back")
    kb.adjust(1)
    return kb.as_markup()
