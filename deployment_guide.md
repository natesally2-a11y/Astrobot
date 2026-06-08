# Руководство по деплою Stellarium AI

Пошаговая инструкция запуска бота и Mini App в продакшене.

## 0. Предварительные требования

- Сервер с Docker и Docker Compose (или Python 3.11+, PostgreSQL 15, Redis).
- Домен с валидным SSL-сертификатом (нужен для вебхука и Mini App).
- Токен бота от [@BotFather](https://t.me/BotFather).
- Ключ OpenAI API.

## 1. Создание и настройка бота в BotFather

1. `/newbot` → задайте имя и username (например, `stellarium_ai_bot`).
2. Сохраните **BOT_TOKEN**.
3. `/setdomain` → укажите ваш домен (нужно для Telegram Login/WebApp).
4. `/mybots → Bot Settings → Menu Button` → задайте URL Mini App:
   `https://yourdomain.com/app` и текст кнопки «Открыть приложение».
5. `/setinline` → включите inline-режим, задайте плейсхолдер
   (например: `daily Лев`).
6. Платежи Telegram Stars включены по умолчанию (валюта `XTR`, провайдер не
   требуется).

## 2. Переменные окружения

```bash
cp .env.example .env
```

Заполните как минимум:

```ini
BOT_TOKEN=123456:ABC...           # из BotFather
OPENAI_API_KEY=sk-...
WEBHOOK_BASE_URL=https://yourdomain.com
WEBHOOK_SECRET=<случайная-строка>
BOT_MODE=webhook                  # webhook для прода, polling для дева
SECRET_KEY=<случайная-строка>
BOT_USERNAME=stellarium_ai_bot
DATABASE_URL=postgresql+asyncpg://stellarium:stellarium@db:5432/stellarium
REDIS_URL=redis://redis:6379/0
```

> Сгенерировать секрет: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

## 3. Запуск через Docker Compose

```bash
docker compose up -d --build
docker compose logs -f app
```

Поднимутся три сервиса: `app` (FastAPI+бот), `db` (PostgreSQL), `redis`.
Таблицы создаются автоматически при первом старте. Для ручного создания схемы
используйте `schema.sql`.

В режиме `BOT_MODE=webhook` приложение само вызовет `setWebhook` на
`${WEBHOOK_BASE_URL}/webhook` с секретным токеном. В режиме `polling` домен не
нужен — удобно для быстрой проверки.

## 4. Nginx (reverse proxy + SSL)

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate     /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location /webhook { proxy_pass http://localhost:8000/webhook; }
    location /app     { proxy_pass http://localhost:8000/app; }
    location /api     { proxy_pass http://localhost:8000/api; }
    location /static  { proxy_pass http://localhost:8000/static; }
    location /health  { proxy_pass http://localhost:8000/health; }

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Бесплатный сертификат можно получить через Let's Encrypt (`certbot`).

## 5. Проверка работоспособности

```bash
curl https://yourdomain.com/health        # {"status":"ok",...}
curl https://yourdomain.com/app            # HTML мини-приложения
```

В Telegram: откройте бота → `/start` → пройдите онбординг → `/chart`.
Проверьте кнопку Menu (Mini App) и inline (`@stellarium_ai_bot daily Лев`).

## 6. Webhook вручную (опционально)

Приложение управляет вебхуком само, но при необходимости:

```bash
curl "https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=https://yourdomain.com/webhook&secret_token=$WEBHOOK_SECRET"
curl "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"
```

## 7. Эфемериды Swiss Ephemeris

По умолчанию используется встроенная эфемерида **Moshier** — внешние файлы
данных не нужны. Для повышенной точности можно подключить файлы `.se1`
(положив их в каталог `ephe/` и вызвав `swe.set_ephe_path`), но для MVP это не
требуется.

## 8. Обновление

```bash
git pull
docker compose up -d --build
```

## 9. Резервное копирование

```bash
docker compose exec db pg_dump -U stellarium stellarium > backup_$(date +%F).sql
```

## 10. Траблшутинг

- **Бот не отвечает (webhook):** проверьте `getWebhookInfo`, корректность
  `WEBHOOK_SECRET`, доступность домена по HTTPS.
- **Mini App не открывается:** проверьте, что URL в Menu Button совпадает с
  `${WEBHOOK_BASE_URL}/app`, и что домен задан в `/setdomain`.
- **401 в Mini App API:** initData не проходит проверку — убедитесь, что
  `BOT_TOKEN` в приложении совпадает с токеном бота, открывающего Mini App.
- **Нет интерпретаций ИИ:** проверьте `OPENAI_API_KEY` и лимиты OpenAI (без
  ключа работает демо-режим с заглушками).
```
