"""Telegram WebApp ``initData`` validation.

Spec: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Optional
from urllib.parse import parse_qsl

from app.config import settings


class InvalidInitData(Exception):
    pass


def parse_init_data(
    init_data: str,
    *,
    bot_token: Optional[str] = None,
    max_age_seconds: int = 24 * 60 * 60,
) -> dict:
    if not init_data:
        raise InvalidInitData("init_data is empty")

    token = bot_token or settings.bot_token
    if not token:
        raise InvalidInitData("Bot token is not configured")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise InvalidInitData("hash field is missing")

    data_check_string = "\n".join(
        f"{k}={parsed[k]}" for k in sorted(parsed.keys())
    )
    secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise InvalidInitData("hash mismatch")

    auth_date = parsed.get("auth_date")
    if auth_date and auth_date.isdigit():
        if int(time.time()) - int(auth_date) > max_age_seconds:
            raise InvalidInitData("init_data is too old")

    user_payload = parsed.get("user")
    if user_payload:
        try:
            parsed["user"] = json.loads(user_payload)
        except json.JSONDecodeError:
            raise InvalidInitData("user field is not valid JSON")
    return parsed


def telegram_id_from_init_data(init_data: str) -> int:
    payload = parse_init_data(init_data)
    user = payload.get("user")
    if not isinstance(user, dict) or "id" not in user:
        raise InvalidInitData("user.id missing")
    return int(user["id"])
