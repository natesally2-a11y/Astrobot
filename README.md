# Stellarium AI

Stellarium AI is an MVP Telegram bot + Mini App for personalized astrology readings.

The product combines:

- Telegram bot flows powered by **aiogram 3**
- FastAPI webhook and Mini App backend
- PostgreSQL persistence with SQLAlchemy models
- Swiss Ephemeris based natal chart calculations with a deterministic local fallback
- OpenAI-based interpretation with safe fallback text when no API key is configured
- Telegram Stars invoices for Pro and Oracle subscriptions
- GDPR/FZ-152 data controls: consent, export, inspection and deletion

> Important: astrology readings are entertainment content and must not be used for medical, financial, legal or other critical decisions.

## Features

- `/start` onboarding with birth date, birth time, city search and mandatory data consent
- `/chart` natal chart SVG + AI reading
- `/today` personalized daily forecast
- `/week` and `/transit` premium forecasts
- `/compatibility` synastry-style partner reading
- `/ask` AI astrologer questions with free daily limit
- `/settings` Telegram Stars subscription invoices
- `/privacy`, `/my_data`, `/export_data`, `/delete_data`
- Inline mode examples:
  - `@stellarium_ai_bot daily Virgo`
  - `@stellarium_ai_bot compatibility Leo Scorpio`
- Mini App at `/app` with chart visualization and profile/subscription panels

## Quick start

```bash
cp .env.example .env
# edit .env and set BOT_TOKEN, WEBHOOK_URL, WEBAPP_URL, OPENAI_API_KEY, SECRET_KEY
docker compose up --build
```

The API exposes:

- `GET /health`
- `POST /webhook`
- `GET /app`
- `GET /api/profile`
- `GET /api/chart`
- `GET /api/chart.svg`
- `POST /api/reading`

## Environment variables

See `.env.example`.

Never commit real BotFather or OpenAI tokens. `BOT_TOKEN` must be configured in the deployment environment.

## Project structure

```text
app/
  bot/                 Telegram bot handlers, keyboards and FSM states
  webapp/              Mini App templates, static assets and API
  astrology/           Calculations, AI prompts and SVG renderer
  database/            SQLAlchemy models, session and CRUD helpers
  config.py            Pydantic settings
  main.py              FastAPI entrypoint
```

## Development checks

```bash
python3 -m compileall app tests
pytest
```

`pytest` requires dependencies from `requirements.txt`.
