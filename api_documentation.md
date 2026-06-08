# API Mini App — Stellarium AI

REST API, обслуживающий Telegram Mini App. Базовый URL:
`https://yourdomain.com`.

## Аутентификация

Все эндпоинты `/api/*` авторизуются по **Telegram WebApp `initData`**.
Клиент передаёт строку `Telegram.WebApp.initData` в теле запроса как
`init_data`. Сервер проверяет подпись HMAC-SHA256:

```
secret_key = HMAC_SHA256("WebAppData", BOT_TOKEN)
hash       = HMAC_SHA256(secret_key, data_check_string)
```

где `data_check_string` — отсортированные по ключу пары `key=value`
(кроме `hash`), соединённые `\n`. Запрос отклоняется (`401`), если подпись
неверна или `auth_date` старше 24 часов.

> **Dev-режим:** если на сервере не задан `BOT_TOKEN`, проверка отключается и
> можно передавать `dev_user_id` напрямую (только для локальной отладки!).

Общие коды ошибок: `401` (auth), `403` (нет доступа/Premium),
`400` (неверный ввод), `404` (не найдено).

---

## POST /api/me

Профиль пользователя, статус подписки и натальная карта.

**Запрос**
```json
{ "init_data": "<Telegram.WebApp.initData>" }
```

**Ответ (зарегистрирован)**
```json
{
  "registered": true,
  "first_name": "Анна",
  "subscription": {
    "type": "pro",
    "title": "Stellarium Pro",
    "active": true,
    "is_premium": true,
    "expires_at": "2026-07-08T07:00:00+00:00"
  },
  "referral_count": 2,
  "birth": { "date": "1992-03-21", "time": "14:15:00", "place": "Казань, Россия" },
  "chart": {
    "has_time": true,
    "ascendant": { "sign": "Лев", "degree": 12.3 },
    "midheaven": { "sign": "Телец" },
    "planets": [
      { "key": "sun", "name": "Солнце", "symbol": "☉", "sign": "Овен",
        "degree": 0.9, "retrograde": false, "house": 9, "element": "Огонь" }
    ],
    "aspects": [
      { "body1": "Солнце", "body2": "Луна", "name": "Тригон",
        "symbol": "△", "orb": 2.1 }
    ],
    "svg": "<svg ...>...</svg>"
  }
}
```

Если пользователь не зарегистрирован: `{ "registered": false }`.
Если нет данных рождения — поле `chart` будет `null`.

---

## POST /api/transits

Текущие важные транзиты + ИИ-интерпретация. **Только для Premium** (Pro/Oracle).

**Запрос**
```json
{ "init_data": "..." }
```

**Ответ**
```json
{
  "transits": [
    { "body1": "транзитный Сатурн", "body2": "натальное Солнце",
      "name": "Квадрат", "orb": 1.2 }
  ],
  "interpretation": "Текст прогноза..."
}
```

Ошибки: `403` (нужна Premium-подписка), `400` (нет данных рождения).

---

## POST /api/compatibility

Синастрия: совместимость пользователя с партнёром.

**Запрос**
```json
{
  "init_data": "...",
  "partner_name": "Иван",
  "birth_date": "1990-05-15",
  "birth_time": "09:30",
  "city": "Москва"
}
```
`birth_time` — необязательно (`null` → расчёт без домов партнёра).

**Ответ**
```json
{
  "interpretation": "Анализ совместимости...",
  "partner_chart": { "...": "как в /api/me chart" }
}
```

Ошибки: `400` (неверная дата/нет данных), `404` (город не найден).

---

## GET /health

Проверка живости сервиса (без авторизации).
```json
{ "status": "ok", "version": "1.0.0" }
```

## GET /app

HTML-страница Mini App (подключает `telegram-web-app.js`, `/static/app.js`,
`/static/app.css`).

---

## Серверный webhook (служебный)

`POST /webhook` — приём апдейтов Telegram (только при `BOT_MODE=webhook`).
Проверяется заголовок `X-Telegram-Bot-Api-Secret-Token` == `WEBHOOK_SECRET`.
Не предназначен для прямого вызова клиентами.
