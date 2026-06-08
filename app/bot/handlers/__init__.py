from aiogram import Router

from app.bot.handlers.ask import router as ask_router
from app.bot.handlers.chart import router as chart_router
from app.bot.handlers.compatibility import router as compatibility_router
from app.bot.handlers.gdpr import router as gdpr_router
from app.bot.handlers.inline import router as inline_router
from app.bot.handlers.payments import router as payments_router
from app.bot.handlers.registration import router as registration_router
from app.bot.handlers.settings import router as settings_router
from app.bot.handlers.start import router as start_router
from app.bot.handlers.today import router as today_router
from app.bot.handlers.transit import router as transit_router


def setup_routers() -> Router:
    router = Router()
    router.include_router(start_router)
    router.include_router(registration_router)
    router.include_router(chart_router)
    router.include_router(today_router)
    router.include_router(compatibility_router)
    router.include_router(ask_router)
    router.include_router(transit_router)
    router.include_router(settings_router)
    router.include_router(gdpr_router)
    router.include_router(payments_router)
    router.include_router(inline_router)
    return router
