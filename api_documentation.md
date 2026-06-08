# Mini App API documentation

Base URL examples:

- local: `http://localhost:8000`
- production: `https://yourdomain.com`

## 1. `GET /healthz`

Проверка состояния сервиса.

### Response

```json
{
  "status": "healthy"
}
```

## 2. `GET /api/webapp/profile`

Возвращает профиль пользователя, summary карты и последние чтения.

### Query params

- `telegram_id` — optional integer. Если отсутствует, используется demo payload.

### Response

```json
{
  "user": {
    "telegram_id": 123456789,
    "first_name": "Anna",
    "subscription_type": "free"
  },
  "birth_data": {
    "birth_place": "Moscow, Russia",
    "birth_date": "1994-11-17",
    "birth_time": "09:30"
  },
  "chart_summary": "Core placements: ...",
  "plan": "free",
  "recent_readings": [],
  "disclaimer": "..."
}
```

## 3. `GET /api/webapp/chart`

Возвращает структуру натальной карты:

- список планет
- дома
- аспекты
- summary

### Query params

- `telegram_id` — optional integer

## 4. `GET /api/webapp/chart.svg`

Возвращает SVG-рендер карты.

### Query params

- `telegram_id` — optional integer

### Content-Type

`image/svg+xml`

## 5. `GET /api/webapp/daily`

Возвращает дневной прогноз по натальной карте.

### Query params

- `telegram_id` — optional integer

### Response

```json
{
  "forecast": "Сегодня ...",
  "disclaimer": "..."
}
```

## 6. Telegram webhook

### `POST /webhook`

Принимает Telegram Update payload и передает его в aiogram dispatcher.

Если `BOT_TOKEN` не задан, endpoint возвращает `503`.

## 7. Ошибки

Общие ответы ошибок:

- `503` — bot token не сконфигурирован
- `422` — некорректные query/body параметры
- `500` — внутренняя ошибка сервиса
