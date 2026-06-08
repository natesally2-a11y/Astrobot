from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    LabeledPrice,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from app.config import get_settings

settings = get_settings()


def gdpr_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Согласен", callback_data="gdpr_agree")],
            [InlineKeyboardButton(text="Политика конфиденциальности", callback_data="show_privacy")],
        ]
    )


def place_candidates_keyboard(candidates: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for idx, item in enumerate(candidates):
        title = item["display_name"][:72]
        rows.append([InlineKeyboardButton(text=title, callback_data=f"place_{idx}")])
    rows.append([InlineKeyboardButton(text="Ввести заново", callback_data="place_retry")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_menu_keyboard(webapp_url: str | None) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="/today"), KeyboardButton(text="/chart")],
        [KeyboardButton(text="/ask"), KeyboardButton(text="/settings")],
    ]
    if webapp_url:
        buttons.append([KeyboardButton(text="Открыть Mini App", web_app=WebAppInfo(url=webapp_url))])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Stellarium Pro — 50 Stars", callback_data="buy_pro")],
            [InlineKeyboardButton(text="Космический Оракул — 150 Stars", callback_data="buy_oracle")],
        ]
    )


def stars_invoice_price(amount: int, label: str) -> list[LabeledPrice]:
    return [LabeledPrice(label=label, amount=amount)]
