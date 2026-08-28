from __future__ import annotations

import copy
import json
import logging
from typing import Any, Awaitable, Callable

from app.services.cv_structurer import validate_cv_dict
from app.services.llm_client import LLMError, extract_json_text, generate
from app.services.prompt_loader import render_prompt

logger = logging.getLogger(__name__)
GenerateFn = Callable[..., Awaitable[str]]


def apply_plan_deterministically(
    facts: dict[str, Any],
    plan: dict[str, Any],
) -> dict[str, Any]:
    """Build a valid CV JSON from FactLock + plan without LLM (safe baseline)."""
    out = copy.deepcopy(facts)
    hidden = set(plan.get("hidden_experience_ids") or [])
    order = plan.get("experience_order") or []
    exp_map = {e["id"]: e for e in facts.get("experience") or []}
    ordered = []
    for eid in order:
        if eid in exp_map and eid not in hidden:
            ordered.append(copy.deepcopy(exp_map[eid]))
    for eid, exp in exp_map.items():
        if eid not in hidden and all(e["id"] != eid for e in ordered):
            ordered.append(copy.deepcopy(exp))

    # emphasize bullets: reorder bullets within first exp
    emphasis = set(plan.get("emphasis_bullet_ids") or [])
    for exp in ordered:
        bullets = exp.get("bullets") or []
        top = [b for b in bullets if b.get("id") in emphasis]
        rest = [b for b in bullets if b.get("id") not in emphasis]
        exp["bullets"] = top + rest

    out["experience"] = ordered

    skill_map = {s["id"]: s for s in facts.get("skills") or []}
    skill_order = plan.get("skill_order") or []
    skills = []
    for sid in skill_order:
        if sid in skill_map:
            skills.append(copy.deepcopy(skill_map[sid]))
    for sid, sk in skill_map.items():
        if all(s["id"] != sid for s in skills):
            skills.append(copy.deepcopy(sk))
    out["skills"] = skills

    brief = plan.get("summary_brief") or ""
    # summary from brief + top bullets (no new facts)
    bits = []
    for exp in ordered[:2]:
        for b in (exp.get("bullets") or [])[:2]:
            bits.append(b.get("text") or "")
    summary = brief
    if bits:
        summary = brief.rstrip(".") + ". " + bits[0]
    out["summary"] = summary[:800]
    out["schema_version"] = "1.0"
    return validate_cv_dict(out).to_canonical_dict()


async def generate_cv(
    facts: dict[str, Any],
    plan: dict[str, Any],
    job_analysis: dict[str, Any] | None = None,
    *,
    db=None,
    generate_fn: GenerateFn | None = None,
    use_llm: bool = False,
) -> dict[str, Any]:
    baseline = apply_plan_deterministically(facts, plan)
    if not use_llm:
        return baseline

    gen = generate_fn or generate
    prompt = render_prompt(
        "generate_cv.j2",
        language=(job_analysis or {}).get("language") or facts.get("language") or "de",
        role_family=plan.get("role_family") or "other",
        factlock_json=json.dumps(facts, ensure_ascii=False),
        plan_json=json.dumps(plan, ensure_ascii=False),
        job_analysis_json=json.dumps(job_analysis or {}, ensure_ascii=False),
    )
    try:
        raw = await gen(prompt, model_tier="strong", json_mode=True, temperature=0.3, db=db)
        data = json.loads(extract_json_text(raw))
        # force locked fields from master
        return _merge_locked_fields(facts, plan, data)
    except (LLMError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.info("generate_cv LLM failed, baseline used: %s", exc)
        return baseline


def _merge_locked_fields(
    facts: dict[str, Any], plan: dict[str, Any], generated: dict[str, Any]
) -> dict[str, Any]:
    base = apply_plan_deterministically(facts, plan)
    # take summary and bullet texts if present, but restore employer/title/dates
    if generated.get("summary"):
        base["summary"] = str(generated["summary"])[:800]
    gen_exps = {e.get("id"): e for e in generated.get("experience") or [] if e.get("id")}
    for exp in base["experience"]:
        ge = gen_exps.get(exp["id"])
        if not ge:
            continue
        # map bullets by id
        gbullets = {b.get("id"): b for b in ge.get("bullets") or []}
        new_bullets = []
        for b in exp.get("bullets") or []:
            gb = gbullets.get(b["id"])
            if gb and gb.get("text"):
                nb = dict(b)
                nb["text"] = str(gb["text"])
                new_bullets.append(nb)
            else:
                new_bullets.append(b)
        exp["bullets"] = new_bullets
    return validate_cv_dict(base).to_canonical_dict()
