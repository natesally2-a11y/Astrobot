from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.config import settings


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Согласен', callback_data='gdpr:agree')],
            [InlineKeyboardButton(text='Политика конфиденциальности', url=f'{settings.app_base_url.rstrip("/")}/privacy')],
        ]
    )


def onboarding_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Начать создание карты', callback_data='onboarding:start')]])


def place_choices_keyboard(places: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for index, place in enumerate(places):
        rows.append([InlineKeyboardButton(text=place['name'][:64], callback_data=f'place:{index}')])
    rows.append([InlineKeyboardButton(text='Искать еще раз', callback_data='place:retry')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Открыть Mini App', web_app=WebAppInfo(url=f'{settings.webapp_url}?telegram_id={telegram_id}'))],
            [InlineKeyboardButton(text=f'Stellarium Pro ({settings.pro_plan_stars} ⭐)', callback_data='buy:pro')],
            [InlineKeyboardButton(text=f'Cosmic Oracle ({settings.oracle_plan_stars} ⭐)', callback_data='buy:oracle')],
        ]
    )
