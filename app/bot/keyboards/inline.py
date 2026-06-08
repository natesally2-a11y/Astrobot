"""Inline keyboard builders for the bot."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import settings


def start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌟 Начать создание карты", callback_data="onboard_start"))
    builder.row(InlineKeyboardButton(text="ℹ️ Подробнее о боте", callback_data="about_bot"))
    return builder.as_markup()


def gdpr_consent_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Согласен", callback_data="gdpr_accept"),
        InlineKeyboardButton(text="📄 Политика конфиденциальности", callback_data="privacy_policy"),
    )
    return builder.as_markup()


def birth_date_year_keyboard(start_year: int = 1950, end_year: int = 2010) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    decades = range(start_year, end_year + 1, 10)
    for decade_start in decades:
        builder.row(
            InlineKeyboardButton(
                text=f"{decade_start}–{min(decade_start + 9, end_year)}",
                callback_data=f"decade_{decade_start}",
            )
        )
    return builder.as_markup()


def birth_date_year_detail_keyboard(decade_start: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    years = range(decade_start, min(decade_start + 10, 2011))
    row: list[InlineKeyboardButton] = []
    for y in years:
        row.append(InlineKeyboardButton(text=str(y), callback_data=f"year_{y}"))
        if len(row) == 5:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="onboard_start"))
    return builder.as_markup()


def birth_month_keyboard() -> InlineKeyboardMarkup:
    months = [
        "Январь", "Февраль", "Март", "Апрель",
        "Май", "Июнь", "Июль", "Август",
        "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
    ]
    builder = InlineKeyboardBuilder()
    row: list[InlineKeyboardButton] = []
    for i, m in enumerate(months, 1):
        row.append(InlineKeyboardButton(text=m, callback_data=f"month_{i}"))
        if len(row) == 3:
            builder.row(*row)
            row = []
    return builder.as_markup()


def birth_day_keyboard(month: int, year: int) -> InlineKeyboardMarkup:
    import calendar

    days_in_month = calendar.monthrange(year, month)[1]
    builder = InlineKeyboardBuilder()
    row: list[InlineKeyboardButton] = []
    for d in range(1, days_in_month + 1):
        row.append(InlineKeyboardButton(text=str(d), callback_data=f"day_{d}"))
        if len(row) == 7:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
    return builder.as_markup()


def birth_time_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    hours = [0, 3, 6, 9, 12, 15, 18, 21]
    row: list[InlineKeyboardButton] = []
    for h in hours:
        row.append(InlineKeyboardButton(text=f"{h:02d}:00", callback_data=f"hour_{h}"))
        if len(row) == 4:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
    builder.row(InlineKeyboardButton(text="⏰ Ввести точное время", callback_data="time_exact"))
    builder.row(InlineKeyboardButton(text="❓ Не знаю время", callback_data="time_unknown"))
    return builder.as_markup()


def birth_time_minutes_keyboard(hour: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for h_offset in range(3):
        actual_hour = hour + h_offset
        if actual_hour > 23:
            break
        row: list[InlineKeyboardButton] = []
        for m in [0, 15, 30, 45]:
            row.append(
                InlineKeyboardButton(
                    text=f"{actual_hour:02d}:{m:02d}",
                    callback_data=f"time_{actual_hour}_{m}",
                )
            )
        builder.row(*row)
    builder.row(InlineKeyboardButton(text="◀️ Другой час", callback_data="onboard_time"))
    return builder.as_markup()


def subscription_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"⭐ Stellarium Pro — {settings.pro_stars_price} Stars/мес",
            callback_data="subscribe_pro",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"🔮 Космический Оракул — {settings.oracle_stars_price} Stars/мес",
            callback_data="subscribe_oracle",
        )
    )
    builder.row(InlineKeyboardButton(text="📋 Сравнить планы", callback_data="compare_plans"))
    return builder.as_markup()


def settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile"))
    builder.row(InlineKeyboardButton(text="⭐ Подписка", callback_data="manage_subscription"))
    builder.row(InlineKeyboardButton(text="🔄 Изменить данные рождения", callback_data="edit_birth_data"))
    builder.row(InlineKeyboardButton(text="📊 Мои данные (GDPR)", callback_data="gdpr_my_data"))
    builder.row(InlineKeyboardButton(text="🗑 Удалить аккаунт", callback_data="gdpr_delete"))
    return builder.as_markup()


def confirm_delete_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⚠️ Да, удалить всё", callback_data="gdpr_delete_confirm"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="settings_back"),
    )
    return builder.as_markup()


def compatibility_input_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Ввести данные партнёра", callback_data="compat_start"))
    return builder.as_markup()


def webapp_keyboard() -> InlineKeyboardMarkup | None:
    if not settings.webapp_url:
        return None
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🌌 Открыть Stellarium",
            web_app=WebAppInfo(url=settings.webapp_url),
        )
    )
    return builder.as_markup()


def back_to_settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Назад в настройки", callback_data="settings_back"))
    return builder.as_markup()
