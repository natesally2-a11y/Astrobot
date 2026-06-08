from app.bot.handlers.astrology import router as astrology_router
from app.bot.handlers.common import router as common_router
from app.bot.handlers.inline_mode import router as inline_router
from app.bot.handlers.onboarding import router as onboarding_router
from app.bot.handlers.payments import router as payments_router

ALL_ROUTERS = [
    onboarding_router,
    common_router,
    astrology_router,
    payments_router,
    inline_router,
]
