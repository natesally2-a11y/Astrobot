# Stellarium AI

MVP Telegram-бота и Mini App для персональной астрологии на стеке:

- `FastAPI` — API, webhook и mini app
- `aiogram 3.x` — логика Telegram-бота
- `PostgreSQL 15` — хранение пользователей, натальных данных и подписок
- `Redis` — зарезервирован под кэш/очереди и rate limits
- `Swiss Ephemeris` (`pyswisseph`) — астрологические расчеты с fallback-режимом
- `OpenAI` — интерпретация карт и прогнозов с локальным fallback без API-ключа

## Что уже есть в MVP

- onboarding через `/start`
- обязательное GDPR/152-ФЗ consent-сообщение
- сбор даты, времени и места рождения
- геокодинг города через Nominatim OpenStreetMap API
- персональная натальная карта + SVG-рендер
- команды `/chart`, `/today`, `/week`, `/compatibility`, `/ask`, `/transit`, `/settings`
- экспорт, просмотр и удаление данных: `/my_data`, `/export_data`, `/delete_data`
- подписки через Telegram Stars (`XTR`) для Pro и Oracle
- mini app по адресу `/app`
- inline mode preview (`daily Virgo`, `compatibility Leo Scorpio`)
- Docker и `docker-compose` для деплоя

## Структура проекта

```text
app/
├── astrology/         # расчет карты, SVG и AI-интерпретации
├── bot/               # команды, onboarding, оплаты и inline mode
├── database/          # SQLAlchemy модели и CRUD
├── services/          # geocoding и подписочная логика
├── webapp/            # HTML/CSS/JS mini app + API роуты
└── main.py            # FastAPI entrypoint
```

## Быстрый старт локально

1. Скопируйте env:

   ```bash
   cp .env.example .env
   ```

2. Заполните:
   - `BOT_TOKEN`
   - `BOT_USERNAME`
   - `OPENAI_API_KEY` (опционально, есть fallback)
   - `BASE_URL` и `WEBHOOK_URL` для production webhook

3. Поднимите проект:

   ```bash
   docker compose up --build
   ```

4. Приложение будет доступно:
   - API: `http://localhost:8000`
   - healthcheck: `http://localhost:8000/healthz`
   - mini app: `http://localhost:8000/app`

## Локальный запуск без Docker

```bash
sudo apt-get install -y python3-dev build-essential
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Telegram webhook

Если переменные `BOT_TOKEN` и `WEBHOOK_URL` заданы, приложение на старте само выставит webhook:

```text
{WEBHOOK_URL}/webhook
```

Для local/dev можно не задавать webhook и использовать только mini app/API или настроить reverse proxy.

## Безопасность

- Не храните токен бота в репозитории — только в `.env` или секретах окружения.
- Если токен уже был опубликован, обязательно перевыпустите его через BotFather.
- AI-ответы и астрологические выводы сопровождаются дисклеймером о развлекательном характере.

## Документация

- `privacy_policy.md`
- `terms_of_service.md`
- `deployment_guide.md`
- `api_documentation.md`
