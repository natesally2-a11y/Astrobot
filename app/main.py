from contextlib import asynccontextmanager
from pathlib import Path

import markdown
from aiogram.types import Update
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.bot.dispatcher import configure_bot, create_bot, create_dispatcher
from app.config import settings
from app.database.session import init_db
from app.seed_demo import seed_demo_data
from app.webapp.api.routes import router as api_router

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
templates = Jinja2Templates(directory=str(BASE_DIR / 'webapp' / 'templates'))

bot = create_bot()
dispatcher = create_dispatcher()


def render_markdown(path: Path) -> str:
    if not path.exists():
        return '<p>Document not found.</p>'
    return markdown.markdown(path.read_text(encoding='utf-8'))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    if settings.enable_demo_data:
        await seed_demo_data()
    if bot is not None:
        await configure_bot(bot)
    yield
    if bot is not None:
        await bot.session.close()


app = FastAPI(title='Stellarium AI', version='1.0.0', lifespan=lifespan)
app.mount('/static', StaticFiles(directory=str(BASE_DIR / 'webapp' / 'static')), name='static')
app.include_router(api_router)


@app.get('/health')
async def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.post('/webhook')
async def telegram_webhook(request: Request) -> JSONResponse:
    if bot is None:
        return JSONResponse({'ok': False, 'detail': 'BOT_TOKEN not configured'}, status_code=503)
    update = Update.model_validate(await request.json(), context={'bot': bot})
    await dispatcher.feed_update(bot, update)
    return JSONResponse({'ok': True})


@app.get('/app', response_class=HTMLResponse)
async def mini_app(request: Request, telegram_id: int = 777000):
    bot_username = ''
    if bot is not None:
        try:
            me = await bot.get_me()
            bot_username = me.username or ''
        except Exception:
            bot_username = ''
    return templates.TemplateResponse(
        request=request,
        name='index.html',
        context={'telegram_id': telegram_id, 'bot_username': bot_username},
    )


@app.get('/privacy', response_class=HTMLResponse)
async def privacy() -> HTMLResponse:
    html = render_markdown(ROOT_DIR / 'privacy_policy.md')
    return HTMLResponse(f'<html><body style="max-width: 880px; margin: 40px auto; font-family: sans-serif;">{html}</body></html>')


@app.get('/terms', response_class=HTMLResponse)
async def terms() -> HTMLResponse:
    html = render_markdown(ROOT_DIR / 'terms_of_service.md')
    return HTMLResponse(f'<html><body style="max-width: 880px; margin: 40px auto; font-family: sans-serif;">{html}</body></html>')
