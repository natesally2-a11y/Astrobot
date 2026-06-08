# Stellarium AI Mini App API

Base URL: `https://yourdomain.com`

## 1) GET `/api/profile/{user_id}`

Возвращает профиль пользователя и базовые данные рождения.

### Пример ответа

```json
{
  "telegram_id": 123456789,
  "first_name": "Alex",
  "username": "alex",
  "subscription_type": "free",
  "subscription_expires_at": null,
  "gdpr_consent": true,
  "birth_data": {
    "birth_date": "1991-08-15",
    "birth_time": "09:40:00",
    "birth_place": "Berlin, Germany",
    "latitude": 52.52,
    "longitude": 13.405
  }
}
```

## 2) GET `/api/chart/{user_id}`

Возвращает JSON-представление карты и SVG для визуализации.

### Поля

- `chart.planets[]`
- `chart.aspects[]`
- `chart.ascendant`
- `chart.houses[]`
- `svg` — строка SVG.

## 3) GET `/api/transits/{user_id}`

Возвращает транзиты дня и краткий ИИ-анализ.

### Пример ответа

```json
{
  "transits": [
    {
      "planet_a": "Transit Sun",
      "planet_b": "Natal Moon",
      "aspect_type": "trine",
      "exact_angle": 121.2,
      "orb": 1.2
    }
  ],
  "analysis": "Текст прогноза..."
}
```

## 4) POST `/api/compatibility`

Рассчитывает совместимость с партнером.

### Тело запроса

```json
{
  "user_id": 123456789,
  "partner_birth_date": "1990-05-03",
  "partner_birth_time": "18:25",
  "partner_place": "Rome"
}
```

### Ответ

```json
{
  "score": 74,
  "highlights": ["Sun: гармоничный тригон"],
  "report": "Текст интерпретации..."
}
```

## Ошибки

- `404` — пользователь/данные не найдены;
- `422` — невалидные даты/время или формат запроса.
