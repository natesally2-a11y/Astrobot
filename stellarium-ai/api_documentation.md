# Документация API Stellarium AI Mini App

Base URL: `https://yourdomain.com`

## Аутентификация

API Mini App использует `initData` от Telegram WebApp для валидации пользователя.
Для защищённых эндпоинтов передавайте `init_data` как query-параметр.

## Эндпоинты

### Health Check

```
GET /health
```

**Ответ:**
```json
{
  "status": "ok",
  "service": "stellarium-ai"
}
```

---

### Получить данные пользователя

```
GET /api/user/{user_id}
```

**Параметры:**
- `user_id` — Telegram ID пользователя

**Ответ:**
```json
{
  "telegram_id": 123456789,
  "display_name": "Александр",
  "subscription_type": "pro",
  "subscription_expires_at": "2025-02-01T12:00:00",
  "is_pro": true,
  "is_oracle": false
}
```

---

### Получить данные натальной карты

```
GET /api/chart/{user_id}
```

**Ответ:**
```json
{
  "birth_date": "1990-06-15",
  "birth_time": "14:30:00",
  "latitude": 55.75,
  "longitude": 37.62,
  "timezone": "Europe/Moscow",
  "planets": {
    "Sun": {
      "longitude": 83.5,
      "sign": "Gemini",
      "sign_ru": "Близнецы",
      "degree": 23.5,
      "minute": 30,
      "retrograde": false
    },
    "Moon": { "..." },
    "Mercury": { "..." }
  },
  "houses": [0.0, 30.0, 60.0, "..."],
  "ascendant": 145.3,
  "midheaven": 55.7,
  "aspects": [
    {
      "planet1": "Sun",
      "planet2": "Moon",
      "aspect_name": "Тригон",
      "angle": 120,
      "orb": 2.3
    }
  ]
}
```

---

### Получить SVG натальной карты

```
GET /api/chart/{user_id}/svg
```

**Content-Type:** `image/svg+xml`

Возвращает SVG-изображение натальной карты (600x600px, тёмная тема).

---

### Получить историю чтений

```
GET /api/readings/{user_id}?limit=10
```

**Параметры:**
- `user_id` — Telegram ID
- `limit` — количество записей (по умолчанию 10, макс 100)

**Ответ:**
```json
[
  {
    "id": 1,
    "type": "natal",
    "question": null,
    "response": "Ваша натальная карта говорит о...",
    "created_at": "2025-01-15T10:30:00"
  },
  {
    "id": 2,
    "type": "daily",
    "question": null,
    "response": "Сегодня звёзды благоволят...",
    "created_at": "2025-01-15T09:00:00"
  }
]
```

---

### Мини-приложение

```
GET /app
```

Возвращает HTML страницу Telegram Mini App с интерактивной натальной картой.

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | Успех |
| 404 | Пользователь или данные не найдены |
| 403 | Неверный initData |
| 500 | Внутренняя ошибка сервера |

---

## Webhook бота

```
POST /webhook
Content-Type: application/json
```

Принимает обновления от Telegram серверов. Настраивается автоматически при наличии `WEBHOOK_URL` в `.env`.

---

## Интеграция с Telegram WebApp

```javascript
// Инициализация
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Получить ID пользователя
const userId = tg.initDataUnsafe.user.id;

// Получить данные карты
const chartData = await fetch(`/api/chart/${userId}`).then(r => r.json());

// Закрыть и открыть бот
tg.openTelegramLink('https://t.me/stellarium_ai_bot?start=chart');
```

---

## Inline Mode

Бот поддерживает inline-режим:

```
@stellarium_ai_bot daily Дева
→ Прогноз для Девы на сегодня

@stellarium_ai_bot compatibility Лев Скорпион
→ Совместимость Льва и Скорпиона

@stellarium_ai_bot Козерог
→ Быстрый прогноз для Козерога
```
