# Deployment Guide for Stellarium AI

## 1. Подготовьте домен и Telegram Bot

1. Создайте бота через BotFather.
2. Получите новый `BOT_TOKEN`.
3. Настройте домен с HTTPS.
4. Укажите URL mini app и webhook в BotFather / Telegram settings.

> Если токен уже был показан в переписке или логах, его необходимо перевыпустить.

## 2. Подготовьте `.env`

```env
APP_ENV=prod
BASE_URL=https://yourdomain.com
WEBHOOK_URL=https://yourdomain.com
BOT_TOKEN=replace-with-fresh-token
OPENAI_API_KEY=replace-with-openai-key
DATABASE_URL=postgresql+asyncpg://stellarium:stellarium@db:5432/stellarium
REDIS_URL=redis://redis:6379/0
SECRET_KEY=replace-with-random-secret
```

## 3. Запуск через Docker Compose

```bash
docker compose up -d --build
```

Проверьте:

```bash
curl https://yourdomain.com/healthz
```

## 4. Nginx reverse proxy

Пример:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 5. Регистрация webhook

При старте приложения webhook выставляется автоматически, если заданы `BOT_TOKEN` и `WEBHOOK_URL`.

Ожидаемый endpoint:

```text
https://yourdomain.com/webhook
```

## 6. Telegram Mini App

Mini app открывается по адресу:

```text
https://yourdomain.com/app
```

Укажите этот URL в настройках бота и используйте HTTPS.

## 7. Production-рекомендации

- храните токены только в секретах окружения
- включите ежедневные бэкапы PostgreSQL
- лимитируйте доступ к БД и Redis по сети
- включите мониторинг healthcheck и логов webhook
- при необходимости валидируйте `initData` mini app на сервере

## 8. Smoke checklist

- `/start` запускает onboarding
- consent сохраняется
- карта строится и отображается в `/chart`
- `/today` отвечает прогнозом
- `/settings` показывает тарифы
- invoice для `XTR` создается
- `/app` открывает mini app
