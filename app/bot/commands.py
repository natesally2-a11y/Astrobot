"""Регистрация списка команд бота (меню Telegram)."""
from __future__ import annotations

from aiogram import Bot
from aiogram.types import BotCommand

BOT_COMMANDS = [
    BotCommand(command="start", description="Приветствие и регистрация"),
    BotCommand(command="chart", description="Натальная карта + ИИ-анализ"),
    BotCommand(command="today", description="Прогноз на сегодня"),
    BotCommand(command="week", description="Прогноз на неделю (Premium)"),
    BotCommand(command="compatibility", description="Совместимость с партнёром"),
    BotCommand(command="ask", description="Задать вопрос астрологу"),
    BotCommand(command="transit", description="Важные транзиты (Premium)"),
    BotCommand(command="settings", description="Настройки и подписка"),
    BotCommand(command="privacy", description="Политика конфиденциальности"),
    BotCommand(command="my_data", description="Мои сохранённые данные"),
    BotCommand(command="export_data", description="Экспорт данных (JSON)"),
    BotCommand(command="delete_data", description="Удалить все данные"),
    BotCommand(command="help", description="Справка по командам"),
]


async def set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(BOT_COMMANDS)
