# Stellarium AI

MVP Telegram Bot + Mini App для персонального AI-астролога.

## Что входит

- Telegram bot на `aiogram 3.x`
- FastAPI backend с webhook `/webhook`
- Mini App `/app` с натальной картой, транзитами, историей чтений и совместимостью
- PostgreSQL модели: пользователи, birth data, readings, subscriptions
- Swiss Ephemeris (`pyswisseph`) для расчета планет, домов и аспектов
- OpenAI GPT-интерпретации с локальным fallback без ключа
- Telegram Stars payments (`XTR`) для тарифов:
  - Free: карта, краткий дневной прогноз, 5 AI-вопросов в день
  - Stellarium Pro: 50 Stars/месяц
  - Космический Оракул: 150 Stars/месяц
- GDPR/152-ФЗ команды: `/privacy`, `/my_data`, `/export_data`, `/delete_data`
- Inline mode examples: `daily Virgo`, `compatibility Leo Scorpio`

## Быстрый старт

```bash
cp .env.example .env
# обязательно заполните BOT_TOKEN
# для локального запуска без публичного HTTPS оставьте WEBHOOK_URL пустым
docker compose --profile polling up --build
```

Локально API и Mini App будут доступны на `http://localhost:8000`. Для проверки Mini App
в браузере используйте development query-параметр с вашим Telegram ID:

```text
http://localhost:8000/app?telegram_id=123456789
```

Для production webhook-режима укажите:

```env
WEBHOOK_URL=https://yourdomain.com/webhook
WEBAPP_URL=https://yourdomain.com/app
ENVIRONMENT=production
```

и запускайте обычный backend:

```bash
docker compose up --build
```

## Основные команды

```text
/start — регистрация и создание карты
/chart — натальная карта + AI-анализ
/today — прогноз на сегодня
/week — прогноз на неделю (Premium)
/compatibility — совместимость с партнером
/ask — вопрос AI-астрологу
/transit — важные транзиты (Premium)
/settings — Mini App, подписки и экспорт
/privacy — политика конфиденциальности
/my_data — показать сохраненные данные
/export_data — экспорт JSON
/delete_data — удаление аккаунта
```

## Важно про секреты

Не коммитьте токен BotFather и ключ OpenAI. Используйте только переменные окружения:

```env
BOT_TOKEN=...
OPENAI_API_KEY=...
```

Если токен был отправлен в чат или опубликован, перевыпустите его в BotFather.

## Документация

- [Privacy Policy](privacy_policy.md)
- [Terms of Service](terms_of_service.md)
- [Deployment Guide](deployment_guide.md)
- [Mini App API Documentation](api_documentation.md)

## Если бот или Mini App не отвечают

1. Проверьте, что `BOT_TOKEN` в `.env` задан и токен не был отозван в BotFather.
2. Для локального запуска используйте polling: `docker compose --profile polling up --build`. Без polling или публичного `WEBHOOK_URL` Telegram не доставит сообщения боту.
3. Не оставляйте `WEBHOOK_URL=https://yourdomain.com/webhook`; пустой `WEBHOOK_URL` означает локальный режим.
4. Откройте `http://localhost:8000/health` и проверьте, что backend отвечает.
5. Mini App внутри Telegram требует публичный HTTPS URL, настроенный в BotFather. Для браузерной проверки используйте `?telegram_id=...` в development режиме.
