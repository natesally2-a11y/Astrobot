"""Общие клавиатуры: согласие, меню, подписки, WebApp."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import settings
from app.plans import ORACLE, PRO, get_plan


def start_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✨ Начать создание карты", callback_data="onboard:start")
    return kb.as_markup()


def consent_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Согласен", callback_data="gdpr:accept")
    kb.button(text="📄 Политика конфиденциальности", callback_data="gdpr:policy")
    kb.adjust(1)
    return kb.as_markup()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🪐 Натальная карта", callback_data="menu:chart")
    kb.button(text="🌤 Прогноз на сегодня", callback_data="menu:today")
    kb.button(text="💞 Совместимость", callback_data="menu:compatibility")
    kb.button(text="🔮 Задать вопрос", callback_data="menu:ask")
    kb.button(text="⚙️ Настройки и подписка", callback_data="menu:settings")
    if settings.webhook_base_url:
        kb.button(
            text="📱 Открыть приложение",
            web_app=WebAppInfo(url=settings.webapp_url),
        )
    kb.adjust(1)
    return kb.as_markup()


def open_app_keyboard() -> InlineKeyboardMarkup | None:
    if not settings.webhook_base_url:
        return None
    kb = InlineKeyboardBuilder()
    kb.button(text="📱 Открыть приложение", web_app=WebAppInfo(url=settings.webapp_url))
    return kb.as_markup()


def subscription_keyboard(current_plan: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    pro = get_plan(PRO)
    oracle = get_plan(ORACLE)
    kb.button(
        text=f"⭐ {pro.title} — {pro.price_rub}₽ ({pro.stars}★)",
        callback_data="buy:pro",
    )
    kb.button(
        text=f"🌌 {oracle.title} — {oracle.price_rub}₽ ({oracle.stars}★)",
        callback_data="buy:oracle",
    )
    kb.button(text="🎁 Реферальная программа", callback_data="menu:referral")
    kb.adjust(1)
    return kb.as_markup()


def delete_confirm_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Да, удалить всё", callback_data="gdpr:delete_confirm")
    kb.button(text="↩️ Отмена", callback_data="gdpr:delete_cancel")
    kb.adjust(1)
    return kb.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="↩️ Меню", callback_data="menu:main")
    return kb.as_markup()
