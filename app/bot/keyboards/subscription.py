from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def settings_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Stellarium Pro — 50 Stars", callback_data="buy:pro")],
            [InlineKeyboardButton(text="🌌 Космический Оракул — 150 Stars", callback_data="buy:oracle")],
            [InlineKeyboardButton(text="Открыть Mini App", web_app=WebAppInfo(url=webapp_url))],
        ]
    )

