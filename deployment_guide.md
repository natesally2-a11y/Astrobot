# Deployment Guide: Stellarium AI

## 1) Предварительные требования

- Docker + Docker Compose
- Домен и TLS-сертификат для production
- Telegram-бот, созданный через BotFather

## 2) Настройка окружения

```bash
cp .env.example .env
```

Заполните:

- `BOT_TOKEN`
- `APP_BASE_URL` (например, `https://yourdomain.com`)
- `OPENAI_API_KEY`
- `SECRET_KEY`

## 3) Локальный запуск

```bash
docker compose up --build
```

Проверка:

- `GET http://localhost:8000/api/health`
- `http://localhost:8000/app`

## 4) Production (пример с Nginx)

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
}
```

## 5) Миграции БД

В MVP используется автоматическое создание таблиц при старте (`create_all`).  
Для production-релиза рекомендуется добавить Alembic-миграции.

## 6) Безопасность и комплаенс

- не храните токены и ключи в git;
- включите регулярное резервное копирование PostgreSQL;
- храните тексты privacy/terms в актуальном состоянии;
- соблюдайте требования Telegram для ботов и mini apps.

