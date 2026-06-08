# Stellarium AI

MVP Telegram bot + Mini App for personalized astrology, subscriptions via Telegram Stars, and GDPR/FZ-152-friendly data management flows.

## Features

- aiogram 3.x bot with onboarding and birth data collection
- FastAPI backend with webhook endpoint and Mini App UI
- Swiss Ephemeris based natal chart and transit calculations
- OpenAI-powered interpretations with deterministic fallback mode
- Telegram Stars subscriptions for Pro and Oracle plans
- GDPR/FZ-152 commands: `/privacy`, `/my_data`, `/export_data`, `/delete_data`
- Inline mode for viral sharing and simple sign-based previews
- Dockerized deployment with PostgreSQL 15 and Redis

## Quick start

1. Copy env template:
   ```bash
   cp .env.example .env
   ```
2. Fill in `.env` with your real `BOT_TOKEN`, `OPENAI_API_KEY`, and public `APP_BASE_URL`.
3. Start the stack:
   ```bash
   docker compose up --build
   ```
4. Open FastAPI docs at `http://localhost:8000/docs`.
5. Point your Telegram bot webhook to `https://yourdomain.com/webhook`.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Demo data

If `ENABLE_DEMO_DATA=true`, the application creates a demo profile for Mini App previews. You can also seed data manually:

```bash
python3 -m app.seed_demo
```

Demo Telegram ID: `777000`

## Additional docs

- `privacy_policy.md`
- `terms_of_service.md`
- `deployment_guide.md`
- `api_documentation.md`
