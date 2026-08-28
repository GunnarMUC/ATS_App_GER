from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.orm import ReferenceCV
from app.services import llm_client
from app.services.ats_structural import analyze_cv_structure, analyze_source_file
from app.services.docx_builder import build_docx
from app.services.pdf_builder import build_pdf
from app.services.settings_service import ensure_settings_row
from app.services.text_builder import build_txt

router = APIRouter(tags=["documents"])
templates = Jinja2Templates(directory="app/templates")


def _facts_for_cv(row: ReferenceCV) -> dict:
    if row.structured_json:
        return row.structured_json
    raise HTTPException(
        status_code=422,
        detail="Keine strukturierten Fakten. Bitte zuerst Fakten speichern oder sperren.",
    )


@router.get("/cv/{cv_id}/ats-structural", response_class=HTMLResponse)
async def ats_structural_partial(cv_id: str, request: Request, db: Session = Depends(get_db)):
    row = db.get(ReferenceCV, cv_id)
    if row is None:
        raise HTTPException(status_code=404, detail="CV nicht gefunden.")

    path = Path(row.stored_path) if row.stored_path else None
    file_report = analyze_source_file(path, row.media_type, row.raw_text)
    facts_report = None
    if row.structured_json:
        facts_report = analyze_cv_structure(row.structured_json)
        row.ats_structural_json = {
            "source": file_report,
            "output": facts_report,
        }
        db.add(row)
        db.commit()

    return templates.TemplateResponse(
        request,
        "partials/ats_report.html",
        {"cv": row, "file_report": file_report, "facts_report": facts_report},
    )


@router.get("/cv/{cv_id}/download")
async def download_master_cv(
    cv_id: str,
    format: str = "docx",
    db: Session = Depends(get_db),
):
    row = db.get(ReferenceCV, cv_id)
    if row is None:
        raise HTTPException(status_code=404, detail="CV nicht gefunden.")
    facts = _facts_for_cv(row)
    fmt = format.lower().strip()
    settings = get_settings()
    out_dir = settings.generated_dir / "cv"
    out_dir.mkdir(parents=True, exist_ok=True)

    safe = f"{row.id}_master"
    if fmt == "txt":
        data = build_txt(facts).encode("utf-8")
        path = out_dir / f"{safe}.txt"
        path.write_bytes(data)
        media = "text/plain; charset=utf-8"
        filename = f"Lebenslauf_{row.original_filename}.txt"
    elif fmt == "pdf":
        path = out_dir / f"{safe}.pdf"
        data = build_pdf(facts, path)
        media = "application/pdf"
        filename = f"Lebenslauf_{Path(row.original_filename).stem}.pdf"
    elif fmt == "docx":
        path = out_dir / f"{safe}.docx"
        data = build_docx(facts, path)
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"Lebenslauf_{Path(row.original_filename).stem}.docx"
    else:
        raise HTTPException(status_code=422, detail="format muss docx|pdf|txt sein.")

    return Response(
        content=data,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/cv/{cv_id}/export", response_class=HTMLResponse)
async def export_page(cv_id: str, request: Request, db: Session = Depends(get_db)):
    row = db.get(ReferenceCV, cv_id)
    if row is None:
        raise HTTPException(status_code=404, detail="CV nicht gefunden.")
    ensure_settings_row(db)
    health = await llm_client.check_health(db)
    path = Path(row.stored_path) if row.stored_path else None
    file_report = analyze_source_file(path, row.media_type, row.raw_text)
    facts_report = analyze_cv_structure(row.structured_json) if row.structured_json else None
    return templates.TemplateResponse(
        request,
        "cv_export.html",
        {
            "cv": row,
            "health": health,
            "file_report": file_report,
            "facts_report": facts_report,
            "has_facts": bool(row.structured_json),
        },
    )
