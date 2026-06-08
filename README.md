# Stellarium AI

Персональный ИИ-астролог в Telegram с натальными картами, транзитами и подписками через Telegram Stars.

## Возможности

- **Натальная карта** — расчёт через Swiss Ephemeris (pyswisseph)
- **ИИ-интерпретации** — OpenAI GPT с астрологическими промптами
- **Прогнозы** — дневные, недельные, транзиты
- **Совместимость** — синастрия двух карт
- **Mini App** — интерактивная SVG-карта
- **Подписки** — Free / Pro (50 Stars) / Oracle (150 Stars)
- **GDPR** — согласие, экспорт, удаление данных
- **Inline mode** — вирусные прогнозы по знакам

## Быстрый старт

```bash
cp .env.example .env
# Заполните BOT_TOKEN и OPENAI_API_KEY

docker compose up -d --build
```

Для локальной разработки:

```bash
pip install -r requirements.txt
docker compose up db redis -d
python -m app.polling
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Регистрация и создание карты |
| `/chart` | Натальная карта |
| `/today` | Прогноз на сегодня |
| `/week` | Прогноз на неделю (Pro) |
| `/compatibility` | Совместимость |
| `/ask` | Вопрос астрологу |
| `/transit` | Транзиты (Pro) |
| `/settings` | Настройки и подписка |

## Структура проекта

```
app/
├── bot/           # Telegram bot (aiogram 3)
├── webapp/        # Mini App (FastAPI + HTML/JS)
├── astrology/     # Swiss Ephemeris + AI + SVG
├── database/      # SQLAlchemy models + CRUD
├── main.py        # FastAPI entry point
└── polling.py     # Dev polling mode
```

## Документация

- [deployment_guide.md](deployment_guide.md) — развёртывание
- [api_documentation.md](api_documentation.md) — Mini App API
- [privacy_policy.md](privacy_policy.md) — политика конфиденциальности
- [terms_of_service.md](terms_of_service.md) — пользовательское соглашение

## Стек

Python 3.11 · FastAPI · aiogram 3 · PostgreSQL · Redis · pyswisseph · OpenAI

## Дисклеймер

Астрологические прогнозы носят развлекательный характер и не являются руководством к действию.
