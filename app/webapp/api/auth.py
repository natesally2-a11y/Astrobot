"""Validate Telegram Mini App ``initData`` and extract the user id."""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Optional
from urllib.parse import parse_qsl

from app.config import get_settings


def parse_init_data(init_data: str) -> dict:
    """Parse the ``initData`` string from window.Telegram.WebApp."""
    return dict(parse_qsl(init_data, keep_blank_values=True))


def verify_init_data(init_data: str) -> Optional[int]:
    """Verify the HMAC and return the Telegram user id when valid.

    Returns ``None`` if the signature is invalid or absent. Spec:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not init_data:
        return None
    settings = get_settings()
    if not settings.bot_token:
        return None

    pairs = parse_init_data(init_data)
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(
        f"{k}={pairs[k]}" for k in sorted(pairs.keys())
    )
    secret_key = hmac.new(
        b"WebAppData", settings.bot_token.encode("utf-8"), hashlib.sha256
    ).digest()
    calculated = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        return None

    user_json = pairs.get("user")
    if not user_json:
        return None
    try:
        user_obj = json.loads(user_json)
        return int(user_obj["id"])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None
