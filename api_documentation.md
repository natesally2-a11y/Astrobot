# API документация Mini App — Stellarium AI

Базовый URL: `https://yourdomain.com`

Все API-эндпоинты требуют заголовок `X-Telegram-Init-Data` с данными из `Telegram.WebApp.initData`.

## Аутентификация

```javascript
fetch('/app/chart', {
  headers: {
    'X-Telegram-Init-Data': window.Telegram.WebApp.initData
  }
})
```

Сервер валидирует подпись через HMAC-SHA256 с ключом, производным от `BOT_TOKEN`.

---

## GET /app

HTML-страница мини-приложения.

**Ответ:** HTML

---

## GET /app/chart

Получить натальную карту пользователя.

**Заголовки:**
- `X-Telegram-Init-Data` (required)

**Ответ 200:**
```json
{
  "chart": {
    "ascendant_sign": "Лев",
    "ascendant": 125.5,
    "midheaven": 35.2,
    "planets": [
      {
        "name": "Солнце",
        "sign": "Овен",
        "sign_emoji": "♈",
        "degree": 15.3,
        "longitude": 15.3,
        "house": 9,
        "retrograde": false
      }
    ],
    "aspects": [
      {
        "planet1": "Солнце",
        "planet2": "Луна",
        "type": "тригон",
        "orb": 2.1
      }
    ],
    "svg": "<svg>...</svg>"
  },
  "birth_place": "Москва, Россия",
  "birth_date": "1990-05-15",
  "subscription": "free",
  "subscription_expires": null
}
```

**Ошибки:**
- `401` — невалидный initData
- `200` с `"error": "no_chart"` — карта не создана

---

## GET /app/readings

История астрологических чтений.

**Заголовки:**
- `X-Telegram-Init-Data` (required)

**Ответ 200:**
```json
{
  "readings": [
    {
      "type": "daily",
      "question": null,
      "response": "Сегодня Луна...",
      "created_at": "2025-06-08T10:30:00+00:00"
    },
    {
      "type": "ask",
      "question": "Стоит ли менять работу?",
      "response": "Ваша карта показывает...",
      "created_at": "2025-06-07T15:00:00+00:00"
    }
  ]
}
```

---

## GET /app/profile

Профиль и статус подписки.

**Заголовки:**
- `X-Telegram-Init-Data` (required)

**Ответ 200:**
```json
{
  "first_name": "Анна",
  "subscription": "pro",
  "subscription_expires": "2025-07-08T00:00:00+00:00",
  "has_chart": true,
  "gdpr_consent": true
}
```

---

## GET /health

Проверка состояния сервиса (без аутентификации).

**Ответ 200:**
```json
{
  "status": "ok",
  "service": "stellarium-ai"
}
```

---

## Типы чтений (reading_type)

| Тип | Описание |
|-----|----------|
| `natal` | Анализ натальной карты |
| `daily` | Прогноз на день |
| `weekly` | Прогноз на неделю |
| `compatibility` | Совместимость |
| `transit` | Транзиты |
| `ask` | Вопрос астрологу |

---

## Тарифы (subscription)

| Значение | Описание |
|----------|----------|
| `free` | Бесплатный |
| `pro` | Stellarium Pro |
| `oracle` | Космический Оракул |

---

## Webhook (бот)

### POST /webhook

Принимает обновления от Telegram Bot API.

**Тело:** JSON Update object (см. [Telegram Bot API](https://core.telegram.org/bots/api#update))

**Ответ:** `{"ok": true}`

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 401 | Не авторизован (невалидный initData) |
| 404 | Пользователь не найден |
| 500 | Внутренняя ошибка сервера |
