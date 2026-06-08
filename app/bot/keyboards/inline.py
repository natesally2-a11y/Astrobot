from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать создание карты", callback_data="onboarding:start")],
            [InlineKeyboardButton(text="Политика конфиденциальности", callback_data="legal:privacy")],
        ]
    )


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Согласен", callback_data="gdpr:accept")],
            [InlineKeyboardButton(text="Политика конфиденциальности", callback_data="legal:privacy")],
        ]
    )


def city_keyboard(cities: list[dict[str, str]]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=city["label"][:64], callback_data=f"city:{idx}")]
        for idx, city in enumerate(cities[:5])
    ]
    rows.append([InlineKeyboardButton(text="Ввести город заново", callback_data="onboarding:place")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_keyboard(webapp_url: str | None = None) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Stellarium Pro — 50 Stars", callback_data="pay:pro")],
        [InlineKeyboardButton(text="Космический Оракул — 150 Stars", callback_data="pay:oracle")],
    ]
    if webapp_url:
        rows.append([InlineKeyboardButton(text="Открыть Mini App", web_app=WebAppInfo(url=webapp_url))])
    rows.append([InlineKeyboardButton(text="Экспорт данных", callback_data="data:export")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def app_keyboard(webapp_url: str | None) -> InlineKeyboardMarkup | None:
    if not webapp_url:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Открыть интерактивную карту", web_app=WebAppInfo(url=webapp_url))]]
    )
