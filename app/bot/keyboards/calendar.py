"""Инлайн-календарь и выбор времени для сбора данных рождения.

Все билдеры принимают `prefix`, чтобы один и тот же UI можно было
использовать в разных диалогах (онбординг и совместимость) без конфликта
callback-данных.
"""
from __future__ import annotations

import calendar
import datetime as dt

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

MONTHS_RU = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

CAL = "cal"
TIME = "time"
CITY = "city"


def build_calendar(year: int, month: int, prefix: str = CAL) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    rows.append([
        InlineKeyboardButton(text="«", callback_data=f"{prefix}:nav:{year-1}:{month}"),
        InlineKeyboardButton(
            text=f"{MONTHS_RU[month-1]} {year}", callback_data=f"{prefix}:ignore"
        ),
        InlineKeyboardButton(text="»", callback_data=f"{prefix}:nav:{year+1}:{month}"),
    ])

    prev_m = month - 1 or 12
    prev_y = year - 1 if month == 1 else year
    next_m = month + 1 if month < 12 else 1
    next_y = year + 1 if month == 12 else year
    rows.append([
        InlineKeyboardButton(text="◀ мес", callback_data=f"{prefix}:nav:{prev_y}:{prev_m}"),
        InlineKeyboardButton(text="мес ▶", callback_data=f"{prefix}:nav:{next_y}:{next_m}"),
    ])

    rows.append([
        InlineKeyboardButton(text=d, callback_data=f"{prefix}:ignore") for d in WEEKDAYS_RU
    ])

    cal = calendar.Calendar(firstweekday=0)
    for week in cal.monthdayscalendar(year, month):
        row: list[InlineKeyboardButton] = []
        for day in week:
            if day == 0:
                row.append(
                    InlineKeyboardButton(text=" ", callback_data=f"{prefix}:ignore")
                )
            else:
                row.append(
                    InlineKeyboardButton(
                        text=str(day),
                        callback_data=f"{prefix}:day:{year}:{month}:{day}",
                    )
                )
        rows.append(row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def default_calendar(prefix: str = CAL) -> InlineKeyboardMarkup:
    today = dt.date.today()
    return build_calendar(today.year - 25, today.month, prefix=prefix)


def build_hours(prefix: str = TIME) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for start in range(0, 24, 6):
        row = [
            InlineKeyboardButton(text=f"{h:02d}", callback_data=f"{prefix}:h:{h}")
            for h in range(start, start + 6)
        ]
        rows.append(row)
    rows.append([
        InlineKeyboardButton(text="🤷 Не знаю время", callback_data=f"{prefix}:unknown")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_minutes(hour: int, prefix: str = TIME) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    minutes = list(range(0, 60, 5))
    for i in range(0, len(minutes), 6):
        chunk = minutes[i : i + 6]
        row = [
            InlineKeyboardButton(
                text=f"{hour:02d}:{m:02d}", callback_data=f"{prefix}:m:{hour}:{m}"
            )
            for m in chunk
        ]
        rows.append(row)
    rows.append([
        InlineKeyboardButton(text="◀ Назад к часам", callback_data=f"{prefix}:back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_cities(results, prefix: str = CITY) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for idx, r in enumerate(results):
        label = r.display_name
        if len(label) > 60:
            label = label[:57] + "…"
        rows.append([
            InlineKeyboardButton(text=label, callback_data=f"{prefix}:{idx}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
