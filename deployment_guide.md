# Deployment Guide

## 1. BotFather

1. Create or open the bot in BotFather.
2. Configure commands:
   - `start` — Приветствие и регистрация
   - `chart` — Показать натальную карту
   - `today` — Персональный прогноз на сегодня
   - `week` — Прогноз на неделю
   - `compatibility` — Совместимость
   - `ask` — Задать вопрос
   - `transit` — Важные транзиты
   - `settings` — Настройки и подписка
   - `privacy` — Политика конфиденциальности
   - `my_data` — Показать данные
   - `export_data` — Экспорт данных
   - `delete_data` — Удаление данных
3. Enable inline mode for viral queries.
4. Set the Mini App URL to `https://your-domain.example/app`.

## 2. Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Set:

```env
BOT_TOKEN=...
WEBHOOK_URL=https://your-domain.example/webhook
WEBAPP_URL=https://your-domain.example/app
OPENAI_API_KEY=...
SECRET_KEY=long-random-secret
DATABASE_URL=postgresql+asyncpg://stellarium:stellarium@db:5432/stellarium
REDIS_URL=redis://redis:6379/0
```

Do not commit `.env`.

## 3. Docker Compose

```bash
docker compose up --build -d
docker compose logs -f api
```

The app creates MVP tables automatically on startup. For production, introduce Alembic migrations before schema changes.

## 4. Nginx example

```nginx
server {
    listen 443 ssl;
    server_name your-domain.example;

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

    location /app/static {
        proxy_pass http://127.0.0.1:8000/app/static;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000/api;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
}
```

## 5. Health check

```bash
curl https://your-domain.example/health
```

Expected:

```json
{"status":"ok"}
```

## 6. Production checklist

- Use a real domain with HTTPS.
- Rotate all secrets before launch.
- Set a meaningful `NOMINATIM_USER_AGENT` with contact email.
- Review OpenAI data processing settings for your account.
- Publish links to `privacy_policy.md` and `terms_of_service.md`.
- Test Telegram Stars payments in the target bot.
- Configure backups for PostgreSQL.
