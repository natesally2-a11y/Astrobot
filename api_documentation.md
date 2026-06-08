# Документация REST API мини-приложения

Базовый префикс: `/api`. Все эндпоинты возвращают `application/json`.

## Аутентификация

Mini App аутентифицируется через **Telegram WebApp initData**. Клиент передаёт
строку `Telegram.WebApp.initData` в HTTP-заголовке:

```
X-Telegram-Init-Data: <initData>
```

Сервер проверяет подпись по алгоритму
[Telegram](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app)
(HMAC-SHA256 с ключом, производным от `BOT_TOKEN`) и отклоняет устаревшие данные
(старше 24 часов).

- `401 Unauthorized` — initData отсутствует или подпись неверна.
- `404 Not Found` — у пользователя нет нужных данных (например, натальной карты).
- `422 Unprocessable Entity` — некорректные входные параметры.

---

## GET `/api/me`

Профиль текущего пользователя и статус подписки.

**Ответ 200:**
```json
{
  "registered": true,
  "first_name": "Аня",
  "subscription_type": "pro",
  "subscription_title": "Stellarium Pro",
  "is_premium": true,
  "subscription_expires_at": "2026-07-08T10:00:00+00:00",
  "has_chart": true,
  "remaining_questions": -1,
  "referral_count": 3
}
```
`remaining_questions = -1` означает безлимит (Premium). Для незарегистрированного
пользователя вернётся `{"registered": false}`.

---

## GET `/api/chart`

Натальная карта текущего пользователя.

**Ответ 200 (сокращённо):**
```json
{
  "planets": [
    {
      "key": "sun", "name": "Солнце", "longitude": 112.68,
      "sign": "Рак", "sign_index": 3, "degree": 22.68,
      "position": "22°41′ Рак", "house": 9, "retrograde": false
    }
  ],
  "aspects": [
    { "body1": "Солнце", "body2": "Юпитер", "type": "Соединение", "key": "conjunction", "orb": 0.1 }
  ],
  "ascendant": { "longitude": 200.3, "sign": "Весы" },
  "midheaven": 110.5,
  "has_houses": true,
  "svg": "<svg ...>...</svg>",
  "birth": { "date": "1990-07-15", "time": "14:30:00", "place": "Москва", "time_known": true }
}
```
Поле `svg` содержит готовое изображение карты для встраивания.
`404`, если карта ещё не создана (нужно пройти онбординг в боте).

---

## GET `/api/transits`

Текущие транзиты к натальным планетам (до 20 ближайших по орбу).

**Ответ 200:**
```json
{
  "is_premium": true,
  "transits": [
    { "transiting": "Сатурн", "natal": "Нептун", "type": "Квадрат", "orb": 0.1 }
  ]
}
```
Для не-Premium пользователей данные возвращаются, но клиент показывает CTA на
оформление подписки (`is_premium: false`).

---

## POST `/api/compatibility`

Быстрый расчёт совместимости (синастрия) с партнёром.

**Тело запроса:**
```json
{
  "date": "1992-03-21",
  "time": "08:15",
  "place": "Санкт-Петербург",
  "latitude": null,
  "longitude": null,
  "timezone": null
}
```
- `date` — обязательно (`YYYY-MM-DD`).
- `time` — опционально (`HH:MM`).
- Координаты можно передать напрямую (`latitude`/`longitude`/`timezone`) либо
  указать `place` — тогда сервер геокодирует город через Nominatim.

**Ответ 200:**
```json
{
  "score": 78,
  "user_chart": { "...": "serialized chart" },
  "partner_chart": { "...": "serialized chart" },
  "hint": "Полный ИИ-анализ совместимости доступен в чат-боте (/compatibility)."
}
```
`score` — упрощённая оценка 0–100 по гармонии стихий Солнца/Луны/Венеры.
Полный ИИ-анализ синастрии доступен в боте командой `/compatibility`.

---

## Прочие (вне `/api`)

| Метод | Путь        | Назначение                                   |
|-------|-------------|----------------------------------------------|
| GET   | `/`         | Лендинг                                       |
| GET   | `/app`      | HTML мини-приложения                          |
| GET   | `/health`   | Health-check (`{"status":"ok"}`)             |
| POST  | `/webhook`  | Приём апдейтов Telegram (webhook-режим)       |
| GET   | `/docs`     | Swagger UI (автодокументация FastAPI)         |

## Пример вызова (JavaScript)

```js
const res = await fetch("/api/chart", {
  headers: { "X-Telegram-Init-Data": Telegram.WebApp.initData },
});
const chart = await res.json();
document.getElementById("chart").innerHTML = chart.svg;
```
