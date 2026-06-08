import hashlib
import hmac
from urllib.parse import urlencode

from app.webapp.security import verify_telegram_init_data


def test_verify_telegram_init_data() -> None:
    bot_token = "123:ABC"
    payload = {
        "auth_date": "1710000000",
        "query_id": "AAE",
        "user": '{"id":42,"first_name":"Ada"}',
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    payload["hash"] = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    assert verify_telegram_init_data(urlencode(payload), bot_token)["id"] == 42
