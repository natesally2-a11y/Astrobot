"""Регистрация всех роутеров бота."""
from __future__ import annotations

from aiogram import Dispatcher

from app.bot.handlers import (
    ask,
    chart,
    compatibility,
    forecasts,
    gdpr,
    help as help_handler,
    inline,
    menu,
    payments,
    settings as settings_handler,
    start,
)


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(gdpr.router)
    dp.include_router(chart.router)
    dp.include_router(forecasts.router)
    dp.include_router(compatibility.router)
    dp.include_router(ask.router)
    dp.include_router(settings_handler.router)
    dp.include_router(payments.router)
    dp.include_router(help_handler.router)
    dp.include_router(inline.router)
    dp.include_router(menu.router)
