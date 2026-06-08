"""Валидация Telegram WebApp initData (HMAC-SHA256)."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from app.config import settings

MAX_AUTH_AGE = 24 * 3600  # сутки


class InitDataError(Exception):
    pass


def validate_init_data(init_data: str, max_age: int = MAX_AUTH_AGE) -> dict:
    """Проверить подпись initData и вернуть распарсенные данные.

    Бросает InitDataError при невалидной подписи.
    """
    if not init_data:
        raise InitDataError("empty init data")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise InitDataError("no hash")

    data_check_string = "\n".join(
        f"{k}={parsed[k]}" for k in sorted(parsed.keys())
    )
    secret_key = hmac.new(
        b"WebAppData", settings.bot_token.encode(), hashlib.sha256
    ).digest()
    calculated = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        raise InitDataError("invalid hash")

    auth_date = int(parsed.get("auth_date", "0"))
    if max_age and auth_date and (time.time() - auth_date > max_age):
        raise InitDataError("init data expired")

    if "user" in parsed:
        try:
            parsed["user"] = json.loads(parsed["user"])
        except json.JSONDecodeError:
            pass
    return parsed


def get_user_id(init_data: str) -> int:
    data = validate_init_data(init_data)
    user = data.get("user")
    if not isinstance(user, dict) or "id" not in user:
        raise InitDataError("no user id")
    return int(user["id"])
