from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def onboarding_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Начать создание карты", callback_data="onboarding:start")]]
    )


def gdpr_consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Согласен", callback_data="gdpr:agree"),
                InlineKeyboardButton(text="Политика конфиденциальности", callback_data="gdpr:privacy"),
            ]
        ]
    )

