"""Mini App HTML pages."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

_TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse(
        "landing.html", {"request": request, "title": "Stellarium AI"}
    )


@router.get("/app", response_class=HTMLResponse)
async def mini_app(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "Stellarium AI"}
    )
