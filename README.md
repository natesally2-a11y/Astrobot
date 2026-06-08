# Stellarium AI (MVP)

Telegram bot + Mini App для персональной астрологии:

- точная натальная карта (дата/время/место рождения);
- ежедневные прогнозы на основе карты + транзитов;
- совместимость (синастрия);
- подписки через Telegram Stars (XTR);
- GDPR/ФЗ-152 команды управления данными;
- mini app для визуализации карты и истории.

## Технологии

- Python 3.11+
- aiogram 3.x
- FastAPI
- PostgreSQL 15
- Redis
- Swiss Ephemeris (`pyswisseph`)
- OpenAI API

## Структура проекта

```text
app/
  bot/
    handlers/
    keyboards/
    middlewares/
  astrology/
  database/
  webapp/
requirements.txt
docker-compose.yml
privacy_policy.md
terms_of_service.md
deployment_guide.md
api_documentation.md
```

## Быстрый старт

1. Скопируйте переменные окружения:

```bash
cp .env.example .env
```

2. Заполните `.env` (обязательно `BOT_TOKEN`, `WEBHOOK_URL`, `OPENAI_API_KEY`).

3. Поднимите сервис:

```bash
docker compose up --build -d
```

4. Проверьте:

```bash
curl http://localhost:8000/health
```

## Ключевые команды бота

- `/start` — регистрация + сбор даты/времени/места рождения
- `/chart` — натальная карта и интерпретация
- `/today` — персональный прогноз на сегодня
- `/week` — недельный прогноз (Premium)
- `/compatibility` — совместимость с партнером
- `/ask` — вопрос ИИ-астрологу
- `/transit` — транзиты дня (Premium)
- `/settings` — планы и оплата Stars
- `/privacy`, `/my_data`, `/export_data`, `/delete_data`

## Важные замечания

- Прогнозы носят исключительно развлекательный характер.
- Не используйте астрологию для медицинских/финансовых критичных решений.
- Bot token храните только в `.env`; не коммитьте секреты в репозиторий.

## Документация

- [deployment_guide.md](deployment_guide.md)
- [api_documentation.md](api_documentation.md)
- [privacy_policy.md](privacy_policy.md)
- [terms_of_service.md](terms_of_service.md)
