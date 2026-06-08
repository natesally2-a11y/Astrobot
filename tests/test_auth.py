"""Tests for Telegram WebApp initData validation."""
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

from app.config import settings
from app.webapp.auth import validate_init_data


def _make_init_data(bot_token: str, user: dict) -> str:
    fields = {
        "auth_date": str(int(time.time())),
        "query_id": "AAEEtest",
        "user": json.dumps(user, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def test_valid_init_data(monkeypatch):
    monkeypatch.setattr(settings, "bot_token", "12345:TESTTOKEN")
    init = _make_init_data("12345:TESTTOKEN", {"id": 777, "first_name": "Test"})
    payload = validate_init_data(init)
    assert payload is not None
    assert payload["user"]["id"] == 777


def test_tampered_init_data_rejected(monkeypatch):
    monkeypatch.setattr(settings, "bot_token", "12345:TESTTOKEN")
    init = _make_init_data("12345:TESTTOKEN", {"id": 777})
    tampered = init.replace("777", "888")
    assert validate_init_data(tampered) is None


def test_empty_init_data():
    assert validate_init_data("") is None
