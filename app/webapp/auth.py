"""Validation of Telegram WebApp ``initData``.

Implements the verification algorithm described in the Telegram docs:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Optional
from urllib.parse import parse_qsl

from app.config import settings


def validate_init_data(init_data: str, max_age_seconds: int = 86400) -> Optional[dict]:
    """Validate ``initData`` and return the parsed payload (incl. ``user``).

    Returns ``None`` when the signature is invalid or the data is too old.
    """
    if not init_data or not settings.bot_token:
        return None

    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={parsed[k]}" for k in sorted(parsed))

    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    # Reject stale payloads to mitigate replay attacks.
    auth_date = parsed.get("auth_date")
    if auth_date and auth_date.isdigit():
        if time.time() - int(auth_date) > max_age_seconds:
            return None

    if "user" in parsed:
        try:
            parsed["user"] = json.loads(parsed["user"])
        except json.JSONDecodeError:
            parsed["user"] = None

    return parsed


def get_user_id_from_init_data(init_data: str) -> Optional[int]:
    payload = validate_init_data(init_data)
    if not payload:
        return None
    user = payload.get("user")
    if isinstance(user, dict) and "id" in user:
        return int(user["id"])
    return None
