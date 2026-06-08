# Руководство по деплою Stellarium AI

Это пошаговая инструкция по развёртыванию бота и мини-приложения в production.

---

## 0. Предварительные требования

- Сервер с Linux (Ubuntu 22.04+), 1–2 vCPU, 2 ГБ RAM.
- Доменное имя с DNS, указывающим на сервер.
- Установленные Docker и Docker Compose.
- Токен бота от [@BotFather](https://t.me/BotFather).
- (Опционально) Ключ OpenAI API. Без него можно работать с `OPENAI_MOCK=true`.

## 1. Создание бота в BotFather

1. Откройте [@BotFather](https://t.me/BotFather) → `/newbot`, задайте имя и username.
2. Сохраните полученный **токен** — он пойдёт в `BOT_TOKEN`.
3. Включите **inline-режим**: `/setinline` → выберите бота → задайте placeholder
   (например, «Введите знак или два знака для совместимости»).
4. Привяжите Mini App: `/newapp` (или `/setmenubutton`) → укажите URL
   `https://ВАШ_ДОМЕН/app`.
5. (Опционально) Команды: `/setcommands` — бот выставит их и сам при старте.

## 2. Подготовка окружения

```bash
git clone <repo> stellarium-ai && cd stellarium-ai
cp .env.example .env
nano .env
```

Заполните как минимум:

```env
BOT_TOKEN=123456789:AA...
BOT_USERNAME=stellarium_ai_bot
RUN_MODE=webhook
WEBHOOK_URL=https://yourdomain.com
WEBHOOK_SECRET=<случайная строка>
WEBAPP_URL=https://yourdomain.com
OPENAI_API_KEY=sk-...
SECRET_KEY=<длинная случайная строка>
```

> `DATABASE_URL` и `REDIS_URL` уже настроены в `docker-compose.yml` на сервисы
> `db` и `redis`, их можно не менять.

## 3. Запуск через Docker Compose

```bash
docker compose up -d --build
docker compose logs -f app
```

Поднимутся три контейнера: `app` (FastAPI+бот), `db` (PostgreSQL), `redis`.
Таблицы создаются автоматически при старте.

Проверка: `curl http://localhost:8000/health` → `{"status":"ok",...}`.

## 4. Настройка Nginx + HTTPS

Telegram требует **HTTPS** для webhook и мини-приложений. Получите сертификат
(например, через Let's Encrypt / certbot) и настройте reverse-proxy:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location /webhook {
        proxy_pass http://127.0.0.1:8000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /app {
        proxy_pass http://127.0.0.1:8000/app;
        proxy_set_header Host $host;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000/api;
        proxy_set_header Host $host;
    }

    location /static {
        proxy_pass http://127.0.0.1:8000/static;
    }
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}
```

```bash
sudo certbot --nginx -d yourdomain.com
sudo systemctl reload nginx
```

## 5. Webhook

При `RUN_MODE=webhook` приложение само регистрирует webhook на старте
(`WEBHOOK_URL` + `WEBHOOK_PATH`) с секретным токеном. Проверить:

```bash
curl "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"
```

Должен отображаться ваш URL без ошибок.

## 6. Telegram Stars (платежи)

Платежи в Stars (валюта `XTR`) **не требуют** provider-токена и работают сразу.
Убедитесь, что бот соответствует требованиям Telegram к цифровым товарам.
Тестировать оплату можно реальными Stars (минимальные суммы).

## 7. Обновление

```bash
git pull
docker compose up -d --build
```

## 8. Резервное копирование БД

```bash
docker compose exec db pg_dump -U stellarium stellarium > backup_$(date +%F).sql
```

## 9. Локальная разработка без публичного домена

Используйте `RUN_MODE=polling` (по умолчанию) — webhook и HTTPS не нужны:

```bash
docker compose up --build
# или без Docker:
DATABASE_URL="sqlite+aiosqlite:///stellarium.db" OPENAI_MOCK=true uvicorn app.main:app --reload
```

Для теста Mini App локально удобно использовать туннель (ngrok/cloudflared),
указав его HTTPS-URL в `WEBAPP_URL` и в BotFather.

## 10. Чек-лист перед публичным запуском

- [ ] HTTPS настроен и валиден.
- [ ] `getWebhookInfo` без ошибок.
- [ ] Mini App открывается из меню бота.
- [ ] Заполнены `privacy_policy.md` и `terms_of_service.md` контактами оператора.
- [ ] Указан контактный e-mail в `NOMINATIM_USER_AGENT` (политика Nominatim).
- [ ] Включён inline-режим, проверена совместимость и дневной прогноз.
- [ ] Протестирован полный путь: /start → онбординг → /chart → /today → оплата.
```
