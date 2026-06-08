# Deployment Guide for Stellarium AI

## 1. Configure environment

```bash
cp .env.example .env
```

Fill in at minimum:

- `BOT_TOKEN`
- `OPENAI_API_KEY`
- `APP_BASE_URL=https://yourdomain.com`
- `WEBHOOK_URL=https://yourdomain.com/webhook`
- `DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/stellarium`
- `SECRET_KEY=<strong random value>`

## 2. Launch services

```bash
docker compose up --build -d
```

## 3. Health checks

- `GET /health` must return `{"status":"ok"}`
- `GET /docs` should show FastAPI docs
- Open `https://yourdomain.com/app?telegram_id=777000` to preview demo data

## 4. Security checklist

- never commit `.env`
- rotate the bot token if it was shared in insecure channels
- add rate limiting before public launch
- review privacy/legal texts with counsel
