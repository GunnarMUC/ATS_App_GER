from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.services import llm_client
from app.services.llm_client import LLMError
from app.services.settings_service import ensure_settings_row, update_settings

router = APIRouter(tags=["settings"])
templates = Jinja2Templates(directory="app/templates")


class SettingsUpdate(BaseModel):
    ollama_host: str | None = None
    model_fast: str | None = None
    model_strong: str | None = None
    same_model: bool = False


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    row = ensure_settings_row(db)
    health = await llm_client.check_health(db)
    models: list[str] = health.get("models_installed") or []
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "settings_row": row,
            "health": health,
            "models": models,
            "env_defaults": get_settings(),
        },
    )


@router.put("/settings")
@router.post("/api/settings")
async def settings_put(body: SettingsUpdate, db: Session = Depends(get_db)):
    try:
        fast = body.model_fast
        strong = body.model_strong
        if body.same_model and fast:
            strong = fast
        row = update_settings(
            db,
            ollama_host=body.ollama_host,
            model_fast=fast,
            model_strong=strong,
        )
    except LLMError as exc:
        return JSONResponse(
            status_code=422,
            content={"error": exc.code, "message": exc.message},
        )
    health = await llm_client.check_health(db)
    return {
        "ok": True,
        "settings": {
            "ollama_host": row.ollama_host,
            "model_fast": row.model_fast,
            "model_strong": row.model_strong,
        },
        "health": health,
    }


@router.post("/settings/wipe")
async def wipe_data(request: Request, db: Session = Depends(get_db), confirm: str = Form("")):
    if confirm != "LOESCHEN":
        ensure_settings_row(db)
        health = await llm_client.check_health(db)
        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "settings_row": ensure_settings_row(db),
                "health": health,
                "models": health.get("models_installed") or [],
                "env_defaults": get_settings(),
                "error": "Zum Löschen LOESCHEN eingeben.",
            },
            status_code=400,
        )
    from app.config import get_settings as gs
    from app.models import orm as models
    import shutil

    for table in (
        models.GeneratedDocument,
        models.AdaptationPlan,
        models.RoleDetection,
        models.JobDescription,
        models.FactLock,
        models.RoleProfile,
        models.ReferenceCV,
    ):
        db.query(table).delete()
    db.commit()
    data = gs().data_dir
    for sub in ("uploads", "generated"):
        p = data / sub
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
            p.mkdir(parents=True, exist_ok=True)
    ensure_settings_row(db)
    health = await llm_client.check_health(db)
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "settings_row": ensure_settings_row(db),
            "health": health,
            "models": health.get("models_installed") or [],
            "env_defaults": get_settings(),
            "saved": True,
            "error": None,
        },
    )


@router.post("/settings")
async def settings_form(
    request: Request,
    db: Session = Depends(get_db),
    ollama_host: str = Form(...),
    model_fast: str = Form(...),
    model_strong: str = Form(""),
    same_model: str | None = Form(None),
):
    try:
        strong = model_fast if same_model else (model_strong or model_fast)
        row = update_settings(
            db,
            ollama_host=ollama_host,
            model_fast=model_fast,
            model_strong=strong,
        )
        error = None
    except LLMError as exc:
        row = ensure_settings_row(db)
        error = exc.message
    health = await llm_client.check_health(db)
    models: list[str] = health.get("models_installed") or []
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "settings_row": row,
            "health": health,
            "models": models,
            "env_defaults": get_settings(),
            "error": error,
            "saved": error is None,
        },
    )
