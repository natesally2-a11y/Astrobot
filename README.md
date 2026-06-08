# Stellarium AI MVP

Telegram-бот и Mini App для персональной AI-астрологии:

- **Бот**: onboarding, сбор даты/времени/города, команды прогнозов, Telegram Stars подписки.
- **Mini App**: просмотр профиля и SVG-натальной карты.
- **Backend**: FastAPI + aiogram 3.x + PostgreSQL + Redis.
- **AI-движок**: OpenAI для интерпретации + Swiss Ephemeris для расчетов (с fallback).
- **Комплаенс**: GDPR/152-ФЗ согласие, экспорт/удаление данных, дисклеймер.

## Быстрый старт

1. Скопируйте пример env:

```bash
cp .env.example .env
```

2. Заполните в `.env`:
   - `BOT_TOKEN`
   - `OPENAI_API_KEY` (необязательно для demo fallback)
   - при необходимости `APP_BASE_URL`

3. Запуск в Docker:

```bash
docker compose up --build
```

4. Проверка:
   - API health: `http://localhost:8000/api/health`
   - Mini App: `http://localhost:8000/app`

## Основные команды бота

- `/start` — регистрация и запуск onboarding
- `/chart` — натальная карта + анализ
- `/today` — прогноз на сегодня
- `/week` — weekly прогноз (premium)
- `/compatibility YYYY-MM-DD` — совместимость с датой партнера
- `/ask <вопрос>` — вопрос ИИ-астрологу
- `/transit` — важный транзит дня (premium)
- `/settings` — подписка и доступ к mini app
- `/privacy`, `/my_data`, `/delete_data`, `/export_data`

## Структура проекта

```text
app/
  astrology/
  bot/
    handlers/
    keyboards/
    middlewares/
    utils/
  database/
  webapp/
    static/
    templates/
  config.py
  main.py
docker-compose.yml
Dockerfile
privacy_policy.md
terms_of_service.md
deployment_guide.md
api_documentation.md
```

## Примечания

- Для Telegram Stars используется валюта `XTR`.
- В бесплатном тарифе действует лимит `FREE_DAILY_QUESTION_LIMIT`.
- Для production-точных эфемерид установите `pyswisseph` (в MVP предусмотрен fallback при его отсутствии).
- Все астрологические ответы содержат развлекательный характер и не являются рекомендацией к действию.
