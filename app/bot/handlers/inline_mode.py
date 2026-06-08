from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

router = Router(name='inline-mode')

SIGN_HINTS = {
    'aries': 'Огонь дня подталкивает к быстрым решениям — направь его в один конкретный шаг.',
    'taurus': 'Стабильность приходит через телесный комфорт, финансовую ясность и спокойный темп.',
    'gemini': 'Сегодня особенно важны диалог, любопытство и умение быстро перестраиваться.',
    'cancer': 'Эмоции усиливаются, поэтому полезно выбирать мягкую коммуникацию и заботу о границах.',
    'leo': 'Сцена твоя, если действовать щедро и уверенно, но без драматизации.',
    'virgo': 'День поддерживает наведение порядка, анализ и маленькие практичные улучшения.',
    'libra': 'Гармония приходит через честный разговор и красивое, но реалистичное равновесие.',
    'scorpio': 'Интенсивность стоит направить в честность с собой и стратегическое спокойствие.',
    'sagittarius': 'Подходит для расширения горизонтов, обучения и смелых, но продуманных инициатив.',
    'capricorn': 'Сегодня выигрывают дисциплина, структура и решения с долгим горизонтом.',
    'aquarius': 'Сильны новые идеи, сообщества и нестандартный взгляд на привычные задачи.',
    'pisces': 'Интуиция особенно живая — держи рядом блокнот и проверяй вдохновение фактами.',
}


@router.inline_query()
async def inline_query_handler(query: InlineQuery) -> None:
    text = (query.query or '').strip().lower()
    results = []
    if text.startswith('compatibility'):
        payload = text.replace('compatibility', '', 1).strip() or 'leo scorpio'
        parts = payload.split()
        left = parts[0].title() if parts else 'Leo'
        right = parts[1].title() if len(parts) > 1 else 'Scorpio'
        preview = f'Совместимость {left} + {right}: сильное притяжение, если есть уважение к границам и честный диалог.'
        results.append(
            InlineQueryResultArticle(
                id='compatibility-preview',
                title=f'Совместимость {left} + {right}',
                description='Быстрый вирусный preview для inline mode',
                input_message_content=InputTextMessageContent(message_text=preview),
            )
        )
    else:
        sign = text.replace('daily', '', 1).strip() or 'virgo'
        preview = SIGN_HINTS.get(sign.lower(), SIGN_HINTS['virgo'])
        results.append(
            InlineQueryResultArticle(
                id='daily-preview',
                title=f'Прогноз на сегодня для {sign.title()}',
                description='Короткий preview для встроенного режима',
                input_message_content=InputTextMessageContent(message_text=f'⭐ {preview}'),
            )
        )
    await query.answer(results, cache_time=1, is_personal=True)
