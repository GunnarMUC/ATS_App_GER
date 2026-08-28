from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import FactLock, ReferenceCV
from app.services import llm_client
from app.services.cv_structurer import StructureError, structure_cv_text, validate_cv_dict
from app.services.fact_lock import commit_lock, get_active_lock, save_draft
from app.services.settings_service import ensure_settings_row

router = APIRouter(tags=["reference_cv"])
templates = Jinja2Templates(directory="app/templates")

FIXTURE_MASTER = Path(__file__).resolve().parents[2] / "spec" / "fixtures" / "master-cv.json"


class FactsBody(BaseModel):
    facts: dict


@router.post("/cv/{cv_id}/structure")
async def structure_cv(cv_id: str, request: Request, db: Session = Depends(get_db)):
    row = db.get(ReferenceCV, cv_id)
    if row is None:
        raise HTTPException(status_code=404, detail="CV nicht gefunden.")
    ensure_settings_row(db)
    try:
        structured = await structure_cv_text(row.raw_text, db=db)
    except StructureError as exc:
        status = 503 if exc.code in {"ollama_down", "host_not_allowed"} else 422
        raise HTTPException(status_code=status, detail=exc.message) from exc

    data = structured.to_canonical_dict()
    row.structured_json = data
    db.add(row)
    db.commit()
    db.refresh(row)

    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request,
            "partials/facts_editor.html",
            {
                "cv": row,
                "facts": data,
                "facts_json": json.dumps(data, ensure_ascii=False, indent=2),
                "lock": None,
                "saved": False,
            },
        )
    return {"ok": True, "facts": data}


@router.get("/cv/{cv_id}/facts", response_class=HTMLResponse)
async def facts_page(cv_id: str, request: Request, db: Session = Depends(get_db)):
    row = db.get(ReferenceCV, cv_id)
    if row is None:
        raise HTTPException(status_code=404, detail="CV nicht gefunden.")
    ensure_settings_row(db)
    health = await llm_client.check_health(db)
    facts = row.structured_json
    lock = (
        db.query(FactLock)
        .filter(FactLock.reference_cv_id == cv_id, FactLock.is_active.is_(True))
        .first()
    )
    return templates.TemplateResponse(
        request,
        "cv_facts.html",
        {
            "cv": row,
            "facts": facts,
            "facts_json": json.dumps(facts, ensure_ascii=False, indent=2) if facts else "",
            "lock": lock,
            "health": health,
            "active_lock": get_active_lock(db),
        },
    )


@router.put("/cv/{cv_id}/facts")
async def put_facts(cv_id: str, body: FactsBody, db: Session = Depends(get_db)):
    row = db.get(ReferenceCV, cv_id)
    if row is None:
        raise HTTPException(status_code=404, detail="CV nicht gefunden.")
    try:
        validated = validate_cv_dict(body.facts)
    except ValidationError as exc:
        return JSONResponse(
            status_code=422,
            content={"error": "validation_failed", "message": str(exc)},
        )
    save_draft(db, cv_id, validated)
    return {"ok": True, "facts": validated.to_canonical_dict()}


@router.post("/cv/{cv_id}/facts")
async def post_facts_form(
    cv_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    row = db.get(ReferenceCV, cv_id)
    if row is None:
        raise HTTPException(status_code=404, detail="CV nicht gefunden.")
    form = await request.form()
    raw = form.get("facts_json") or ""
    try:
        data = json.loads(str(raw))
        validated = validate_cv_dict(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        health = await llm_client.check_health(db)
        return templates.TemplateResponse(
            request,
            "cv_facts.html",
            {
                "cv": row,
                "facts": row.structured_json,
                "facts_json": str(raw),
                "lock": None,
                "health": health,
                "error": f"Ungültige Fakten: {exc}",
                "active_lock": get_active_lock(db),
            },
            status_code=422,
        )
    save_draft(db, cv_id, validated)
    health = await llm_client.check_health(db)
    return templates.TemplateResponse(
        request,
        "cv_facts.html",
        {
            "cv": row,
            "facts": validated.to_canonical_dict(),
            "facts_json": json.dumps(validated.to_canonical_dict(), ensure_ascii=False, indent=2),
            "lock": None,
            "health": health,
            "saved": True,
            "active_lock": get_active_lock(db),
        },
    )


@router.post("/cv/{cv_id}/lock")
async def lock_facts(cv_id: str, request: Request, db: Session = Depends(get_db)):
    row = db.get(ReferenceCV, cv_id)
    if row is None:
        raise HTTPException(status_code=404, detail="CV nicht gefunden.")

    facts_data = row.structured_json
    ctype = request.headers.get("content-type") or ""
    if "application/json" in ctype:
        body = await request.json()
        if isinstance(body, dict) and body.get("facts"):
            facts_data = body["facts"]
    elif "application/x-www-form-urlencoded" in ctype or "multipart/form-data" in ctype:
        form = await request.form()
        raw = form.get("facts_json")
        if raw:
            try:
                facts_data = json.loads(str(raw))
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=422, detail="facts_json ungültig") from exc

    if not facts_data:
        raise HTTPException(
            status_code=422,
            detail="Keine Fakten zum Sperren. Bitte zuerst speichern oder strukturieren.",
        )

    try:
        validated = validate_cv_dict(facts_data)
        lock = commit_lock(db, reference_cv_id=cv_id, facts=validated)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    db.refresh(row)
    wants_html = "text/html" in (request.headers.get("accept") or "") or request.headers.get(
        "hx-request"
    )
    if wants_html and "application/json" not in ctype:
        health = await llm_client.check_health(db)
        return templates.TemplateResponse(
            request,
            "cv_facts.html",
            {
                "cv": row,
                "facts": lock.facts_json,
                "facts_json": json.dumps(lock.facts_json, ensure_ascii=False, indent=2),
                "lock": lock,
                "health": health,
                "locked": True,
                "active_lock": lock,
            },
        )
    return {
        "ok": True,
        "lock_id": lock.id,
        "content_hash": lock.content_hash,
        "is_active": lock.is_active,
    }


@router.post("/cv/load-fixture")
async def load_fixture(request: Request, db: Session = Depends(get_db)):
    if not FIXTURE_MASTER.exists():
        raise HTTPException(status_code=404, detail="Fixture fehlt.")
    facts = json.loads(FIXTURE_MASTER.read_text(encoding="utf-8"))
    validated = validate_cv_dict(facts)
    raw = json.dumps(facts, ensure_ascii=False, indent=2)
    from app.services.storage import store_upload

    _name, path = store_upload(raw.encode("utf-8"), "master-cv-fixture.json")
    row = ReferenceCV(
        original_filename="master-cv-fixture.json",
        stored_path=str(path),
        media_type="txt",
        raw_text=raw,
        structured_json=validated.to_canonical_dict(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return JSONResponse(
        {
            "ok": True,
            "cv_id": row.id,
            "redirect": f"/cv/{row.id}/facts",
        }
    )
