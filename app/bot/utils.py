"""Вспомогательные функции для обработчиков бота."""
from __future__ import annotations

from aiogram.types import Message

TG_LIMIT = 4096


async def reply_long(message: Message, text: str, **kwargs) -> None:
    """Отправить длинный текст, разбив его на части по лимиту Telegram."""
    if len(text) <= TG_LIMIT:
        await message.answer(text, **kwargs)
        return
    chunk = ""
    for paragraph in text.split("\n"):
        if len(chunk) + len(paragraph) + 1 > TG_LIMIT:
            await message.answer(chunk, **kwargs)
            chunk = ""
        chunk += paragraph + "\n"
    if chunk.strip():
        await message.answer(chunk, **kwargs)


def parse_referral(args: str | None) -> int | None:
    """Извлечь telegram_id реферера из аргументов /start."""
    if not args:
        return None
    raw = args.strip()
    if raw.startswith("ref_"):
        raw = raw[4:]
    if raw.isdigit():
        return int(raw)
    return None
