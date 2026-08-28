from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.orm import Application, GeneratedDocument

STAGES = ("offen", "eingereicht", "interview", "absage", "angebot", "zusage")

STAGE_LABELS = {
    "offen": "Offen",
    "eingereicht": "Eingereicht",
    "interview": "Interview",
    "absage": "Absage",
    "angebot": "Angebot",
    "zusage": "Zusage",
}


def get_or_create_application(db: Session, job_id: str) -> Application:
    row = db.query(Application).filter(Application.job_id == job_id).first()
    if row is not None:
        return row
    row = Application(job_id=job_id, stage="offen", notes="")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def set_stage(db: Session, application_id: str, stage: str) -> Application | None:
    if stage not in STAGES:
        return None
    row = db.get(Application, application_id)
    if row is None:
        return None
    row.stage = stage
    row.updated_at = datetime.now(UTC)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def link_document(db: Session, job_id: str, doc: GeneratedDocument) -> None:
    app_row = get_or_create_application(db, job_id)
    doc.application_id = app_row.id
    db.add(doc)
    db.commit()
