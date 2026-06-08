from __future__ import annotations

import calendar
from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

MONTH_NAMES = {
    1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь',
    7: 'Июль', 8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
}


def build_calendar(year: int | None = None, month: int | None = None) -> InlineKeyboardMarkup:
    today = datetime.utcnow()
    year = year or today.year
    month = month or today.month
    cal = calendar.Calendar(firstweekday=0)
    rows = [[InlineKeyboardButton(text=f'{MONTH_NAMES[month]} {year}', callback_data='noop')]]
    rows.append([
        InlineKeyboardButton(text='Пн', callback_data='noop'),
        InlineKeyboardButton(text='Вт', callback_data='noop'),
        InlineKeyboardButton(text='Ср', callback_data='noop'),
        InlineKeyboardButton(text='Чт', callback_data='noop'),
        InlineKeyboardButton(text='Пт', callback_data='noop'),
        InlineKeyboardButton(text='Сб', callback_data='noop'),
        InlineKeyboardButton(text='Вс', callback_data='noop'),
    ])
    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=' ', callback_data='noop'))
            else:
                row.append(InlineKeyboardButton(text=str(day), callback_data=f'calendar:pick:{year}:{month}:{day}'))
        rows.append(row)
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    rows.append([
        InlineKeyboardButton(text='◀️', callback_data=f'calendar:nav:{prev_year}:{prev_month}'),
        InlineKeyboardButton(text='Сегодня', callback_data=f'calendar:pick:{today.year}:{today.month}:{today.day}'),
        InlineKeyboardButton(text='▶️', callback_data=f'calendar:nav:{next_year}:{next_month}'),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
