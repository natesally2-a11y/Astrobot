# 🌟 Stellarium AI — Персональный ИИ-Астролог в Telegram

Telegram-бот + Mini App для персонализированных астрологических прогнозов на основе натальной карты.

## Возможности

- **Натальная карта** — точный расчёт через Swiss Ephemeris с SVG-визуализацией
- **ИИ-интерпретация** — GPT-4 анализирует карту как профессиональный астролог
- **Персональные прогнозы** — ежедневные и недельные на основе транзитов
- **Совместимость** — синастрия двух карт
- **Подписки через Telegram Stars** — Pro (50 Stars) и Oracle (150 Stars)
- **Mini App** — интерактивная карта и управление профилем
- **Inline Mode** — вирусное распространение через быстрые прогнозы
- **GDPR / ФЗ-152** — полное соответствие законодательству

## Технический стек

| Компонент | Технология |
|-----------|-----------|
| Язык | Python 3.11+ |
| Bot Framework | aiogram 3.x |
| Web Framework | FastAPI |
| База данных | PostgreSQL 15 |
| Кэш | Redis 7 |
| Астрология | Swiss Ephemeris (pyswisseph) |
| ИИ | OpenAI GPT-4 |
| Геокодинг | Nominatim OSM API |
| Деплой | Docker Compose |

## Быстрый старт

### 1. Клонирование

```bash
git clone <repo-url>
cd stellarium-ai
```

### 2. Настройка переменных окружения

```bash
cp .env.example .env
# Отредактируйте .env — укажите BOT_TOKEN и OPENAI_API_KEY
```

### 3. Запуск через Docker Compose

```bash
docker-compose up -d
```

### 4. Локальная разработка (без Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Запустить PostgreSQL и Redis локально, затем:
python run_polling.py
```

### 5. Webhook-режим (продакшен)

```bash
# В .env укажите WEBHOOK_URL=https://yourdomain.com
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Команды бота

| Команда | Описание | Доступ |
|---------|----------|--------|
| `/start` | Регистрация и ввод данных | Все |
| `/chart` | Натальная карта + ИИ-анализ | Все |
| `/today` | Прогноз на сегодня | Все (кратко) / Pro (подробно) |
| `/week` | Прогноз на неделю | Pro / Oracle |
| `/compatibility` | Совместимость | Все (лимит) / Pro (безлимит) |
| `/ask <вопрос>` | Вопрос астрологу | 5/день бесплатно / Pro безлимит |
| `/transit` | Анализ транзитов | Pro / Oracle |
| `/settings` | Настройки и подписка | Все |
| `/help` | Справка | Все |
| `/privacy` | Политика конфиденциальности | Все |
| `/my_data` | Просмотр данных | Все |
| `/export_data` | Экспорт в JSON | Все |
| `/delete_data` | Удаление аккаунта | Все |

## Подписки

| План | Цена | Stars | Возможности |
|------|------|-------|-------------|
| Бесплатный | 0₽ | 0 | Карта, базовый анализ, 5 вопросов/день |
| Stellarium Pro | 99₽/мес | 50 | Подробные прогнозы, безлимит, совместимость |
| Космический Оракул | 299₽/мес | 150 | Всё из Pro + бизнес-астрология, годовые прогнозы |

## Структура проекта

```
stellarium-ai/
├── app/
│   ├── bot/
│   │   ├── handlers/       # Обработчики команд
│   │   ├── keyboards/      # Inline-клавиатуры
│   │   ├── middlewares/     # GDPR, подписки
│   │   └── utils/           # Геокодинг
│   ├── webapp/
│   │   ├── api/             # REST API для Mini App
│   │   ├── static/          # CSS, JS
│   │   └── templates/       # HTML
│   ├── astrology/
│   │   ├── calculations.py  # Swiss Ephemeris
│   │   ├── ai_interpreter.py # GPT промпты
│   │   └── chart_renderer.py # SVG карт
│   ├── database/
│   │   ├── models.py        # SQLAlchemy модели
│   │   ├── session.py       # Сессия БД
│   │   └── crud.py          # CRUD операции
│   ├── config.py            # Настройки
│   └── main.py              # FastAPI + webhook
├── run_polling.py           # Polling-режим
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
└── .env.example
```

## Переменные окружения

| Переменная | Описание | Обязательна |
|-----------|----------|:-----------:|
| `BOT_TOKEN` | Токен Telegram бота | ✅ |
| `OPENAI_API_KEY` | Ключ OpenAI API | ✅ |
| `DATABASE_URL` | URL PostgreSQL | ✅ |
| `REDIS_URL` | URL Redis | ✅ |
| `WEBHOOK_URL` | URL для webhook | Для продакшена |
| `SECRET_KEY` | Ключ для WebApp валидации | Рекомендуется |
| `WEBAPP_URL` | URL Mini App | Для Mini App |
