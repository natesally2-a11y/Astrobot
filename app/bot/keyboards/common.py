from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать создание карты", callback_data="onboarding:start")],
            [InlineKeyboardButton(text="Политика конфиденциальности", callback_data="privacy:show")],
        ]
    )


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Согласен", callback_data="gdpr:agree")],
            [InlineKeyboardButton(text="Политика конфиденциальности", callback_data="privacy:show")],
        ]
    )


def settings_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть Mini App", web_app=WebAppInfo(url=webapp_url))],
            [InlineKeyboardButton(text="Stellarium Pro — 50 Stars", callback_data="subscribe:pro")],
            [InlineKeyboardButton(text="Космический Оракул — 150 Stars", callback_data="subscribe:oracle")],
            [InlineKeyboardButton(text="Экспорт данных", callback_data="data:export")],
        ]
    )


def upgrade_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Stellarium Pro — 50 Stars", callback_data="subscribe:pro")],
            [InlineKeyboardButton(text="Космический Оракул — 150 Stars", callback_data="subscribe:oracle")],
        ]
    )


def delete_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да, удалить все данные", callback_data="data:delete_confirm")],
            [InlineKeyboardButton(text="Отмена", callback_data="data:delete_cancel")],
        ]
    )
