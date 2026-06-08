# API документация Stellarium AI Mini App

## Базовый URL

```
https://yourdomain.com/api
```

## Эндпоинты

### GET /api/chart/{user_id}

Получение данных натальной карты пользователя.

**Параметры:**
- `user_id` (path, int) — Telegram ID пользователя

**Ответ 200:**
```json
{
  "chart_text": "🌟 Натальная карта\n...",
  "sun_sign": "Лев",
  "moon_sign": "Рыбы",
  "rising_sign": "Скорпион",
  "planets": [
    {
      "name": "Солнце",
      "symbol": "☉",
      "sign": "Лев",
      "sign_symbol": "♌",
      "degree": 15.42,
      "house": 10,
      "retrograde": false
    }
  ],
  "houses": [
    {
      "number": 1,
      "sign": "Скорпион",
      "degree": 5.3
    }
  ],
  "aspects": [
    {
      "planet1": "Солнце",
      "planet2": "Луна",
      "type": "Тригон",
      "orb": 2.45
    }
  ]
}
```

**Ответ 404:**
```json
{"detail": "Birth data not found"}
```

---

### GET /api/chart/{user_id}/svg

Получение натальной карты в формате SVG.

**Параметры:**
- `user_id` (path, int) — Telegram ID пользователя

**Ответ 200:** SVG-изображение (`Content-Type: image/svg+xml`)

---

### GET /api/user/{user_id}

Получение информации о пользователе.

**Параметры:**
- `user_id` (path, int) — Telegram ID пользователя

**Ответ 200:**
```json
{
  "telegram_id": 123456789,
  "first_name": "Иван",
  "subscription": "pro",
  "has_birth_data": true,
  "birth_data": {
    "birth_date": "1990-05-15",
    "birth_time": "14:30:00",
    "birth_place": "Москва, Россия"
  }
}
```

---

### GET /api/readings/{user_id}

Получение истории чтений.

**Параметры:**
- `user_id` (path, int) — Telegram ID пользователя
- `limit` (query, int, default=20, max=50) — Количество записей

**Ответ 200:**
```json
[
  {
    "id": 1,
    "type": "daily",
    "question": null,
    "response": "Сегодня звёзды благоприятствуют...",
    "date": "2026-06-08T10:30:00"
  }
]
```

---

### GET /api/subscription/plans

Получение списка тарифных планов.

**Ответ 200:**
```json
{
  "plans": [
    {
      "id": "free",
      "name": "Бесплатный",
      "price": 0,
      "stars": 0,
      "features": ["Натальная карта", "Базовый анализ", "5 вопросов/день"]
    },
    {
      "id": "pro",
      "name": "Stellarium Pro",
      "price": 99,
      "stars": 50,
      "features": ["Подробные прогнозы", "Безлимитные вопросы"]
    },
    {
      "id": "oracle",
      "name": "Космический Оракул",
      "price": 299,
      "stars": 150,
      "features": ["Всё из Pro", "Бизнес-астрология"]
    }
  ]
}
```

---

### GET /health

Проверка состояния сервиса.

**Ответ 200:**
```json
{"status": "ok", "service": "stellarium-ai"}
```

---

### POST /webhook

Эндпоинт для Telegram webhook. Не предназначен для прямого вызова.

---

### GET /app

HTML-страница Mini App. Открывается через Telegram WebApp.

## Аутентификация Mini App

Mini App валидирует данные через `initData` от Telegram WebApp SDK:

```javascript
const tg = window.Telegram.WebApp;
const userId = tg.initDataUnsafe.user.id;
```

Серверная валидация выполняется через HMAC-SHA256 с использованием `BOT_TOKEN`.
