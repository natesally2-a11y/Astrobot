# ✦ Stellarium AI — Персональный ИИ-Астролог

Telegram-бот + Мини-приложение с персонализированными астрологическими прогнозами на основе точной натальной карты пользователя.

## Возможности

- 🗺 **Натальная карта** — расчёт по дате/времени/месту рождения (Swiss Ephemeris)
- ☀️ **Ежедневные прогнозы** — персональные, не общие гороскопы
- 💕 **Совместимость** — синастрия двух карт
- 🔮 **Вопросы ИИ-астрологу** — GPT-4o с астрологическим контекстом
- 💫 **Транзиты** — текущие планетарные влияния (Pro)
- 📅 **Недельные прогнозы** (Pro)
- 💳 **Telegram Stars** — микроплатежи 50⭐ и 150⭐
- 🔒 **GDPR/ФЗ-152** — полное соответствие требованиям
- 🌐 **Мини-приложение** — интерактивная карта в браузере Telegram
- 📢 **Inline-режим** — вирусный рост через @stellarium_bot

## Быстрый старт

### 1. Клонировать и настроить

```bash
git clone <repo>
cd stellarium-ai
cp .env.example .env
# Заполните .env своими значениями
```

### 2. Запуск через Docker (рекомендуется)

```bash
docker-compose up -d
```

### 3. Локальная разработка (polling-режим)

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить PostgreSQL и Redis (или использовать SQLite)
# Запустить бот в режиме polling (без webhook)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Переменные окружения

| Переменная | Описание | Обязательно |
|-----------|----------|-------------|
| `BOT_TOKEN` | Токен Telegram-бота от @BotFather | ✅ |
| `OPENAI_API_KEY` | Ключ OpenAI API (GPT-4o) | Рекомендуется |
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `REDIS_URL` | Redis connection string | Рекомендуется |
| `WEBHOOK_URL` | URL сервера для webhook (пусто = polling) | Для продакшна |
| `SECRET_KEY` | Секрет для валидации WebApp | ✅ |

## Команды бота

| Команда | Описание | Тариф |
|---------|----------|-------|
| `/start` | Регистрация и создание карты | Все |
| `/chart` | Натальная карта + ИИ-анализ | Все |
| `/today` | Прогноз на сегодня | Все |
| `/week` | Прогноз на неделю | Pro |
| `/compatibility` | Совместимость с партнёром | Все |
| `/ask` | Вопрос астрологу | Все (лимит) |
| `/transit` | Текущие транзиты | Pro |
| `/settings` | Настройки и подписка | Все |
| `/privacy` | Политика конфиденциальности | Все |
| `/my_data` | Мои данные (GDPR) | Все |
| `/delete_data` | Удалить все данные | Все |
| `/export_data` | Экспорт данных (JSON) | Все |

## Тарифы

| Тариф | Цена | Возможности |
|-------|------|-------------|
| 🆓 Free | Бесплатно | Карта + 5 вопросов/день |
| ⭐ Pro | 50 Stars (~99₽) | Всё + безлимит + недельные прогнозы |
| 🔮 Oracle | 150 Stars (~299₽) | Всё Pro + бизнес-астрология + годовые прогнозы |

## Архитектура

```
stellarium-ai/
├── app/
│   ├── main.py              # FastAPI + aiogram entry point
│   ├── config.py            # Настройки
│   ├── bot/
│   │   ├── handlers/        # Обработчики команд
│   │   ├── keyboards/       # Inline клавиатуры
│   │   ├── middlewares/     # Database middleware
│   │   └── states/          # FSM состояния
│   ├── webapp/              # Telegram Mini App
│   │   ├── routes.py        # FastAPI роуты
│   │   ├── templates/       # HTML
│   │   └── static/          # CSS + JS
│   ├── astrology/
│   │   ├── calculations.py  # Swiss Ephemeris расчёты
│   │   ├── ai_interpreter.py # GPT-4o промпты
│   │   └── chart_renderer.py # SVG генерация
│   └── database/
│       ├── models.py        # SQLAlchemy модели
│       ├── crud.py          # DB операции
│       └── connection.py    # Подключение
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Стек технологий

- **Python 3.11+** / **aiogram 3.x** / **FastAPI**
- **PostgreSQL 15** / **Redis 7**
- **pyswisseph** — Swiss Ephemeris
- **OpenAI GPT-4o** — ИИ-интерпретации
- **Nominatim OSM API** — геокодирование
- **SVG** — генерация натальных карт

## Деплой

Полная инструкция по деплою: [deployment_guide.md](deployment_guide.md)

## Лицензия

MIT
