from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.database import init_db
from app.routers import (
    applications,
    documents,
    generate,
    health,
    jobs,
    pages,
    progress,
    reference_cv,
    settings,
    upload,
)
from app.security.bind import assert_bind_is_loopback
from app.security.csrf import CSRFMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("ats_app")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    settings.ensure_dirs()
    assert_bind_is_loopback()
    init_db()
    logger.info("app ready host=%s port=%s", settings.app_host, settings.app_port)
    yield


app = FastAPI(
    title="ATS-Bewerbungs-APP",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if get_settings().debug else None,
    redoc_url=None,
)
app.add_middleware(CSRFMiddleware)

static_dir = Path("app/static")
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(health.router)
app.include_router(pages.router)
app.include_router(upload.router)
app.include_router(settings.router)
app.include_router(reference_cv.router)
app.include_router(documents.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(generate.router)
app.include_router(progress.router)

templates = Jinja2Templates(directory="app/templates")


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.exception("unhandled error path=%s", request.url.path)
    settings = get_settings()
    if "text/html" in (request.headers.get("accept") or ""):
        return templates.TemplateResponse(
            request,
            "partials/error.html",
            {"message": "Ein interner Fehler ist aufgetreten." if not settings.debug else str(exc)},
            status_code=500,
        )
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "Interner Fehler." if not settings.debug else str(exc),
        },
    )
