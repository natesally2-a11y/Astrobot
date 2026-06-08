"""A compact inline calendar for picking a birth date."""
from __future__ import annotations

import calendar
import datetime as dt

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

_MONTHS_RU = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
_WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


class CalendarCB(CallbackData, prefix="cal"):
    action: str  # "day", "prev-month", "next-month", "prev-year", "next-year", "ignore"
    year: int
    month: int
    day: int


def build_calendar(year: int | None = None, month: int | None = None) -> InlineKeyboardMarkup:
    today = dt.date.today()
    year = year or today.year
    month = month or today.month

    kb = InlineKeyboardBuilder()

    # Header: year navigation.
    kb.row(
        InlineKeyboardButton(text="«", callback_data=CalendarCB(action="prev-year", year=year, month=month, day=0).pack()),
        InlineKeyboardButton(text=str(year), callback_data=CalendarCB(action="ignore", year=year, month=month, day=0).pack()),
        InlineKeyboardButton(text="»", callback_data=CalendarCB(action="next-year", year=year, month=month, day=0).pack()),
    )
    # Month navigation.
    kb.row(
        InlineKeyboardButton(text="‹", callback_data=CalendarCB(action="prev-month", year=year, month=month, day=0).pack()),
        InlineKeyboardButton(text=_MONTHS_RU[month - 1], callback_data=CalendarCB(action="ignore", year=year, month=month, day=0).pack()),
        InlineKeyboardButton(text="›", callback_data=CalendarCB(action="next-month", year=year, month=month, day=0).pack()),
    )
    # Weekday headers.
    kb.row(*[
        InlineKeyboardButton(text=w, callback_data=CalendarCB(action="ignore", year=year, month=month, day=0).pack())
        for w in _WEEKDAYS_RU
    ])

    # Days grid.
    month_cal = calendar.monthcalendar(year, month)
    for week in month_cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data=CalendarCB(action="ignore", year=year, month=month, day=0).pack()))
            else:
                row.append(InlineKeyboardButton(text=str(day), callback_data=CalendarCB(action="day", year=year, month=month, day=day).pack()))
        kb.row(*row)

    return kb.as_markup()
