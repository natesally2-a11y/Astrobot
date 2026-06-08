# Руководство по развёртыванию Stellarium AI

## Требования

- VPS с Ubuntu 22.04+ (минимум 1 CPU, 2 GB RAM)
- Доменное имя с SSL-сертификатом
- Docker и Docker Compose
- Telegram Bot Token (от @BotFather)
- OpenAI API Key

## Шаг 1: Подготовка сервера

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

## Шаг 2: Получение SSL-сертификата

```bash
sudo certbot --nginx -d yourdomain.com
```

## Шаг 3: Клонирование проекта

```bash
cd /opt
git clone <repo-url> stellarium-ai
cd stellarium-ai
```

## Шаг 4: Настройка переменных окружения

```bash
cp .env.example .env
nano .env
```

Заполните:
```
BOT_TOKEN=8730150448:AAF2WIWbalTieFVb2lc1kdtGIAkrtflgLvs
WEBHOOK_URL=https://yourdomain.com
OPENAI_API_KEY=sk-your-key-here
DATABASE_URL=postgresql+asyncpg://stellarium:stellarium@db:5432/stellarium
REDIS_URL=redis://redis:6379
SECRET_KEY=your-random-secret-key
WEBAPP_URL=https://yourdomain.com/app
```

## Шаг 5: Настройка Nginx

```bash
sudo cp nginx.conf /etc/nginx/sites-available/stellarium
sudo ln -s /etc/nginx/sites-available/stellarium /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Отредактируйте `server_name` и пути к SSL-сертификатам.

## Шаг 6: Запуск

```bash
docker-compose up -d --build
```

## Шаг 7: Проверка

```bash
# Проверка контейнеров
docker-compose ps

# Логи бота
docker-compose logs -f bot

# Health check
curl https://yourdomain.com/health
```

## Шаг 8: Настройка бота в BotFather

1. Откройте @BotFather
2. Выберите бота
3. **Edit Bot** → установите описание и аватар
4. **Bot Settings** → **Inline Mode** → включите
5. **Bot Settings** → **Menu Button** → установите URL Mini App
6. **Payments** → настройте Telegram Stars

## Обновление

```bash
cd /opt/stellarium-ai
git pull
docker-compose up -d --build
```

## Мониторинг

```bash
# Логи в реальном времени
docker-compose logs -f

# Состояние базы данных
docker-compose exec db psql -U stellarium -c "SELECT count(*) FROM users;"

# Перезапуск
docker-compose restart bot
```

## Бэкапы

```bash
# Бэкап базы данных
docker-compose exec db pg_dump -U stellarium stellarium > backup_$(date +%Y%m%d).sql

# Восстановление
docker-compose exec -T db psql -U stellarium stellarium < backup.sql
```

## Устранение неполадок

| Проблема | Решение |
|----------|---------|
| Бот не отвечает | Проверьте логи: `docker-compose logs bot` |
| Ошибка БД | Убедитесь, что PostgreSQL запущен: `docker-compose ps` |
| Webhook не работает | Проверьте SSL и Nginx конфигурацию |
| OpenAI ошибки | Проверьте API ключ и баланс аккаунта |
