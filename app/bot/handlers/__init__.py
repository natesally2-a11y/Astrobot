"""Handler routers registration."""
from __future__ import annotations

from aiogram import Dispatcher

from app.bot.handlers import (
    ask,
    chart,
    compatibility,
    forecast,
    gdpr,
    help as help_handler,
    inline,
    menu,
    payments,
    settings as settings_handler,
    start,
)


def register_handlers(dp: Dispatcher) -> None:
    """Include all routers. Order matters: specific before catch-all (ask)."""
    dp.include_router(start.router)
    dp.include_router(chart.router)
    dp.include_router(forecast.router)
    dp.include_router(compatibility.router)
    dp.include_router(settings_handler.router)
    dp.include_router(payments.router)
    dp.include_router(gdpr.router)
    dp.include_router(help_handler.router)
    dp.include_router(inline.router)
    dp.include_router(menu.router)
    # ask must be last — it contains a catch-all text handler.
    dp.include_router(ask.router)
