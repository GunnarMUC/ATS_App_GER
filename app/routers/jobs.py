from __future__ import annotations

from datetime import UTC

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.domain.role_taxonomy import LABELS_DE, ROLE_FAMILIES
from app.models.orm import (
    AdaptationPlan,
    FactLock,
    JobDescription,
    RoleDetection,
    RoleProfile,
)
from app.services import llm_client
from app.services.document_parser import ParseError, parse_bytes, parse_plain_text
from app.services.fact_lock import get_active_lock
from app.services.job_analyzer import analyze_and_detect
from app.services.lens_planner import build_adaptation_plan, validate_plan_ids
from app.services.settings_service import ensure_settings_row
from app.services.storage import store_upload

router = APIRouter(tags=["jobs"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/jobs/new", response_class=HTMLResponse)
async def job_new_page(request: Request, db: Session = Depends(get_db)):
    ensure_settings_row(db)
    health = await llm_client.check_health(db)
    lock = get_active_lock(db)
    return templates.TemplateResponse(
        request,
        "job_new.html",
        {"health": health, "has_lock": lock is not None},
    )


@router.post("/jobs")
async def create_job(
    request: Request,
    db: Session = Depends(get_db),
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    use_llm: str | None = Form(None),
):
    ensure_settings_row(db)
    settings = get_settings()
    try:
        if file is not None and file.filename:
            data = await file.read()
            if len(data) > settings.max_upload_bytes:
                raise HTTPException(status_code=413, detail="Datei zu groß.")
            result = parse_bytes(data, file.filename)
            _n, path = store_upload(data, file.filename)
            source = "upload"
            stored = str(path)
            raw = result.text
        elif text and text.strip():
            result = parse_plain_text(text)
            raw = result.text
            source = "paste"
            stored = None
        else:
            raise HTTPException(status_code=422, detail="Text oder Datei erforderlich.")
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc

    analysis, detection = await analyze_and_detect(raw, db=db, use_llm=bool(use_llm))
    title = analysis.get("title") or (raw.splitlines() or ["Stelle"])[0][:200]
    job = JobDescription(
        title_raw=title,
        source=source,
        raw_text=raw,
        stored_path=stored,
        language=analysis.get("language") or "de",
        analysis_json=analysis,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    det = RoleDetection(job_id=job.id, detection_json=detection)
    db.add(det)
    db.commit()

    if request.headers.get("hx-request") or "text/html" in (request.headers.get("accept") or ""):
        return RedirectResponse(url=f"/jobs/{job.id}", status_code=303)
    return {"ok": True, "job_id": job.id, "analysis": analysis, "detection": detection}


@router.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(job_id: str, request: Request, db: Session = Depends(get_db)):
    job = db.get(JobDescription, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Stelle nicht gefunden.")
    ensure_settings_row(db)
    health = await llm_client.check_health(db)
    det = (
        db.query(RoleDetection)
        .filter(RoleDetection.job_id == job_id)
        .order_by(RoleDetection.created_at.desc())
        .first()
    )
    detection = det.detection_json if det else {}
    user_role = det.user_role_family if det else None
    effective = user_role or (detection.get("top") or {}).get("role_family") or "other"
    lock = get_active_lock(db)
    return templates.TemplateResponse(
        request,
        "job_detail.html",
        {
            "health": health,
            "job": job,
            "detection": detection,
            "user_role": user_role,
            "effective_role": effective,
            "labels": LABELS_DE,
            "families": ROLE_FAMILIES,
            "has_lock": lock is not None,
            "det_row": det,
        },
    )


@router.post("/jobs/{job_id}/role")
async def set_role(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db),
    role_family: str = Form(...),
):
    job = db.get(JobDescription, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Stelle nicht gefunden.")
    if role_family not in ROLE_FAMILIES:
        raise HTTPException(status_code=422, detail="Unbekannte Rolle.")
    det = (
        db.query(RoleDetection)
        .filter(RoleDetection.job_id == job_id)
        .order_by(RoleDetection.created_at.desc())
        .first()
    )
    if det is None:
        raise HTTPException(status_code=404, detail="Keine Detection.")
    det.user_role_family = role_family
    db.add(det)
    db.commit()
    return RedirectResponse(url=f"/jobs/{job_id}/plan", status_code=303)


@router.post("/jobs/{job_id}/plan")
@router.get("/jobs/{job_id}/plan", response_class=HTMLResponse)
async def plan_page(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    job = db.get(JobDescription, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Stelle nicht gefunden.")
    lock = get_active_lock(db)
    if lock is None:
        raise HTTPException(
            status_code=422, detail="Kein aktiver FactLock. Zuerst Master-CV sperren."
        )
    ensure_settings_row(db)
    health = await llm_client.check_health(db)

    det = (
        db.query(RoleDetection)
        .filter(RoleDetection.job_id == job_id)
        .order_by(RoleDetection.created_at.desc())
        .first()
    )
    role_family = (
        (det.user_role_family if det else None)
        or ((det.detection_json or {}).get("top") or {}).get("role_family")
        or "other"
    )

    profile = (
        db.query(RoleProfile)
        .filter(RoleProfile.role_family == role_family)
        .order_by(RoleProfile.updated_at.desc())
        .first()
    )
    profile_lens = profile.lens_json if profile else None

    existing = (
        db.query(AdaptationPlan)
        .filter(
            AdaptationPlan.job_id == job_id,
            AdaptationPlan.status.in_(["draft", "confirmed"]),
        )
        .order_by(AdaptationPlan.id.desc())
        .first()
    )

    if request.method == "POST" or existing is None:
        plan_json = await build_adaptation_plan(
            lock.facts_json,
            role_family=role_family,
            job_analysis=job.analysis_json,
            role_profile=profile_lens,
            db=db,
            use_llm=False,
        )
        if existing and existing.status == "draft":
            existing.plan_json = plan_json
            existing.fact_lock_id = lock.id
            existing.role_profile_id = profile.id if profile else None
            db.add(existing)
            db.commit()
            db.refresh(existing)
            plan_row = existing
        else:
            plan_row = AdaptationPlan(
                job_id=job_id,
                fact_lock_id=lock.id,
                role_profile_id=profile.id if profile else None,
                plan_json=plan_json,
                status="draft",
            )
            db.add(plan_row)
            db.commit()
            db.refresh(plan_row)
    else:
        plan_row = existing

    facts = lock.facts_json
    exp_map = {e["id"]: e for e in facts.get("experience") or []}
    skill_map = {s["id"]: s for s in facts.get("skills") or []}
    return templates.TemplateResponse(
        request,
        "plan.html",
        {
            "health": health,
            "job": job,
            "plan": plan_row,
            "plan_json": plan_row.plan_json,
            "role_family": role_family,
            "labels": LABELS_DE,
            "exp_map": exp_map,
            "skill_map": skill_map,
            "profile": profile,
        },
    )


@router.put("/jobs/{job_id}/plan/{plan_id}")
async def update_plan(
    job_id: str,
    plan_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    plan = db.get(AdaptationPlan, plan_id)
    if plan is None or plan.job_id != job_id:
        raise HTTPException(status_code=404, detail="Plan nicht gefunden.")
    if plan.status == "confirmed":
        raise HTTPException(status_code=409, detail="Plan bereits bestätigt.")
    lock = db.get(FactLock, plan.fact_lock_id)
    body = await request.json()
    data = {**plan.plan_json, **body}
    data = validate_plan_ids(data, lock.facts_json)
    plan.plan_json = data
    db.add(plan)
    db.commit()
    return {"ok": True, "plan": plan.plan_json}


@router.post("/jobs/{job_id}/plan/{plan_id}/confirm")
async def confirm_plan(job_id: str, plan_id: str, request: Request, db: Session = Depends(get_db)):
    plan = db.get(AdaptationPlan, plan_id)
    if plan is None or plan.job_id != job_id:
        raise HTTPException(status_code=404, detail="Plan nicht gefunden.")
    # optional form overrides
    ctype = request.headers.get("content-type") or ""
    if "form" in ctype:
        form = await request.form()
        data = dict(plan.plan_json)
        if form.get("summary_brief"):
            data["summary_brief"] = str(form.get("summary_brief"))[:600]
        order = form.getlist("experience_order") if hasattr(form, "getlist") else []
        if not order and form.get("experience_order_csv"):
            order = [x for x in str(form.get("experience_order_csv")).split(",") if x]
        hidden = form.getlist("hidden_experience_ids") if hasattr(form, "getlist") else []
        if form.get("hidden_csv") is not None:
            hidden = [x for x in str(form.get("hidden_csv")).split(",") if x]
        if order:
            data["experience_order"] = list(order)
        data["hidden_experience_ids"] = list(hidden)
        lock = db.get(FactLock, plan.fact_lock_id)
        data = validate_plan_ids(data, lock.facts_json)
        plan.plan_json = data

    from datetime import datetime

    # supersede other confirmed for same job
    for other in (
        db.query(AdaptationPlan)
        .filter(AdaptationPlan.job_id == job_id, AdaptationPlan.status == "confirmed")
        .all()
    ):
        if other.id != plan.id:
            other.status = "superseded"
            db.add(other)

    plan.status = "confirmed"
    plan.confirmed_at = datetime.now(UTC)
    db.add(plan)
    db.commit()
    return RedirectResponse(url=f"/jobs/{job_id}/review", status_code=303)


@router.post("/api/profiles")
async def save_profile(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    name = body.get("name") or "Profil"
    role_family = body.get("role_family")
    lens = body.get("lens_json") or body.get("plan_json")
    if not role_family or not lens:
        raise HTTPException(status_code=422, detail="role_family und lens_json nötig.")
    row = RoleProfile(name=name, role_family=role_family, lens_json=lens)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"ok": True, "id": row.id}


@router.get("/profiles", response_class=HTMLResponse)
async def profiles_page(request: Request, db: Session = Depends(get_db)):
    ensure_settings_row(db)
    health = await llm_client.check_health(db)
    rows = db.query(RoleProfile).order_by(RoleProfile.updated_at.desc()).all()
    return templates.TemplateResponse(
        request,
        "profiles.html",
        {"health": health, "profiles": rows, "labels": LABELS_DE},
    )
