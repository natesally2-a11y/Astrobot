# Mini App API Documentation

Mini App API is served by the same FastAPI app.

## Authentication

Production requests must include Telegram WebApp init data:

```http
X-Telegram-Init-Data: query_id=...&user=...&auth_date=...&hash=...
```

The backend verifies the signature using `BOT_TOKEN`.

In non-production environments, a `user_id` query parameter is accepted for local debugging:

```http
GET /api/profile?user_id=123456
```

## Endpoints

### GET `/api/profile`

Returns the user's Telegram profile, subscription state and saved birth metadata.

Response:

```json
{
  "telegram_id": 123456,
  "first_name": "Ada",
  "username": "ada",
  "subscription_type": "free",
  "subscription_expires_at": null,
  "has_birth_data": true,
  "birth_data": {
    "birth_date": "1992-03-24",
    "birth_time": "08:45:00",
    "birth_place": "Moscow, Russia"
  }
}
```

### GET `/api/chart`

Returns natal chart data for visualization.

Response:

```json
{
  "birth_datetime": "1992-03-24T08:45:00+00:00",
  "birth_place": "Moscow, Russia",
  "latitude": 55.7558,
  "longitude": 37.6173,
  "planets": [
    {
      "key": "Sun",
      "name": "Солнце",
      "longitude": 4.12,
      "sign": "Овен",
      "degree": 4.12,
      "house": 11
    }
  ],
  "aspects": []
}
```

### GET `/api/chart.svg`

Returns SVG markup wrapped in JSON:

```json
{
  "svg": "<svg ...>...</svg>"
}
```

### POST `/api/reading`

Generates a natal interpretation for the current user.

Response:

```json
{
  "reading": "..."
}
```

## Error responses

- `401` — missing or invalid Telegram init data
- `404` — user profile or natal chart not found
- `500` — unexpected server error
