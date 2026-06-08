from __future__ import annotations

import calendar
from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

RU_WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def month_calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    month_name = f"{calendar.month_name[month]} {year}".title()
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=month_name, callback_data="ignore")],
        [InlineKeyboardButton(text=day, callback_data="ignore") for day in RU_WEEKDAYS],
    ]

    cal = calendar.Calendar(firstweekday=0)
    for week in cal.monthdayscalendar(year, month):
        row: list[InlineKeyboardButton] = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text="·", callback_data="ignore"))
            else:
                row.append(
                    InlineKeyboardButton(
                        text=str(day),
                        callback_data=f"birthdate:{year:04d}-{month:02d}-{day:02d}",
                    )
                )
        rows.append(row)

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    rows.append(
        [
            InlineKeyboardButton(text="◀️", callback_data=f"calendar:{prev_year}:{prev_month}"),
            InlineKeyboardButton(text="▶️", callback_data=f"calendar:{next_year}:{next_month}"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def starting_calendar() -> InlineKeyboardMarkup:
    today = date.today()
    return month_calendar_keyboard(today.year, today.month)


def hour_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for hour in range(24):
        row.append(InlineKeyboardButton(text=f"{hour:02d}", callback_data=f"hour:{hour:02d}"))
        if len(row) == 6:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Время неизвестно", callback_data="hour:unknown")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def minute_keyboard(selected_hour: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="00", callback_data=f"time:{selected_hour}:00"),
                InlineKeyboardButton(text="15", callback_data=f"time:{selected_hour}:15"),
                InlineKeyboardButton(text="30", callback_data=f"time:{selected_hour}:30"),
                InlineKeyboardButton(text="45", callback_data=f"time:{selected_hour}:45"),
            ],
            [InlineKeyboardButton(text="⬅️ Назад к часам", callback_data="time:back")],
        ]
    )

