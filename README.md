# Stellarium AI

Personal AI astrologer for Telegram — bot + Mini App, Swiss Ephemeris
calculations, GPT-powered interpretations, Telegram Stars subscriptions and
GDPR / 152-ФЗ compliance built in.

## Features

- Onboarding with calendar/time pickers and city geocoding
- Swiss Ephemeris-based natal chart (planets, houses, aspects)
- SVG chart renderer for the bot and the Mini App
- GPT interpretations: natal, daily, weekly, transits, compatibility, free Q&A
- Telegram Stars subscriptions (Free / Pro / Cosmic Oracle)
- Mini App with `initData` HMAC validation and REST API
- Inline mode (viral horoscopes and compatibility shortcuts)
- Referral system (`?start=ref_<id>` adds a week of Premium to the referrer)
- GDPR self-service: `/privacy`, `/my_data`, `/export_data`, `/delete_data`

## Quick start (Docker)

1. Create `.env` from the template:

   ```bash
   cp .env.example .env
   ```

2. Fill in `BOT_TOKEN`, `OPENAI_API_KEY` and (for production) `WEBHOOK_URL`.

3. Run the stack:

   ```bash
   docker compose up --build
   ```

4. Long polling starts automatically in development.  For production set
   `USE_WEBHOOK=true` and put nginx in front (see `nginx.conf.example`).

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit with your tokens
uvicorn app.main:app --reload
```

The FastAPI app boots the bot (long polling by default) and serves the Mini
App on `/app`.

## Documentation

- [`docs/privacy_policy.md`](docs/privacy_policy.md)
- [`docs/terms_of_service.md`](docs/terms_of_service.md)
- [`docs/deployment_guide.md`](docs/deployment_guide.md)
- [`docs/api_documentation.md`](docs/api_documentation.md)

## Project layout

```
stellarium-ai/
├── app/
│   ├── astrology/        Swiss Ephemeris, GPT interpreter, SVG renderer
│   ├── bot/              aiogram handlers, keyboards, middlewares
│   ├── database/         SQLAlchemy models + CRUD helpers
│   ├── webapp/           FastAPI Mini App + REST API + static
│   ├── config.py
│   └── main.py           ASGI entry point (bot + REST in one process)
├── docs/                 Markdown docs included in MVP
├── Dockerfile
├── docker-compose.yml
├── nginx.conf.example
├── requirements.txt
└── .env.example
```

⚠️ Astrological forecasts are entertainment only and must not be used as a
basis for medical, financial or legal decisions.
