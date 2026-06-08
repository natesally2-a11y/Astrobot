# Stellarium AI Mini App API

Base URL: `http://localhost:8000`

## Healthcheck

### `GET /api/health`

Ответ:

```json
{"status":"ok"}
```

## Пользователь

### `GET /api/user/{telegram_id}`

Возвращает профиль и birth_data.

Коды:
- `200` OK
- `404` пользователь не найден

## Натальная карта

### `GET /api/chart/{telegram_id}`

Возвращает:
- `svg` — SVG-представление карты
- `sun_sign` — солнечный знак

Коды:
- `200` OK
- `404` birth data не найдено

## История чтений

### `GET /api/readings/{telegram_id}`

Список последних чтений (до 50):

```json
[
  {
    "reading_type": "daily",
    "question": null,
    "ai_response": "...",
    "created_at": "2026-06-08T07:30:00"
  }
]
```

## Совместимость

### `GET /api/compatibility?first_date=YYYY-MM-DD&second_date=YYYY-MM-DD`

Пример ответа:

```json
{"result":"Солнечная совместимость: 76%. Это очень гармоничная пара."}
```

