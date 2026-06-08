# Руководство по деплою Stellarium AI

## Требования

- VPS/сервер с Linux (Ubuntu 22.04 рекомендуется)
- Docker + Docker Compose
- Доменное имя с SSL (для webhook)
- Telegram Bot Token (от @BotFather)
- OpenAI API Key (опционально, есть fallback)

---

## Шаг 1: Подготовка сервера

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установить Docker Compose
sudo apt install docker-compose-plugin -y

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

## Шаг 2: Клонировать репозиторий

```bash
git clone <your-repo-url> stellarium-ai
cd stellarium-ai
```

## Шаг 3: Настроить переменные окружения

```bash
cp .env.example .env
nano .env
```

Заполните обязательные поля:
```env
BOT_TOKEN=8730150448:AAF2WIWbalTieFVb2lc1kdtGIAkrtflgLvs
WEBHOOK_URL=https://yourdomain.com
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://stellarium:StrongPassword@db:5432/stellarium
DB_PASSWORD=StrongPassword
SECRET_KEY=random-64-char-string
```

Сгенерировать SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Шаг 4: Настройка Nginx с SSL

Установить Certbot:
```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

Настроить Nginx (`/etc/nginx/sites-available/stellarium`):
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Bot webhook
    location /webhook {
        proxy_pass http://localhost:8000/webhook;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Mini App
    location /app {
        proxy_pass http://localhost:8000/app;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
    
    # API
    location /api {
        proxy_pass http://localhost:8000/api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
    
    # Static files
    location /static {
        proxy_pass http://localhost:8000/static;
    }
}
```

Получить SSL-сертификат:
```bash
sudo certbot --nginx -d yourdomain.com
sudo ln -s /etc/nginx/sites-available/stellarium /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Шаг 5: Запустить приложение

```bash
docker-compose up -d --build
```

Проверить статус:
```bash
docker-compose ps
docker-compose logs -f bot
```

## Шаг 6: Настроить BotFather

1. Открыть @BotFather в Telegram
2. `/mybots` → выбрать бота
3. **Bot Settings** → **Menu Button** → установить URL мини-приложения: `https://yourdomain.com/app`
4. **Bot Settings** → **Inline Mode** → включить
5. **Bot Settings** → **Payments** → включить Telegram Stars

## Шаг 7: Настроить команды бота

В @BotFather:
```
/setcommands
```
Вставить:
```
start - Начать и создать карту
chart - Натальная карта
today - Прогноз на сегодня
week - Прогноз на неделю (Pro)
compatibility - Совместимость
ask - Задать вопрос
transit - Транзиты (Pro)
settings - Настройки
help - Справка
privacy - Конфиденциальность
my_data - Мои данные
delete_data - Удалить данные
export_data - Экспорт данных
```

## Обновление

```bash
git pull
docker-compose up -d --build bot
```

## Мониторинг

```bash
# Логи в реальном времени
docker-compose logs -f bot

# Использование ресурсов
docker stats

# Проверка здоровья
curl https://yourdomain.com/health
```

## Бэкап базы данных

```bash
# Создать бэкап
docker-compose exec db pg_dump -U stellarium stellarium > backup_$(date +%Y%m%d).sql

# Восстановить
docker-compose exec -T db psql -U stellarium stellarium < backup.sql
```

---

## Локальная разработка (без Docker)

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить PostgreSQL и Redis локально или через docker
docker run -d -p 5432:5432 -e POSTGRES_DB=stellarium -e POSTGRES_USER=stellarium -e POSTGRES_PASSWORD=secret postgres:15
docker run -d -p 6379:6379 redis:7

# Изменить DATABASE_URL в .env
DATABASE_URL=postgresql+asyncpg://stellarium:secret@localhost:5432/stellarium
REDIS_URL=redis://localhost:6379

# Запустить в режиме polling (без webhook)
WEBHOOK_URL= python -m uvicorn app.main:app --reload
```
