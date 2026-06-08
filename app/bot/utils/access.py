"""Subscription and rate-limit checks shared by handlers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.database.models import SubscriptionTier, User


def has_active_premium(user: User) -> bool:
    if user.subscription_type == SubscriptionTier.FREE:
        return False
    if user.subscription_expires_at is None:
        return False
    expires = user.subscription_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return expires > datetime.now(timezone.utc)


def is_oracle(user: User) -> bool:
    return user.subscription_type == SubscriptionTier.ORACLE and has_active_premium(user)


def plan_label(user: User) -> str:
    if not has_active_premium(user):
        return "Free"
    if user.subscription_type == SubscriptionTier.ORACLE:
        return "Космический Оракул"
    return "Pro"


def format_expires(user: User) -> Optional[str]:
    if user.subscription_expires_at is None:
        return None
    return user.subscription_expires_at.strftime("%d.%m.%Y")


def remaining_free_questions(asked_today: int, limit: int) -> int:
    return max(0, limit - asked_today)
