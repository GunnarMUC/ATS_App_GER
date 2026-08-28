from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import Application, GeneratedDocument, JobDescription
from app.services.applications import STAGES, get_or_create_application, set_stage

router = APIRouter(tags=["applications"])


@router.post("/applications")
async def create_application(
    job_id: str = Form(...),
    db: Session = Depends(get_db),
):
    job = db.get(JobDescription, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Stelle nicht gefunden.")
    get_or_create_application(db, job_id)
    return RedirectResponse(url="/", status_code=303)


@router.post("/applications/{application_id}/stage")
async def update_stage(
    application_id: str,
    stage: str = Form(...),
    db: Session = Depends(get_db),
):
    if stage not in STAGES:
        raise HTTPException(status_code=422, detail="Unbekannter Status.")
    row = set_stage(db, application_id, stage)
    if row is None:
        raise HTTPException(status_code=404, detail="Bewerbung nicht gefunden.")
    return RedirectResponse(url="/", status_code=303)


@router.post("/applications/{application_id}/notes")
async def update_notes(
    application_id: str,
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    row = db.get(Application, application_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Bewerbung nicht gefunden.")
    row.notes = notes
    db.add(row)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@router.post("/applications/{application_id}/delete")
async def delete_application(application_id: str, db: Session = Depends(get_db)):
    row = db.get(Application, application_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Bewerbung nicht gefunden.")
    db.query(GeneratedDocument).filter(GeneratedDocument.application_id == application_id).update(
        {GeneratedDocument.application_id: None}
    )
    db.delete(row)
    db.commit()
    return RedirectResponse(url="/", status_code=303)
