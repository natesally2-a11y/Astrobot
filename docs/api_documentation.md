# Mini App REST API

The Mini App talks to the FastAPI backend over a small JSON API.  Every
request **must** carry the original `Telegram.WebApp.initData` string as the
`X-Init-Data` HTTP header — the backend validates the HMAC signature using
the bot token (see `app/webapp/security.py`).

Base URL: `<WEBHOOK_URL>/api`

OpenAPI/Swagger UI: `<WEBHOOK_URL>/docs`

## Authentication

```http
GET /api/profile
X-Init-Data: query_id=AAH...&user=%7B%22id%22%3A12345%2C...%7D&auth_date=1700000000&hash=abc123
```

Responses:

- `200 OK` — request authorised.
- `401 Unauthorized` — `X-Init-Data` missing, invalid hash or older than
  24 h.

## Endpoints

### `GET /api/profile`

```json
{
  "telegram_id": 12345,
  "first_name": "Anna",
  "plan": "Pro",
  "plan_active_until": "2025-02-01T00:00:00+00:00",
  "has_birth_data": true,
  "asked_today": 2
}
```

### `GET /api/birth`

```json
{
  "birth_date": "1990-05-12",
  "birth_time": "14:30:00",
  "birth_place": "Moscow, Russia",
  "latitude": 55.7558,
  "longitude": 37.6173,
  "timezone": "Europe/Moscow"
}
```

`404` if the user has not completed onboarding.

### `GET /api/chart.svg`

Returns a deterministic SVG natal chart (Content-Type `image/svg+xml`) sized
for embedding into the Mini App.

### `GET /api/chart/summary`

```json
{
  "summary": "Asc: 14° Lev\nSun: 21°30' Bull\n...",
  "positions": [
    {"name": "Sun", "sign": "Овен", "longitude": 12.34,
     "degree_in_sign": 12.34, "house": 1, "retrograde": false},
    ...
  ],
  "aspects": [
    {"a": "Sun", "b": "Moon", "aspect": "Trine", "orb": 1.2},
    ...
  ],
  "generated_at": "2025-01-15T12:00:00+00:00"
}
```

### `GET /api/readings?limit=20`

Returns the latest readings for the authenticated user:

```json
[
  {
    "id": 42,
    "type": "daily",
    "question": null,
    "response": "Сегодня для тебя ...",
    "created_at": "2025-01-15T08:30:00+00:00"
  }
]
```

### `GET /api/healthz`

Liveness probe.  Returns `{"status": "ok"}`.

## Error format

Errors follow FastAPI's default envelope:

```json
{"detail": "User not found. Open the bot first."}
```

## Rate limiting

The MVP does not implement application-level rate limiting — rely on nginx
(`limit_req_zone`) or your cloud provider's WAF.  Free tier users are gated
by `FREE_DAILY_QUESTIONS` (default 5/day) inside the bot.

## Webhook (server-to-Telegram)

If `USE_WEBHOOK=true`, Telegram delivers updates to:

```
POST <WEBHOOK_URL>/webhook/<WEBHOOK_SECRET>
Content-Type: application/json
```

The handler validates the secret path segment and forwards updates to the
aiogram dispatcher.
