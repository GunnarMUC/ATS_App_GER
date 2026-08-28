from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.role_taxonomy import LABELS_DE
from app.models.orm import (
    Application,
    GeneratedDocument,
    JobDescription,
    ReferenceCV,
    RoleDetection,
)
from app.services import llm_client
from app.services.applications import STAGE_LABELS, STAGES
from app.services.settings_service import ensure_settings_row

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    ensure_settings_row(db)
    health = await llm_client.check_health(db)
    cvs = db.query(ReferenceCV).order_by(ReferenceCV.created_at.desc()).limit(10).all()
    apps = db.query(Application).order_by(Application.updated_at.desc()).all()
    rows = []
    for app_row in apps:
        job = db.get(JobDescription, app_row.job_id)
        det = (
            db.query(RoleDetection)
            .filter(RoleDetection.job_id == app_row.job_id)
            .order_by(RoleDetection.created_at.desc())
            .first()
        )
        detection = det.detection_json if det else {}
        role = (
            (det.user_role_family if det else None)
            or (detection.get("top") or {}).get("role_family")
            or ""
        )
        latest_cv = (
            db.query(GeneratedDocument)
            .filter(
                GeneratedDocument.application_id == app_row.id,
                GeneratedDocument.type == "cv",
            )
            .order_by(GeneratedDocument.version.desc())
            .first()
        )
        if latest_cv is None:
            latest_cv = (
                db.query(GeneratedDocument)
                .filter(
                    GeneratedDocument.job_id == app_row.job_id,
                    GeneratedDocument.type == "cv",
                )
                .order_by(GeneratedDocument.version.desc())
                .first()
            )
        rows.append(
            {
                "app": app_row,
                "job": job,
                "role": role,
                "role_label": LABELS_DE.get(role, role),
                "latest_cv": latest_cv,
            }
        )
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "health": health,
            "cvs": cvs,
            "applications": rows,
            "stages": STAGES,
            "stage_labels": STAGE_LABELS,
        },
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
