"""Access-control helpers (premium checks, admin, referral links)."""
from __future__ import annotations

from app.bot.plans import PREMIUM_PLANS
from app.config import settings
from app.database.models import PLAN_ORACLE, User


def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_ids


def has_premium(user: User) -> bool:
    """True if the user has any active paid plan (or is an admin)."""
    if is_admin(user.telegram_id):
        return True
    return user.subscription_type in PREMIUM_PLANS


def has_oracle(user: User) -> bool:
    if is_admin(user.telegram_id):
        return True
    return user.subscription_type == PLAN_ORACLE


def referral_link(telegram_id: int) -> str:
    return f"https://t.me/{settings.bot_username}?start=ref_{telegram_id}"
