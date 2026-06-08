from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.config import get_settings

DISCLAIMER = (
    "⚠️ Важно: Астрологические прогнозы носят исключительно развлекательный характер "
    "и не являются руководством к действию.\n\n"
    "Не используйте астрологию для принятия важных жизненных, медицинских или финансовых решений. "
    "При серьёзных проблемах обращайтесь к квалифицированным специалистам.\n\n"
    "Stellarium AI создан для саморазвития и развлечения."
)

GDPR_TEXT = """📋 Согласие на обработку персональных данных

Для создания персональной натальной карты нам необходимы:
• Дата, время и место рождения
• Имя для персонализации

Мы обрабатываем эти данные для:
✅ Астрологических расчётов
✅ Персонализированных прогнозов
✅ Работы подписки

Мы НЕ передаём данные третьим лицам.
Вы можете удалить все данные командой /delete_data

Согласием с условиями обработки данных в соответствии с ФЗ-152 «О персональных данных» и GDPR нажмите кнопку «Согласен»."""


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌟 Начать создание карты", callback_data="start_registration")],
        ]
    )


def main_menu_keyboard() -> InlineKeyboardMarkup:
    settings = get_settings()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Моя карта", callback_data="cmd_chart")],
            [
                InlineKeyboardButton(text="☀️ Сегодня", callback_data="cmd_today"),
                InlineKeyboardButton(text="📅 Неделя", callback_data="cmd_week"),
            ],
            [
                InlineKeyboardButton(text="💕 Совместимость", callback_data="cmd_compatibility"),
                InlineKeyboardButton(text="🔮 Спросить", callback_data="cmd_ask"),
            ],
            [
                InlineKeyboardButton(text="🌙 Транзиты", callback_data="cmd_transit"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="cmd_settings"),
            ],
            [InlineKeyboardButton(text="📱 Открыть приложение", web_app=WebAppInfo(url=settings.webapp_url))],
        ]
    )


def gdpr_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен", callback_data="gdpr_accept")],
            [InlineKeyboardButton(text="📄 Политика конфиденциальности", callback_data="privacy_policy")],
        ]
    )


def subscription_keyboard() -> InlineKeyboardMarkup:
    settings = get_settings()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"⭐ Stellarium Pro — {settings.pro_stars} Stars/мес",
                callback_data="subscribe_pro",
            )],
            [InlineKeyboardButton(
                text=f"🌌 Космический Оракул — {settings.oracle_stars} Stars/мес",
                callback_data="subscribe_oracle",
            )],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="cmd_settings")],
        ]
    )


def settings_keyboard() -> InlineKeyboardMarkup:
    settings = get_settings()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 Подписка", callback_data="show_subscription")],
            [InlineKeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=settings.webapp_url))],
            [InlineKeyboardButton(text="📋 Мои данные", callback_data="my_data")],
            [InlineKeyboardButton(text="📤 Экспорт данных", callback_data="export_data")],
            [InlineKeyboardButton(text="🗑 Удалить данные", callback_data="delete_data_confirm")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="back_to_menu")],
        ]
    )


def year_keyboard(start_year: int = 1940, end_year: int = 2015) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for year in range(end_year, start_year - 1, -1):
        row.append(InlineKeyboardButton(text=str(year), callback_data=f"year_{year}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_registration")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def month_keyboard(year: int) -> InlineKeyboardMarkup:
    months = [
        ("Янв", 1), ("Фев", 2), ("Мар", 3), ("Апр", 4),
        ("Май", 5), ("Июн", 6), ("Июл", 7), ("Авг", 8),
        ("Сен", 9), ("Окт", 10), ("Ноя", 11), ("Дек", 12),
    ]
    rows = []
    row = []
    for name, num in months:
        row.append(InlineKeyboardButton(text=name, callback_data=f"month_{year}_{num}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_year")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def day_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    import calendar
    days_in_month = calendar.monthrange(year, month)[1]
    rows = []
    row = []
    for day in range(1, days_in_month + 1):
        row.append(InlineKeyboardButton(text=str(day), callback_data=f"day_{year}_{month}_{day}"))
        if len(row) == 7:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"year_{year}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def hour_keyboard() -> InlineKeyboardMarkup:
    rows = []
    row = []
    for hour in range(24):
        row.append(InlineKeyboardButton(text=f"{hour:02d}", callback_data=f"hour_{hour}"))
        if len(row) == 6:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([
        InlineKeyboardButton(text="❓ Не знаю", callback_data="hour_unknown"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_date"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def minute_keyboard(hour: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="00", callback_data=f"time_{hour}_0"),
            InlineKeyboardButton(text="15", callback_data=f"time_{hour}_15"),
            InlineKeyboardButton(text="30", callback_data=f"time_{hour}_30"),
            InlineKeyboardButton(text="45", callback_data=f"time_{hour}_45"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_hour")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def city_keyboard(cities: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for i, city in enumerate(cities):
        rows.append([
            InlineKeyboardButton(
                text=city["short_name"][:60],
                callback_data=f"city_{i}",
            )
        ])
    rows.append([InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_registration")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить всё", callback_data="delete_data_yes"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cmd_settings"),
            ],
        ]
    )
