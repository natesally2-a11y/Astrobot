# Deployment Guide

## 1. Подготовка BotFather

1. Создайте или откройте бота в BotFather.
2. Включите inline mode командой `/setinline`.
3. Настройте команды через BotFather или дайте приложению выполнить `set_my_commands` на старте.
4. Настройте кнопку Mini App:
   - URL: `https://yourdomain.com/app`
   - название: `Stellarium AI`
5. Не храните токен бота в git. Передавайте его через `BOT_TOKEN`.

## 2. Переменные окружения

Создайте `.env` на основе `.env.example`:

```env
BOT_TOKEN=...
WEBHOOK_URL=https://yourdomain.com/webhook
WEBAPP_URL=https://yourdomain.com/app
BOT_USERNAME=stellarium_ai_bot
OPENAI_API_KEY=...
DATABASE_URL=postgresql+asyncpg://stellarium:stellarium@db:5432/stellarium
REDIS_URL=redis://redis:6379/0
SECRET_KEY=...
ENVIRONMENT=production
```

## 3. Docker Compose

### Локальный режим без публичного домена

Оставьте `WEBHOOK_URL` пустым и запустите backend вместе с polling-ботом:

```bash
docker compose --profile polling up --build -d
docker compose logs -f api bot-polling
```

### Production webhook-режим

Укажите публичный HTTPS `WEBHOOK_URL` и запустите только backend:

```bash
docker compose up --build -d
docker compose logs -f api
```

Backend поднимет таблицы БД автоматически на старте. Инициализация БД делает несколько
повторных попыток, чтобы дождаться PostgreSQL после `docker compose up`.

## 4. Nginx

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    location /webhook {
        proxy_pass http://127.0.0.1:8000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /app {
        proxy_pass http://127.0.0.1:8000/app;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000/api;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /static {
        proxy_pass http://127.0.0.1:8000/static;
    }

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
}
```

## 5. Проверки после деплоя

```bash
curl https://yourdomain.com/health
```

В Telegram:

1. `/start` — пройти регистрацию и согласие.
2. `/chart` — получить SVG-карту и AI-анализ.
3. `/settings` — открыть Mini App и проверить тарифы.
4. Нажать Pro/Oracle и проверить инвойс Stars.

Если бот не отвечает локально, убедитесь, что запущен service `bot-polling`. Если бот не
отвечает в production, проверьте `WEBHOOK_URL`, HTTPS-сертификат и логи `api`.
Mini App внутри Telegram открывается только с публичного HTTPS URL, настроенного в BotFather.

## 6. OpenAI fallback

Если `OPENAI_API_KEY` не задан, бот отвечает локальными шаблонами. Это полезно для тестового
деплоя, но для продакшена ключ нужен для полноценного AI-опыта.
