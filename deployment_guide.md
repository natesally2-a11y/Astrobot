# Stellarium AI — Deployment Guide

## 1. Подготовка

1. Установите Docker и Docker Compose.
2. Скопируйте `.env.example` в `.env`:

```bash
cp .env.example .env
```

3. Заполните переменные:
- `BOT_TOKEN`
- `WEBHOOK_URL`
- `WEBAPP_BASE_URL`
- `OPENAI_API_KEY`
- `SECRET_KEY`

## 2. Запуск через Docker Compose

```bash
docker compose up --build -d
```

Проверка:

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

## 3. Webhook Telegram

1. Убедитесь, что `WEBHOOK_URL` публично доступен по HTTPS.
2. После старта приложение автоматически установит webhook на:

`https://<domain>/webhook`

## 4. Nginx reverse proxy (пример)

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    location /webhook {
        proxy_pass http://127.0.0.1:8000/webhook;
    }

    location /app {
        proxy_pass http://127.0.0.1:8000/app;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000/api;
    }
}
```

## 5. Альтернативный запуск polling (локально)

```bash
python -m app.bot.run_polling
```

## 6. Рекомендации по продакшену

- Использовать отдельный PostgreSQL/Redis с backup;
- хранить секреты в безопасном vault/secret manager;
- включить мониторинг логов и алерты по 5xx;
- добавить миграции (Alembic) перед масштабированием.
