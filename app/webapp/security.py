from __future__ import annotations

import hashlib
import hmac
import json
from urllib.parse import parse_qsl


def validate_init_data(init_data: str, bot_token: str) -> dict:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("missing hash")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("invalid init data hash")

    user = parsed.get("user")
    parsed["user"] = json.loads(user) if user else None
    return parsed


def extract_user_id_from_init_data(init_data: str, bot_token: str) -> int:
    parsed = validate_init_data(init_data, bot_token)
    user = parsed.get("user")
    if not user or "id" not in user:
        raise ValueError("missing user")
    return int(user["id"])
