from __future__ import annotations

from datetime import datetime


def is_premium(subscription_type: str, subscription_expires_at: datetime | None) -> bool:
    if subscription_type not in {"pro", "oracle"}:
        return False
    return bool(subscription_expires_at and subscription_expires_at > datetime.utcnow())

