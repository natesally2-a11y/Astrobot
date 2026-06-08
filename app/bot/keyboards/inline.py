"""Inline keyboard builders."""

from __future__ import annotations

import calendar as cal_mod
from datetime import date
from typing import Optional

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)

from app.config import settings


def start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌟 Начать создание карты", callback_data="onboard:start")],
            [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="show:help")],
        ]
    )


def gdpr_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен", callback_data="gdpr:accept")],
            [
                InlineKeyboardButton(
                    text="🔐 Политика конфиденциальности",
                    callback_data="show:privacy",
                )
            ],
        ]
    )


def main_menu_kb(has_chart: bool) -> InlineKeyboardMarkup:
    rows = []
    if has_chart:
        rows.append([
            InlineKeyboardButton(text="🪐 Натальная карта", callback_data="menu:chart"),
            InlineKeyboardButton(text="🌞 Сегодня", callback_data="menu:today"),
        ])
        rows.append([
            InlineKeyboardButton(text="🌙 Неделя (Pro)", callback_data="menu:week"),
            InlineKeyboardButton(text="💞 Совместимость", callback_data="menu:compat"),
        ])
        rows.append([
            InlineKeyboardButton(text="❓ Задать вопрос", callback_data="menu:ask"),
            InlineKeyboardButton(text="🌌 Транзиты (Pro)", callback_data="menu:transit"),
        ])
    else:
        rows.append([
            InlineKeyboardButton(
                text="🌟 Создать натальную карту",
                callback_data="onboard:start",
            )
        ])
    rows.append([
        InlineKeyboardButton(text="💳 Подписка", callback_data="menu:subscription"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu:settings"),
    ])
    if settings.webapp_url:
        rows.append([
            InlineKeyboardButton(
                text="🌌 Открыть мини-приложение",
                web_app=WebAppInfo(url=settings.webapp_url),
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def calendar_kb(year: int, month: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    month_name = date(year, month, 1).strftime("%B %Y")
    rows.append([
        InlineKeyboardButton(text="«", callback_data=f"cal:nav:{year}:{month}:-1"),
        InlineKeyboardButton(text=month_name, callback_data="cal:noop"),
        InlineKeyboardButton(text="»", callback_data=f"cal:nav:{year}:{month}:1"),
    ])
    rows.append([
        InlineKeyboardButton(text=d, callback_data="cal:noop")
        for d in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    ])
    month_cal = cal_mod.Calendar(firstweekday=0).monthdayscalendar(year, month)
    for week in month_cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="cal:noop"))
            else:
                row.append(
                    InlineKeyboardButton(
                        text=str(day),
                        callback_data=f"cal:pick:{year}:{month}:{day}",
                    )
                )
        rows.append(row)
    rows.append([
        InlineKeyboardButton(text="− 10 лет", callback_data=f"cal:year:{year - 10}:{month}"),
        InlineKeyboardButton(text="+ 10 лет", callback_data=f"cal:year:{year + 10}:{month}"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def hours_kb() -> InlineKeyboardMarkup:
    rows = []
    for start in range(0, 24, 6):
        rows.append([
            InlineKeyboardButton(text=f"{h:02d}", callback_data=f"time:h:{h}")
            for h in range(start, start + 6)
        ])
    rows.append([
        InlineKeyboardButton(text="🤷 Не знаю время", callback_data="time:unknown"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def minutes_kb() -> InlineKeyboardMarkup:
    rows = []
    quarters = [0, 15, 30, 45]
    rows.append([
        InlineKeyboardButton(text=f"{m:02d}", callback_data=f"time:m:{m}")
        for m in quarters
    ])
    five_step = list(range(0, 60, 5))
    for i in range(0, len(five_step), 6):
        rows.append([
            InlineKeyboardButton(text=f"{m:02d}", callback_data=f"time:m:{m}")
            for m in five_step[i : i + 6]
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_geo_kb(query: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, это оно", callback_data="geo:ok"),
                InlineKeyboardButton(text="✏️ Ввести заново", callback_data="geo:retry"),
            ]
        ]
    )


def subscription_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"⭐ Pro — {settings.pro_price_stars} Stars",
                callback_data="buy:pro",
            )],
            [InlineKeyboardButton(
                text=f"🌌 Космический Оракул — {settings.oracle_price_stars} Stars",
                callback_data="buy:oracle",
            )],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="menu:back")],
        ]
    )


def settings_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="✏️ Пересоздать карту", callback_data="onboard:restart")],
        [InlineKeyboardButton(text="📥 Экспортировать данные", callback_data="data:export")],
        [InlineKeyboardButton(text="🗑 Удалить аккаунт", callback_data="data:delete")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu:back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить", callback_data="data:delete:yes"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="menu:back"),
            ]
        ]
    )


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="menu:back")]
        ]
    )


def open_webapp_kb() -> Optional[InlineKeyboardMarkup]:
    if not settings.webapp_url:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="🌌 Открыть карту в приложении",
                web_app=WebAppInfo(url=settings.webapp_url),
            )
        ]]
    )
