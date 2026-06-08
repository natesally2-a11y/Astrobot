from __future__ import annotations

import calendar
from datetime import datetime

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Начать создание карты", callback_data="onboarding:start")
    builder.button(text="Политика конфиденциальности", callback_data="legal:privacy")
    builder.adjust(1)
    return builder.as_markup()


def consent_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Согласен", callback_data="consent:agree")
    builder.button(text="Политика конфиденциальности", callback_data="legal:privacy")
    builder.adjust(1)
    return builder.as_markup()


def year_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    current_year = datetime.utcnow().year
    years = list(range(current_year - 90, current_year - 5))
    page_size = 12
    start = max(0, min(page * page_size, len(years) - page_size))
    subset = years[start : start + page_size]

    builder = InlineKeyboardBuilder()
    for year in subset:
        builder.button(text=str(year), callback_data=f"date:year:{year}")
    builder.adjust(3)
    if start > 0:
        builder.button(text="← Раньше", callback_data=f"date:page:{page - 1}")
    if start + page_size < len(years):
        builder.button(text="Позже →", callback_data=f"date:page:{page + 1}")
    builder.button(text="Отмена", callback_data="onboarding:cancel")
    builder.adjust(2, 1)
    return builder.as_markup()


def month_keyboard(year: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for month in range(1, 13):
        builder.button(
            text=f"{month:02d}",
            callback_data=f"date:month:{year}:{month}",
        )
    builder.adjust(3)
    builder.button(text="← Назад", callback_data="date:back:year")
    return builder.as_markup()


def day_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    _, days_in_month = calendar.monthrange(year, month)
    for day in range(1, days_in_month + 1):
        builder.button(
            text=f"{day:02d}",
            callback_data=f"date:day:{year}:{month}:{day}",
        )
    builder.adjust(7)
    builder.button(text="← Назад", callback_data=f"date:back:month:{year}")
    return builder.as_markup()


def hour_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for hour in range(24):
        builder.button(text=f"{hour:02d}", callback_data=f"time:hour:{hour}")
    builder.adjust(4)
    builder.button(text="Время примерно / не знаю", callback_data="time:approx")
    builder.button(text="Отмена", callback_data="onboarding:cancel")
    builder.adjust(1)
    return builder.as_markup()


def minute_keyboard(hour: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for minute in range(0, 60, 5):
        builder.button(
            text=f"{minute:02d}",
            callback_data=f"time:minute:{hour}:{minute}",
        )
    builder.adjust(4)
    builder.button(text="← Назад", callback_data="time:back:hour")
    return builder.as_markup()


def location_results_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Попробовать другой город", callback_data="place:retry")
    return builder.as_markup()
