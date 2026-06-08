"""HTML views for the Mini App."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return HTMLResponse(
        "<html><body style='font-family:sans-serif;background:#0d1b2a;color:#fff;"
        "text-align:center;padding:40px;'>"
        "<h1>🌌 Stellarium AI</h1>"
        "<p>Откройте бота в Telegram: "
        "<a href='https://t.me/stellarium_ai_bot' style='color:#ffb703;'>"
        "@stellarium_ai_bot</a></p>"
        "</body></html>"
    )


@router.get("/app", response_class=HTMLResponse)
async def app_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("app.html", {"request": request})


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}
