# 🔮 Stellarium AI

**Персональный ИИ-астролог в Telegram** — бот + мини-приложение с натальными
картами, прогнозами на основе реальных транзитов, подписками через Telegram Stars
и полным соответствием GDPR / 152-ФЗ.

> ⚠️ Астрологические прогнозы носят исключительно развлекательный характер и не
> являются руководством к действию.

---

## ✨ Возможности

- 🪐 **Точная натальная карта** на основе Swiss Ephemeris (положения планет, дома, аспекты)
- 🤖 **ИИ-интерпретация** (OpenAI GPT-4) с кастомными астрологическими промптами
- ☀️ **Персональные прогнозы**: на день, неделю (Premium), важные транзиты (Premium)
- 💞 **Совместимость** (синастрия двух карт)
- 💬 **Чат-астролог** — задавайте любые вопросы (лимит на Free-тарифе)
- 🌌 **Mini App** — интерактивная карта (SVG), совместимость, транзиты, профиль
- ⭐ **Подписки через Telegram Stars** — Free / Pro (99₽) / Космический Оракул (299₽)
- 🔐 **GDPR / 152-ФЗ** — согласие, экспорт, удаление данных, дисклеймер
- 🚀 **Inline-режим** и **реферальная система** для вирусного роста

## 🏗 Технологический стек

| Слой            | Технология                                  |
|-----------------|---------------------------------------------|
| Бот             | [aiogram 3.x](https://docs.aiogram.dev)     |
| Web / Mini App  | FastAPI + Jinja2 + ванильный JS             |
| База данных     | PostgreSQL 15 + SQLAlchemy 2 (async)        |
| Кэш / FSM       | Redis (с fallback на память)                |
| Астрология      | Swiss Ephemeris (`pyswisseph`, Moshier)     |
| Геокодинг       | OpenStreetMap Nominatim                     |
| Часовые пояса   | `timezonefinder`                            |
| ИИ              | OpenAI GPT-4 (есть offline-mock режим)      |

## 📁 Структура проекта

```
app/
├── bot/                 # Telegram-бот (aiogram)
│   ├── handlers/        # /start, /chart, /today, оплата, GDPR, inline…
│   ├── keyboards/       # inline-клавиатуры + календарь
│   ├── middlewares/     # сессия БД, пользователь
│   └── utils/           # доступ/премиум/рефералы
├── webapp/              # Mini App
│   ├── api/             # REST API (auth по initData)
│   ├── templates/       # HTML
│   └── static/          # CSS/JS
├── astrology/           # движок: расчёты, SVG, ИИ, геокодинг
├── database/            # модели + CRUD (async SQLAlchemy)
├── config.py
└── main.py              # FastAPI + webhook/polling
tests/                   # pytest
Dockerfile, docker-compose.yml
privacy_policy.md, terms_of_service.md, deployment_guide.md, api_documentation.md
```

## 🚀 Быстрый старт (Docker)

```bash
cp .env.example .env
# отредактируйте .env: BOT_TOKEN, OPENAI_API_KEY (или OPENAI_MOCK=true)

docker compose up --build
```

Бот поднимется вместе с PostgreSQL и Redis. По умолчанию запускается в
**polling**-режиме (не нужен публичный HTTPS) — удобно для разработки.
Mini App доступен на `http://localhost:8000/app`.

## 🧑‍💻 Локальный запуск без Docker

```bash
pip install -r requirements.txt
cp .env.example .env            # заполните BOT_TOKEN

# Только бот (polling), SQLite вместо Postgres:
DATABASE_URL="sqlite+aiosqlite:///stellarium.db" OPENAI_MOCK=true \
  python -m app.bot.runner

# Либо полный сервер (бот + Mini App):
DATABASE_URL="sqlite+aiosqlite:///stellarium.db" OPENAI_MOCK=true \
  uvicorn app.main:app --reload
```

> Для SQLite дополнительно поставьте `pip install aiosqlite`.
> `OPENAI_MOCK=true` включает детерминированные ответы без обращения к OpenAI —
> удобно для разработки и CI.

## ⚙️ Конфигурация

Все параметры — в `.env` (см. `.env.example`). Ключевые:

| Переменная        | Назначение                                              |
|-------------------|---------------------------------------------------------|
| `BOT_TOKEN`       | токен от @BotFather                                      |
| `BOT_USERNAME`    | username бота (для рефералок/inline)                     |
| `RUN_MODE`        | `polling` (dev) или `webhook` (prod)                    |
| `WEBHOOK_URL`     | публичный HTTPS-домен (для webhook)                     |
| `WEBAPP_URL`      | URL мини-приложения                                     |
| `OPENAI_API_KEY`  | ключ OpenAI (или `OPENAI_MOCK=true`)                    |
| `DATABASE_URL`    | строка подключения (asyncpg/aiosqlite)                 |
| `REDIS_URL`       | Redis для FSM/кэша (можно оставить пустым)              |
| `SECRET_KEY`      | секрет для валидации WebApp initData                   |
| `ADMIN_IDS`       | ID администраторов (полный Premium для тестов)          |

## 🧪 Тесты

```bash
OPENAI_MOCK=true python -m pytest -q
```

## 💳 Тарифы

| Тариф               | Цена      | Stars | Возможности                                       |
|---------------------|-----------|-------|---------------------------------------------------|
| Free                | 0         | —     | Карта, базовый анализ, 5 вопросов/день            |
| Stellarium Pro      | 99₽/мес   | 50 ⭐ | Прогнозы день/неделя, транзиты, безлимит вопросов |
| Космический Оракул  | 299₽/мес  | 150 ⭐| Всё из Pro + бизнес-астрология, годовые прогнозы  |

## 📜 Документация

- [deployment_guide.md](deployment_guide.md) — пошаговый деплой (Docker, Nginx, webhook)
- [api_documentation.md](api_documentation.md) — REST API мини-приложения
- [privacy_policy.md](privacy_policy.md) — политика конфиденциальности
- [terms_of_service.md](terms_of_service.md) — пользовательское соглашение

## ⚖️ Правовое

Stellarium AI обрабатывает данные в соответствии с GDPR и ФЗ-152. Пользователь
даёт явное согласие перед сохранением данных и может в любой момент выгрузить
(`/export_data`) или удалить (`/delete_data`) их. Сервис носит развлекательный
характер.
