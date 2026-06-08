"""All bot routers, aggregated."""
from aiogram import Router

from app.bot.handlers import (
    common,
    onboarding,
    chart,
    forecasts,
    compatibility,
    ask,
    subscriptions,
    gdpr,
    inline_mode,
    payments,
    menu,
)


def get_root_router() -> Router:
    """Compose all routers in a deterministic order."""
    root = Router(name="root")
    root.include_routers(
        common.router,
        gdpr.router,
        onboarding.router,
        chart.router,
        forecasts.router,
        compatibility.router,
        ask.router,
        subscriptions.router,
        payments.router,
        inline_mode.router,
        menu.router,  # menu callbacks should be last to act as a catch-all
    )
    return root
