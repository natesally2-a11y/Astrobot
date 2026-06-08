from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData


class MonthCD(CallbackData, prefix="month"):
    month: int


class DayCD(CallbackData, prefix="day"):
    day: int
    month: int


class YearCD(CallbackData, prefix="year"):
    year: int


class TimeCD(CallbackData, prefix="time"):
    value: str


class SubscriptionCD(CallbackData, prefix="sub"):
    plan: str


MONTH_NAMES = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]


def get_gdpr_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Согласен", callback_data="gdpr:agree"),
        InlineKeyboardButton(text="📋 Политика конфиденциальности", callback_data="gdpr:policy"),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_year_keyboard(current_year: int = 2025) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    years = list(range(current_year - 80, current_year - 4))
    years.reverse()
    for year in years[:40]:
        builder.add(InlineKeyboardButton(
            text=str(year),
            callback_data=YearCD(year=year).pack(),
        ))
    builder.adjust(5)
    return builder.as_markup()


def get_month_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, name in enumerate(MONTH_NAMES, 1):
        builder.add(InlineKeyboardButton(
            text=name,
            callback_data=MonthCD(month=i).pack(),
        ))
    builder.adjust(3)
    return builder.as_markup()


def get_day_keyboard(month: int) -> InlineKeyboardMarkup:
    import calendar
    days_in_month = calendar.monthrange(2000, month)[1]
    builder = InlineKeyboardBuilder()
    for day in range(1, days_in_month + 1):
        builder.add(InlineKeyboardButton(
            text=str(day),
            callback_data=DayCD(day=day, month=month).pack(),
        ))
    builder.adjust(7)
    return builder.as_markup()


def get_birth_time_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    time_options = [
        ("00:00", "00:00"), ("02:00", "02:00"), ("04:00", "04:00"),
        ("06:00", "06:00"), ("08:00", "08:00"), ("10:00", "10:00"),
        ("12:00", "12:00"), ("14:00", "14:00"), ("16:00", "16:00"),
        ("18:00", "18:00"), ("20:00", "20:00"), ("22:00", "22:00"),
    ]
    for label, value in time_options:
        builder.add(InlineKeyboardButton(
            text=label,
            callback_data=TimeCD(value=value).pack(),
        ))
    builder.add(InlineKeyboardButton(
        text="❓ Не знаю время",
        callback_data=TimeCD(value="unknown").pack(),
    ))
    builder.adjust(4)
    return builder.as_markup()


def get_main_menu_keyboard(has_birth_data: bool = False, is_pro: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if has_birth_data:
        builder.add(
            InlineKeyboardButton(text="🗺 Моя карта", callback_data="menu:chart"),
            InlineKeyboardButton(text="☀️ Прогноз на сегодня", callback_data="menu:today"),
        )
        if is_pro:
            builder.add(
                InlineKeyboardButton(text="📅 Прогноз на неделю", callback_data="menu:week"),
                InlineKeyboardButton(text="💫 Транзиты", callback_data="menu:transit"),
            )
        builder.add(
            InlineKeyboardButton(text="💕 Совместимость", callback_data="menu:compatibility"),
            InlineKeyboardButton(text="🔮 Задать вопрос", callback_data="menu:ask"),
        )

    if not is_pro:
        builder.add(
            InlineKeyboardButton(text="⭐ Upgrade — Pro 50⭐", callback_data="menu:upgrade_pro"),
            InlineKeyboardButton(text="🔮 Oracle 150⭐", callback_data="menu:upgrade_oracle"),
        )

    builder.add(InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu:settings"))
    builder.adjust(2)
    return builder.as_markup()


def get_subscription_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="⭐ Stellarium Pro — 50 Stars/мес",
            callback_data=SubscriptionCD(plan="pro").pack(),
        ),
        InlineKeyboardButton(
            text="🔮 Космический Оракул — 150 Stars/мес",
            callback_data=SubscriptionCD(plan="oracle").pack(),
        ),
        InlineKeyboardButton(text="❌ Отмена", callback_data="sub:cancel"),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_settings_keyboard(is_pro: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✏️ Изменить данные рождения", callback_data="settings:edit_birth"),
        InlineKeyboardButton(text="📋 Мои данные", callback_data="settings:my_data"),
        InlineKeyboardButton(text="🔒 Политика конфиденциальности", callback_data="settings:privacy"),
        InlineKeyboardButton(text="📤 Экспорт данных", callback_data="settings:export"),
        InlineKeyboardButton(text="🗑 Удалить аккаунт", callback_data="settings:delete"),
    )
    if not is_pro:
        builder.add(
            InlineKeyboardButton(text="⭐ Оформить подписку", callback_data="settings:subscribe"),
        )
    builder.adjust(1)
    return builder.as_markup()


def get_confirm_delete_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="⚠️ Да, удалить все данные", callback_data="confirm:delete"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="confirm:cancel"),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_back_keyboard(callback_data: str = "menu:main") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data))
    return builder.as_markup()


def get_webapp_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    from aiogram.types import WebAppInfo
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="🌐 Открыть мини-приложение",
            web_app=WebAppInfo(url=f"https://t.me/{bot_username}/app"),
        )
    )
    return builder.as_markup()
