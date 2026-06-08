# Руководство по развёртыванию Stellarium AI

## Требования

- Docker и Docker Compose
- Домен с SSL-сертификатом (для webhook и Mini App)
- Telegram Bot Token (от [@BotFather](https://t.me/BotFather))
- OpenAI API Key

## Быстрый старт (Docker)

### 1. Клонирование и настройка

```bash
git clone <repository-url>
cd stellarium-ai
cp .env.example .env
```

### 2. Заполните `.env`

```env
BOT_TOKEN=your_bot_token_from_botfather
WEBHOOK_URL=https://yourdomain.com
WEBAPP_URL=https://yourdomain.com/app
OPENAI_API_KEY=sk-...
SECRET_KEY=generate-random-32-char-string
```

### 3. Запуск

```bash
docker compose up -d --build
```

Сервис будет доступен на порту `8000`.

### 4. Настройка Nginx

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location /webhook {
        proxy_pass http://127.0.0.1:8000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /app {
        proxy_pass http://127.0.0.1:8000/app;
        proxy_set_header Host $host;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

### 5. Настройка бота в BotFather

1. `/setdomain` — укажите `yourdomain.com`
2. `/setmenubutton` — URL: `https://yourdomain.com/app`
3. Включите inline mode: `/setinline` — placeholder: `daily Virgo`

## Локальная разработка (Polling)

Без webhook можно запустить бота в режиме polling:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Запустите PostgreSQL и Redis локально или через docker compose up db redis -d

export BOT_TOKEN=your_token
export DATABASE_URL=postgresql+asyncpg://stellarium:stellarium@localhost:5432/stellarium
export OPENAI_API_KEY=sk-...

# Терминал 1: API + webhook endpoint
uvicorn app.main:app --reload --port 8000

# Терминал 2: Polling
python -m app.polling
```

## Проверка работоспособности

```bash
curl https://yourdomain.com/health
# {"status":"ok","service":"stellarium-ai"}
```

## Переменные окружения

| Переменная | Описание | Обязательно |
|------------|----------|-------------|
| `BOT_TOKEN` | Токен Telegram-бота | Да |
| `WEBHOOK_URL` | URL сервера (без /webhook) | Для prod |
| `WEBAPP_URL` | URL мини-приложения | Да |
| `OPENAI_API_KEY` | Ключ OpenAI | Да |
| `DATABASE_URL` | PostgreSQL connection string | Да |
| `REDIS_URL` | Redis URL | Нет |
| `SECRET_KEY` | Ключ для WebApp validation | Да |
| `PRO_STARS` | Цена Pro в Stars (default: 50) | Нет |
| `ORACLE_STARS` | Цена Oracle в Stars (default: 150) | Нет |

## Обновление

```bash
git pull
docker compose up -d --build
```

## Бэкап базы данных

```bash
docker compose exec db pg_dump -U stellarium stellarium > backup.sql
```

## Безопасность

- **Никогда** не коммитьте `.env` с реальными токенами
- Используйте HTTPS для webhook и Mini App
- Регулярно обновляйте зависимости
- Ограничьте доступ к PostgreSQL только из Docker-сети
