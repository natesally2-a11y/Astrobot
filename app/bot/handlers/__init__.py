"""Aggregate routers from all handler modules."""

from aiogram import Router

from app.bot.handlers import (
    common,
    inline_mode,
    onboarding,
    payments,
    privacy,
    readings,
    subscription,
)


def get_router() -> Router:
    root = Router(name="root")
    root.include_router(common.router)
    root.include_router(onboarding.router)
    root.include_router(readings.router)
    root.include_router(subscription.router)
    root.include_router(payments.router)
    root.include_router(privacy.router)
    root.include_router(inline_mode.router)
    return root
