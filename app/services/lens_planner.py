from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.services.lens_ranker import build_plan_skeleton
from app.services.llm_client import LLMError, extract_json_text, generate
from app.services.prompt_loader import render_prompt

logger = logging.getLogger(__name__)
GenerateFn = Callable[..., Awaitable[str]]


def validate_plan_ids(plan: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    exp_ids = {e["id"] for e in facts.get("experience") or []}
    skill_ids = {s["id"] for s in facts.get("skills") or []}
    bullet_ids = {b["id"] for e in facts.get("experience") or [] for b in e.get("bullets") or []}
    kpi_ids = {k["id"] for k in facts.get("kpis") or []}

    order = [e for e in plan.get("experience_order") or [] if e in exp_ids]
    for e in exp_ids:
        if e not in order and e not in (plan.get("hidden_experience_ids") or []):
            order.append(e)
    hidden = [e for e in plan.get("hidden_experience_ids") or [] if e in exp_ids]
    # hidden must not appear in order
    order = [e for e in order if e not in hidden]

    plan["experience_order"] = order
    plan["hidden_experience_ids"] = hidden
    plan["skill_order"] = [s for s in plan.get("skill_order") or [] if s in skill_ids]
    plan["emphasis_bullet_ids"] = [
        b for b in plan.get("emphasis_bullet_ids") or [] if b in bullet_ids
    ]
    plan["emphasis_kpi_ids"] = [k for k in plan.get("emphasis_kpi_ids") or [] if k in kpi_ids]
    bindings = []
    for b in plan.get("keyword_bindings") or []:
        fid = b.get("fact_id")
        kind = b.get("fact_kind")
        ok = (
            (kind == "skill" and fid in skill_ids)
            or (kind == "kpi" and fid in kpi_ids)
            or (kind == "bullet" and fid in bullet_ids)
            or (kind == "title" and fid in exp_ids)
        )
        if ok:
            bindings.append(b)
    plan["keyword_bindings"] = bindings
    plan["schema_version"] = "1.0"
    if not plan.get("summary_brief") or len(plan["summary_brief"]) < 20:
        plan["summary_brief"] = (
            plan.get("summary_brief")
            or "Rollenspezifische Betonung vorhandener Fakten ohne Erfindungen."
        )
        if len(plan["summary_brief"]) < 20:
            plan["summary_brief"] = (
                "Rollenspezifische Betonung vorhandener Fakten ohne Erfindungen."
            )
    plan.setdefault("gaps", [])
    plan.setdefault("warnings_de", [])
    return plan


async def build_adaptation_plan(
    facts: dict[str, Any],
    *,
    role_family: str,
    job_analysis: dict[str, Any] | None = None,
    role_profile: dict[str, Any] | None = None,
    db=None,
    generate_fn: GenerateFn | None = None,
    use_llm: bool = False,
) -> dict[str, Any]:
    skeleton = build_plan_skeleton(facts, role_family=role_family, job_analysis=job_analysis)
    if role_profile:
        # overlay default order if ids valid
        po = [e for e in role_profile.get("experience_order") or [] if e]
        if po:
            skeleton["experience_order"] = [e for e in po if e in skeleton["experience_order"]] + [
                e for e in skeleton["experience_order"] if e not in po
            ]

    plan = validate_plan_ids(skeleton, facts)
    if not use_llm:
        return plan

    gen = generate_fn or generate
    prompt = render_prompt(
        "plan_adaptation.j2",
        role_family=role_family,
        factlock_json=json.dumps(facts, ensure_ascii=False),
        job_analysis_json=json.dumps(job_analysis or {}, ensure_ascii=False),
        ranker_skeleton_json=json.dumps(plan, ensure_ascii=False),
        role_profile_json=json.dumps(role_profile, ensure_ascii=False) if role_profile else None,
    )
    try:
        raw = await gen(prompt, model_tier="strong", json_mode=True, temperature=0.3, db=db)
        data = json.loads(extract_json_text(raw))
        if isinstance(data, dict):
            if data.get("summary_brief"):
                plan["summary_brief"] = str(data["summary_brief"])[:600]
            if isinstance(data.get("warnings_de"), list):
                plan["warnings_de"] = [str(w) for w in data["warnings_de"]]
            # allow slight reorder if valid
            if isinstance(data.get("experience_order"), list):
                plan["experience_order"] = data["experience_order"]
            if isinstance(data.get("hidden_experience_ids"), list):
                plan["hidden_experience_ids"] = data["hidden_experience_ids"]
            if isinstance(data.get("skill_order"), list):
                plan["skill_order"] = data["skill_order"]
            plan = validate_plan_ids(plan, facts)
    except (LLMError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.info("lens_planner LLM skipped: %s", exc)
    return plan
