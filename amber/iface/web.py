"""FastAPI + Jinja2：三列看板。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..adapters.llm import build_llm
from ..adapters.store import SqliteStore
from ..app.run import PROMPT, board, explain
from ..config import Settings

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))


def create_app(settings: Settings, store: SqliteStore | None = None) -> FastAPI:
    app = FastAPI(title="Amber", version="1.0.0")
    app.mount(
        "/static",
        StaticFiles(directory=str(Path(__file__).resolve().parents[2] / "static")),
        name="static",
    )
    store = store or SqliteStore(settings.db_path)
    llm = build_llm(settings.llm_base_url, settings.llm_api_key, settings.llm_model, PROMPT) if settings.llm_enabled else None

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        try:
            b = board(store, settings)
            error = ""
        except ValueError as exc:
            b = None
            error = str(exc)
        return TEMPLATES.TemplateResponse(
            request, "index.html",
            {"board": b, "error": error, "today": date.today().isoformat()},
        )

    @app.get("/explain.txt", response_class=PlainTextResponse)
    def explain_text() -> PlainTextResponse:
        _, text = explain(store, settings, llm=llm)
        return PlainTextResponse(text, media_type="text/plain; charset=utf-8")

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "tasks": len(store.list_tasks())}

    return app


def app_factory(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        from ..config import settings as default_settings

        settings = default_settings
    return create_app(settings)

