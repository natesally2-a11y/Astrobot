# Deployment Guide

This guide walks through deploying Stellarium AI to a production server with
Docker Compose, nginx as a TLS terminator and a Telegram webhook.

## 1. Prerequisites

- Linux server with a public IP and a domain name (e.g. `stellarium.example.com`).
- Docker 24+ and Docker Compose v2.
- Telegram bot token from [@BotFather](https://t.me/BotFather).
- OpenAI API key.
- A Telegram Mini App URL configured in BotFather (`/newapp`).

## 2. Configure environment

```bash
git clone <your-fork> stellarium-ai
cd stellarium-ai
cp .env.example .env
$EDITOR .env
```

Required values:

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | from @BotFather |
| `BOT_USERNAME` | bot's username without `@` |
| `WEBHOOK_URL` | `https://stellarium.example.com` (used for webhook + Mini App) |
| `WEBHOOK_SECRET` | random 32-character string |
| `USE_WEBHOOK` | `true` in production |
| `OPENAI_API_KEY` | OpenAI key |
| `DATABASE_URL` | provided by docker-compose (`postgresql+asyncpg://...`) |
| `REDIS_URL` | provided by docker-compose |
| `SECRET_KEY` | random 32+ chars |

## 3. TLS

The Telegram Bot API only accepts webhooks on HTTPS.  The simplest setup is
Let's Encrypt with [certbot](https://certbot.eff.org/):

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d stellarium.example.com
```

## 4. nginx

Copy `nginx.conf.example` to `/etc/nginx/sites-available/stellarium.conf`,
update domain names and certificate paths, then enable:

```bash
sudo ln -s /etc/nginx/sites-available/stellarium.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 5. Launch

```bash
docker compose up -d --build
docker compose logs -f bot
```

The bot service will:

1. Apply database schema (`init_db`).
2. Set Telegram commands.
3. Configure the Mini App menu button.
4. Register the webhook (if `USE_WEBHOOK=true`) or start polling.

Health endpoints:

- `GET /health` — process is up.
- `GET /api/healthz` — REST API is reachable.

## 6. Mini App configuration (BotFather)

In `@BotFather`:

```
/mybots → <your bot> → Bot Settings → Menu Button → Configure menu button
        → URL: https://stellarium.example.com/app
        → Text: 🌌 Stellarium
```

Then `/newapp` to register a Mini App and link it to the same URL.

## 7. Telegram Stars payouts

Enable Stars in BotFather (`Bot Settings → Payments`) and read
[official docs](https://core.telegram.org/bots/payments-stars) for payout
flow.  Refund requests are processed via `refundStarPayment`.

## 8. Backups

The compose stack ships a `postgres_data` volume.  Snapshot it via:

```bash
docker compose exec db pg_dump -U stellarium stellarium | gzip > stellarium_$(date +%F).sql.gz
```

Schedule with cron or your provider's snapshot feature.

## 9. Updating

```bash
git pull
docker compose build bot
docker compose up -d bot
```

Aiogram 3.x and Pydantic v2 are pinned in `requirements.txt`.  Bump versions
with care and run `pytest`/manual smoke tests before pushing.

## 10. Observability (optional)

- Send logs to journald or Loki via the standard Docker logging driver.
- Hook Sentry by setting the SDK and an env var (out of MVP scope).
