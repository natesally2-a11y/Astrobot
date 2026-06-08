"""HTML-страница Mini App."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.get("/app", response_class=HTMLResponse)
async def mini_app(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("app.html", {"request": request})
