# Mini App API Documentation

Все endpoints находятся под `/api`. В продакшене Mini App должен передавать Telegram WebApp
`initData`; подпись проверяется сервером по `BOT_TOKEN`.

В development режиме можно передавать `telegram_id` query-параметром.

## Auth examples

```text
GET /api/me?initData=<telegram-webapp-init-data>
GET /api/me?telegram_id=123456789
```

## GET /api/me

Возвращает профиль пользователя.

```json
{
  "telegram_id": 123456789,
  "first_name": "Anna",
  "username": "anna",
  "subscription_type": "free",
  "subscription_expires_at": null,
  "gdpr_consent": true,
  "has_birth_data": true
}
```

## GET /api/chart

Возвращает натальную карту, планеты, аспекты, транзиты и SVG.

```json
{
  "profile": {
    "birth_date": "1992-08-24",
    "birth_time": "14:30:00",
    "birth_place": "Казань, Россия",
    "latitude": 55.79,
    "longitude": 49.12,
    "timezone": "Europe/Moscow"
  },
  "planets": [
    {
      "planet": "sun",
      "label": "Солнце",
      "sign": "Дева",
      "degree": 1.2,
      "house": 9,
      "longitude": 151.2
    }
  ],
  "aspects": [],
  "transits": [],
  "svg": "<svg>...</svg>"
}
```

## GET /api/readings

Возвращает последние чтения пользователя.

```json
[
  {
    "id": 1,
    "type": "daily",
    "question": null,
    "response": "Сегодня...",
    "created_at": "2026-06-08T07:30:00Z"
  }
]
```

## POST /api/compatibility

Создает чтение совместимости с партнером.

Request:

```json
{
  "birth_date": "24.08.1992",
  "birth_time": "14:30",
  "birth_place": "Москва, Россия"
}
```

Response:

```json
{
  "reading": "Солнце первого партнера...",
  "partner_place": "Москва, Россия"
}
```

## GET /api/transits

Возвращает важные транзиты на дату.

```text
GET /api/transits?target_date=2026-06-08&initData=...
```

```json
[
  {
    "transit_planet": "Марс",
    "natal_planet": "Солнце",
    "aspect": "тригон",
    "orb": 1.4
  }
]
```
