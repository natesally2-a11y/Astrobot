# 🌌 Stellarium AI

Stellarium AI — **AI-астролог в Telegram**: персональные натальные карты,
ежедневные прогнозы по транзитам, синастрия, ИИ-консультации и доступные
подписки через **Telegram Stars** (99₽ / 299₽). MVP включает бот, мини-приложение
с интерактивной картой, GDPR/152-ФЗ совместимый онбординг, инлайн-режим для
вирусного роста и реферальную систему.

## ✨ Возможности MVP

| Категория | Что доступно |
|-----------|--------------|
| Бот       | `/start` `/chart` `/today` `/week` `/compatibility` `/ask` `/transit` `/settings` `/privacy` `/my_data` `/export_data` `/delete_data` `/help` |
| Астрология | Расчёт планет, домов и аспектов через Swiss Ephemeris (`pyswisseph`) |
| ИИ | Интерпретации, прогнозы и синастрия через OpenAI GPT-4o (fallback без ключа) |
| Мини-приложение | SVG-карта, таблица планет, аспекты, статус подписки |
| Платежи | Telegram Stars (XTR), планы Pro (50★ / 99₽) и Oracle (150★ / 299₽) |
| GDPR / 152-ФЗ | Явное согласие, экспорт JSON, право быть забытым |
| Виральность | Inline-режим, реферальные ссылки (+7 дней Pro за друга) |
| DevOps | Dockerfile, docker-compose.yml, конфиг Nginx, режимы webhook / polling |

## 🚀 Быстрый старт (1 минута, без БД)

```bash
git clone <repo> stellarium && cd stellarium
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# BOT_TOKEN уже подставлен; добавьте OPENAI_API_KEY если есть
python run_bot.py
```

Бот стартует в long-polling режиме, использует SQLite (`stellarium.db`) и
без OpenAI работает в режиме «эвристических ответов».

## 🐳 Docker Compose

```bash
cp .env.example .env  # заполните секреты
docker compose up -d --build
docker compose logs -f app
```

Контейнеры: `stellarium_app` (FastAPI + bot), `stellarium_db` (Postgres 15),
`stellarium_redis` (Redis 7). Mini App доступен по адресу
`http://localhost:8000/app` (для Telegram — нужен HTTPS-домен).

## 📁 Структура проекта

```
stellarium-ai/
├── app/
│   ├── bot/                    # aiogram-роутеры, FSM, клавиатуры, middleware
│   │   ├── handlers/           # /start, /chart, /today, /ask, payments, inline…
│   │   ├── keyboards/          # Inline-меню
│   │   ├── middlewares/        # DB-сессия, регистрация пользователя
│   │   └── utils/              # доступ, лимиты, подписки
│   ├── webapp/                 # FastAPI + Mini App
│   │   ├── api/                # REST API (chart.svg, chart, me)
│   │   ├── static/             # CSS/JS Mini App
│   │   └── templates/          # HTML Mini App
│   ├── astrology/
│   │   ├── calculations.py     # Swiss Ephemeris + аспекты + синастрия
│   │   ├── chart_renderer.py   # SVG натальной карты
│   │   ├── ai_interpreter.py   # OpenAI промпты + fallback
│   │   └── geocoding.py        # OpenStreetMap Nominatim
│   ├── database/               # SQLAlchemy 2 async + CRUD
│   ├── payments/               # Описание планов Telegram Stars
│   ├── config.py               # pydantic-settings
│   └── main.py                 # FastAPI app + webhook + polling
├── docs/                       # privacy / terms / deployment / API
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── run_bot.py
```

## 🧠 Архитектура

- **Bot** (`aiogram 3.13`) — обрабатывает чат, FSM-онбординг, inline-режим,
  платежи.
- **FastAPI** — хостит Mini App, REST API, опциональный webhook для бота.
- **PostgreSQL / SQLite** — пользователи, натальные данные, подписки, история
  ИИ-чтений.
- **Swiss Ephemeris** — точные расчёты (Placidus-дома, аспекты с орбисами).
- **OpenAI GPT-4o** — интерпретации через продуманные системные промпты.
- **Telegram Stars (XTR)** — нативная микро-оплата без банковских интеграций.

См. подробности в `docs/deployment_guide.md` и `docs/api_documentation.md`.

## 🔐 GDPR / 152-ФЗ

- `/privacy` — короткая политика, `/privacy_full` — полный текст
  (`docs/privacy_policy.md`).
- `/my_data` — какие данные хранятся.
- `/export_data` — выгрузка JSON.
- `/delete_data` — необратимое удаление (право быть забытым).
- Согласие подтверждается кнопкой перед первым сохранением данных.

## 💸 Тарифы

| План | Цена | Stars | Включено |
|------|------|-------|----------|
| Free | 0₽ | — | Натальная карта, 5 вопросов в день |
| Pro | 99₽/мес | 50★ | Дневные/недельные прогнозы, безлимит вопросов, синастрия, транзиты |
| Oracle | 299₽/мес | 150★ | Pro + бизнес-астрология, годовые прогнозы, ритуалы, приоритет ИИ |

## ⚠️ Дисклеймер

Прогнозы носят исключительно развлекательный характер и не являются основанием
для медицинских, юридических или финансовых решений.

## 📚 Дополнительная документация

- [docs/privacy_policy.md](docs/privacy_policy.md)
- [docs/terms_of_service.md](docs/terms_of_service.md)
- [docs/deployment_guide.md](docs/deployment_guide.md)
- [docs/api_documentation.md](docs/api_documentation.md)
