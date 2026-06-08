# ✨ Stellarium AI

Персональный ИИ-астролог в Telegram: бот + Mini App. Строит **точную натальную
карту** по дате, времени и месту рождения, рассчитывает транзиты и даёт
персонализированные прогнозы через GPT — а не общие гороскопы по знакам.

> ⚠️ Все прогнозы носят **развлекательный характер** и не являются руководством
> к действию (см. дисклеймер в боте и `terms_of_service.md`).

## Возможности

- 🪐 Натальная карта на Swiss Ephemeris (планеты, дома, аспекты) + SVG-визуализация
- 🤖 ИИ-интерпретация (OpenAI GPT) с кастомными астрологическими промптами
- 🌤 Прогнозы: на день, неделю/месяц (Premium), транзиты (Premium)
- 💞 Совместимость (синастрия двух карт)
- 🔮 Вопросы астрологу (лимит 5/день на Free, безлимит на Premium)
- 💳 Подписки через **Telegram Stars** (Free / Pro 99₽ / Oracle 299₽)
- 📱 Mini App: интерактивная карта, совместимость, транзиты, профиль
- 🔗 Inline-режим для вирусного роста (`@bot daily Лев`, `@bot compatibility Лев Скорпион`)
- 🎁 Реферальная программа (+1 неделя Premium за друга)
- 🔐 GDPR / 152-ФЗ: согласие, просмотр, экспорт (JSON) и удаление данных

## Технологический стек

| Слой | Технология |
|------|------------|
| Бот | aiogram 3.x |
| Web / Mini App | FastAPI + Uvicorn + Jinja2 |
| БД | PostgreSQL 15 (SQLAlchemy 2.0 async, asyncpg) |
| Кэш / FSM | Redis |
| Астрология | Swiss Ephemeris (`pyswisseph`, режим Moshier — без файлов эфемерид) |
| ИИ | OpenAI GPT (`gpt-4o` по умолчанию) |
| Геокодинг | OpenStreetMap Nominatim + `timezonefinder` |

## Структура проекта

```
stellarium-ai/
├── app/
│   ├── bot/                 # Telegram-бот
│   │   ├── handlers/        # Обработчики команд и колбэков
│   │   ├── keyboards/       # Inline-клавиатуры (меню, календарь, подписки)
│   │   ├── middlewares/     # Инъекция сессии БД
│   │   ├── bot.py           # Фабрика Bot/Dispatcher
│   │   ├── commands.py      # Меню команд
│   │   ├── states.py        # FSM-состояния
│   │   └── texts.py         # Тексты сообщений
│   ├── webapp/              # Mini App
│   │   ├── static/          # CSS, JS
│   │   ├── templates/       # HTML
│   │   ├── api.py           # REST API
│   │   ├── auth.py          # Валидация Telegram initData
│   │   └── views.py         # HTML-страница /app
│   ├── astrology/           # Астрологический движок
│   │   ├── calculations.py  # Swiss Ephemeris (карта, транзиты, аспекты)
│   │   ├── ai_interpreter.py# GPT-промпты
│   │   ├── chart_renderer.py# SVG-генерация
│   │   ├── chart_summary.py # Текстовое описание карты
│   │   └── constants.py     # Знаки, планеты, аспекты
│   ├── services/            # Геокодинг, сборка карты
│   ├── database/            # models.py, crud.py, session.py
│   ├── plans.py             # Тарифные планы
│   ├── config.py            # Настройки (env)
│   └── main.py              # FastAPI + webhook/polling
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── schema.sql
├── privacy_policy.md
├── terms_of_service.md
├── deployment_guide.md
└── api_documentation.md
```

## Быстрый старт (Docker)

1. Скопируйте переменные окружения и заполните их:

```bash
cp .env.example .env
# Впишите BOT_TOKEN (из @BotFather) и OPENAI_API_KEY
```

2. Запустите весь стек (бот + Postgres + Redis):

```bash
docker compose up -d --build
```

По умолчанию бот стартует в режиме **polling** — внешний домен не нужен.
Для продакшена с Mini App и вебхуком см. `deployment_guide.md`.

## Локальный запуск (без Docker)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # заполните BOT_TOKEN; для разработки можно SQLite

# Только бот (long-polling):
python -m app.run_polling

# Бот + Mini App API (FastAPI):
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> Для разработки можно использовать SQLite:
> `DATABASE_URL=sqlite+aiosqlite:///./stellarium.db` (установите `aiosqlite`).
> Без `OPENAI_API_KEY` бот работает в демо-режиме (заглушки интерпретаций).
> Без публичного `WEBHOOK_BASE_URL` кнопки Mini App в боте скрываются.

## Переменные окружения

См. `.env.example`. Ключевые: `BOT_TOKEN`, `OPENAI_API_KEY`, `DATABASE_URL`,
`REDIS_URL`, `WEBHOOK_BASE_URL`, `WEBHOOK_SECRET`, `BOT_MODE` (`polling`/`webhook`),
`SECRET_KEY`, `BOT_USERNAME`.

## Команды бота

`/start` `/chart` `/today` `/week` (Premium) `/compatibility` `/ask`
`/transit` (Premium) `/settings` `/help`
Приватность: `/privacy` `/my_data` `/export_data` `/delete_data`

## Тарифы

| План | Цена | Stars | Лимит вопросов |
|------|------|-------|----------------|
| Free | 0 | — | 5 / день |
| Stellarium Pro | 99₽ | 50★ | безлимит |
| Космический Оракул | 299₽ | 150★ | безлимит |

## Документация

- [Политика конфиденциальности](privacy_policy.md)
- [Пользовательское соглашение](terms_of_service.md)
- [Руководство по деплою](deployment_guide.md)
- [API Mini App](api_documentation.md)
