from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.orm import ReferenceCV
from app.services.document_parser import ParseError, parse_bytes, parse_plain_text
from app.services.storage import store_upload

router = APIRouter(tags=["upload"])
templates = Jinja2Templates(directory="app/templates")


@router.post("/upload/cv")
async def upload_cv(
    request: Request,
    db: Session = Depends(get_db),
    file: UploadFile | None = File(None),
    paste_text: str | None = Form(None),
):
    settings = get_settings()
    try:
        if file is not None and file.filename:
            data = await file.read()
            if len(data) > settings.max_upload_bytes:
                raise HTTPException(status_code=413, detail="Datei zu groß (max. 8 MB).")
            if not data:
                raise HTTPException(status_code=422, detail="Leere Datei.")
            result = parse_bytes(data, file.filename)
            _stored_name, path = store_upload(data, file.filename)
            original = file.filename
            stored_path = str(path)
        elif paste_text and paste_text.strip():
            result = parse_plain_text(paste_text)
            _stored_name, path = store_upload(
                paste_text.encode("utf-8"), "paste.txt"
            )
            original = "paste.txt"
            stored_path = str(path)
        else:
            raise HTTPException(status_code=422, detail="Datei oder Text erforderlich.")
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc

    row = ReferenceCV(
        original_filename=original,
        stored_path=stored_path,
        media_type=result.media_type,
        raw_text=result.text,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    wants_html = "text/html" in (request.headers.get("accept") or "")
    if wants_html or request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request,
            "partials/upload_preview.html",
            {"cv": row, "warnings": result.warnings},
        )
    return RedirectResponse(url=f"/cv/{row.id}", status_code=303)


@router.get("/cv/{cv_id}", response_class=HTMLResponse)
async def cv_detail(cv_id: str, request: Request, db: Session = Depends(get_db)):
    row = db.get(ReferenceCV, cv_id)
    if row is None:
        raise HTTPException(status_code=404, detail="CV nicht gefunden.")
    return templates.TemplateResponse(
        request,
        "cv_detail.html",
        {"cv": row, "warnings": []},
    )
