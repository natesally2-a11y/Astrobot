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
# заполните BOT_TOKEN, WEBHOOK_URL, WEBAPP_URL, OPENAI_API_KEY при наличии
docker compose up --build
```

Локально API будет доступен на `http://localhost:8000`.

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
