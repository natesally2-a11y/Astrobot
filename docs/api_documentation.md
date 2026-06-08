# Stellarium AI — Mini App API

Base URL: `https://yourdomain.com`

Все защищённые эндпойнты требуют заголовок
`X-Telegram-Init-Data`, значение которого равно `window.Telegram.WebApp.initData`.
Подпись проверяется по алгоритму из документации Telegram
(<https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app>).

## Аутентификация

```http
GET /api/me
X-Telegram-Init-Data: query_id=...&user=...&hash=...
```

Возможные ответы:

| HTTP | Тело | Значение |
|------|------|----------|
| 200  | `{...}` | OK |
| 401  | `{"detail": "invalid_init_data"}` | Подпись не прошла проверку |
| 404  | `{"detail": "user_not_found"}` | Пользователь не зарегистрирован в боте |

## `GET /api/me`

Возвращает базовый профиль текущего пользователя.

```json
{
  "telegram_id": 123456789,
  "first_name": "Маша",
  "subscription_type": "pro",
  "is_premium": true,
  "subscription_expires_at": "2026-07-08T12:00:00+00:00",
  "has_birth_data": true,
  "birth_place": "Москва, Россия"
}
```

## `GET /api/chart`

Возвращает структурированную натальную карту текущего пользователя.

```json
{
  "sun": "Лев",
  "moon": "Скорпион",
  "ascendant": "Дева",
  "has_time": true,
  "timezone": "Europe/Moscow",
  "houses": [12.4, 35.7, ...],
  "planets": [
    {
      "name": "Sun",
      "name_ru": "Солнце",
      "glyph": "☉",
      "longitude": 132.45,
      "sign": "Лев",
      "sign_glyph": "♌",
      "sign_degree": 12.45,
      "house": 11,
      "retrograde": false
    }
  ],
  "aspects": [
    {
      "planet_a": "Sun",
      "planet_b": "Moon",
      "name": "trine",
      "name_ru": "тригон",
      "angle": 120,
      "orb": 1.2
    }
  ]
}
```

Ошибки: `404 birth_data_required` если пользователь ещё не ввёл данные.

## `GET /api/chart.svg`

Возвращает SVG-карту (Content-Type: `image/svg+xml`). Удобно использовать как
`<img src>` или вставлять inline.

## `GET /api/preview/chart.svg`

**Публичный** эндпойнт без проверки initData — предназначен для лендингов и
демонстрационных материалов.

Параметры query:

| Параметр | Тип | Default |
|----------|-----|---------|
| `year`   | int | required |
| `month`  | int | required |
| `day`    | int | required |
| `hour`   | int | 12 |
| `minute` | int | 0 |
| `lat`    | float | 55.7558 (Москва) |
| `lon`    | float | 37.6173 |

## События из Mini App в бот

Кнопки в мини-приложении используют `Telegram.WebApp.sendData(...)` для
обратной связи. Поддерживаемые значения:

| `sendData` | Действие в боте |
|------------|-----------------|
| `request_chart_reading` | Открыть новое чтение (эквивалент `/chart`) |
| `open_subscriptions`    | Показать тарифы (эквивалент `/settings`) |

Их обработка в боте сейчас сводится к закрытию Mini App и возвращению
пользователя в чат; для расширения добавьте handler на
`Message.web_app_data`.

## Версионирование

Текущая версия API — `0.1.0`. Все изменения публикуются в CHANGELOG, breaking
changes сопровождаются переходным префиксом `/api/v2/...`.
