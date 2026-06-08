# Stellarium AI — Руководство по развёртыванию

Документ описывает запуск Stellarium AI в трёх режимах:

1. **Локальный dev** (SQLite + long-polling) — для разработчиков.
2. **Docker Compose** (PostgreSQL + Redis + uvicorn) — для тестового стенда.
3. **Production с Nginx и webhook** — для боевого окружения.

## 0. Предварительные требования

| Компонент | Версия |
|-----------|--------|
| Python    | 3.11+  |
| Docker    | 24+    |
| PostgreSQL | 15+ (для prod) |
| Nginx     | 1.24+ (для prod) |
| Свободный домен с HTTPS | обязательно для Mini App и webhook |
| Bot Token | от @BotFather |
| OpenAI API key | для AI-интерпретаций (опционально) |

> Mini App работает только по HTTPS — это требование Telegram.

## 1. Локальный запуск (dev)

```bash
git clone <repo> stellarium && cd stellarium
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# отредактируйте BOT_TOKEN и (при наличии) OPENAI_API_KEY

# Вариант A — только бот в polling-режиме
python run_bot.py

# Вариант B — FastAPI + bot polling (Mini App доступен на :8000/app)
uvicorn app.main:app --reload
```

Для тестирования Mini App локально можно использовать ngrok:

```bash
ngrok http 8000
# Скопируйте https-URL в .env -> WEBAPP_PUBLIC_URL
```

## 2. Docker Compose

```bash
cp .env.example .env
# заполните BOT_TOKEN, OPENAI_API_KEY, SECRET_KEY, WEBAPP_PUBLIC_URL
docker compose up -d --build
docker compose logs -f app
```

Compose поднимает три контейнера: `app`, `db` (Postgres 15), `redis` (Redis 7).
Том `pgdata` хранит базу. Папка `./ephe` (для swiss-ephemeris файлов)
монтируется в `/app/ephe`. Скачайте файлы из
<https://www.astro.com/ftp/swisseph/ephe/> при необходимости повышенной
точности; иначе используется встроенная Moshier-модель.

## 3. Production: Nginx + webhook

1. Установите Docker и Nginx, выпустите TLS-сертификат (например, через
   Certbot/Let's Encrypt).
2. В `.env` укажите:

   ```env
   WEBHOOK_URL=https://yourdomain.com
   WEBHOOK_SECRET=<длинная случайная строка>
   WEBAPP_PUBLIC_URL=https://yourdomain.com
   DATABASE_URL=postgresql+asyncpg://stellarium:strongpass@db:5432/stellarium
   ```

3. Запустите `docker compose up -d`.
4. Настройте Nginx:

   ```nginx
   server {
       listen 443 ssl http2;
       server_name yourdomain.com;

       ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

       client_max_body_size 5m;

       location /webhook {
           proxy_pass http://127.0.0.1:8000/webhook;
           proxy_set_header X-Forwarded-For $remote_addr;
           proxy_set_header X-Telegram-Bot-Api-Secret-Token $http_x_telegram_bot_api_secret_token;
       }

       location /app {
           proxy_pass http://127.0.0.1:8000/app;
       }

       location /api/ {
           proxy_pass http://127.0.0.1:8000/api/;
       }

       location /static/ {
           proxy_pass http://127.0.0.1:8000/static/;
       }
   }

   server {
       listen 80;
       server_name yourdomain.com;
       return 301 https://$host$request_uri;
   }
   ```

5. Перезагрузите Nginx: `sudo nginx -t && sudo systemctl reload nginx`.
6. При первом запуске приложение само вызовет `setWebhook`. Проверьте:

   ```bash
   curl "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"
   ```

7. У BotFather пропишите Mini App URL для команды «Меню»:
   `https://yourdomain.com/app`.

## 4. Telegram Stars — настройка

1. У BotFather включите `/setpayments` и выберите Stars.
2. Убедитесь, что бот опубликован (`/setprivacy`, `/setjoingroups`).
3. Платежи приходят в виде `pre_checkout_query` и `successful_payment`,
   которые уже обрабатываются модулями `app/bot/handlers/payments.py`.

## 5. Управление базой

В составе репозитория нет миграций (для MVP схема создаётся через
`SQLAlchemy.metadata.create_all`). Для production используйте Alembic:

```bash
alembic init alembic
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## 6. Бэкапы и мониторинг

- Раз в сутки выгружайте `pg_dump`:
  `docker exec stellarium_db pg_dump -U stellarium stellarium > backup.sql`.
- Мониторьте здоровье через `GET /health` (HTTP 200 + `{"status":"ok"}`).
- Логи бота пишутся в stdout (формат loguru), их легко собирать в Loki/ELK.

## 7. Откат

```bash
docker compose down
git checkout <previous-tag>
docker compose up -d --build
```
