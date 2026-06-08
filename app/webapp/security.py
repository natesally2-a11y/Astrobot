import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, Query

from app.config import get_settings


def verify_telegram_init_data(init_data: str, bot_token: str) -> dict:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("Missing init data hash.")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid init data signature.")

    user_raw = parsed.get("user")
    return json.loads(user_raw) if user_raw else {}


async def get_webapp_user_id(
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    dev_user_id: int | None = Query(default=None, alias="user_id"),
) -> int:
    settings = get_settings()
    if x_telegram_init_data and settings.bot_token:
        try:
            user = verify_telegram_init_data(x_telegram_init_data, settings.require_bot_token())
            return int(user["id"])
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=401, detail="Invalid Telegram init data.") from exc

    if settings.environment != "production" and dev_user_id is not None:
        return dev_user_id

    raise HTTPException(status_code=401, detail="Telegram init data is required.")
