from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import ReferenceCV
from app.services import llm_client
from app.services.settings_service import ensure_settings_row

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    ensure_settings_row(db)
    health = await llm_client.check_health(db)
    cvs = db.query(ReferenceCV).order_by(ReferenceCV.created_at.desc()).limit(10).all()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"health": health, "cvs": cvs},
    )


@router.get("/cv", response_class=HTMLResponse)
async def cv_page(request: Request, db: Session = Depends(get_db)):
    ensure_settings_row(db)
    health = await llm_client.check_health(db)
    cvs = db.query(ReferenceCV).order_by(ReferenceCV.created_at.desc()).all()
    return templates.TemplateResponse(
        request,
        "cv_upload.html",
        {"health": health, "cvs": cvs},
    )
