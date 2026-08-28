from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.services.llm_client import LLMError, generate
from app.services.prompt_loader import render_prompt

logger = logging.getLogger(__name__)
GenerateFn = Callable[..., Awaitable[str]]


def build_cover_template(
    facts: dict[str, Any],
    plan: dict[str, Any],
    job_analysis: dict[str, Any] | None = None,
) -> str:
    p = facts.get("personal") or {}
    name = p.get("full_name") or ""
    city = p.get("city") or ""
    email = p.get("email") or ""
    phone = p.get("phone") or ""
    title = (job_analysis or {}).get("title") or "die ausgeschriebene Position"
    company = (job_analysis or {}).get("company") or ""
    form = (job_analysis or {}).get("form_of_address") or "sie"
    anrede = "Sehr geehrte Damen und Herren," if form != "du" else "Hallo,"
    lang = (job_analysis or {}).get("language") or "de"

    # pick 2 emphasis bullets
    bullet_ids = set(plan.get("emphasis_bullet_ids") or [])
    evidence = []
    for exp in facts.get("experience") or []:
        for b in exp.get("bullets") or []:
            if b.get("id") in bullet_ids:
                evidence.append(b.get("text") or "")
        if len(evidence) >= 2:
            break
    if not evidence:
        for exp in facts.get("experience") or []:
            for b in exp.get("bullets") or []:
                evidence.append(b.get("text") or "")
                if len(evidence) >= 2:
                    break
            if len(evidence) >= 2:
                break

    brief = plan.get("summary_brief") or ""
    e1 = evidence[0] if evidence else ""
    e2 = evidence[1] if len(evidence) > 1 else ""

    if lang == "en":
        lines = [
            name,
            f"{city}" if city else "",
            f"{phone} · {email}".strip(" ·"),
            "",
            f"Application: {title}",
            "",
            "Dear Sir or Madam," if form != "du" else "Hello,",
            "",
            f"I am applying for the role of {title}" + (f" at {company}." if company else "."),
            "",
            f"{brief}",
            "",
            e1,
            e2,
            "",
            "I look forward to a personal conversation.",
            "",
            "Kind regards,",
            name,
        ]
    else:
        lines = [
            name,
            city,
            f"{phone} · {email}".strip(" ·"),
            "",
            f"Betreff: Bewerbung als {title}",
            "",
            anrede,
            "",
            f"hiermit bewerbe ich mich um die Position „{title}“"
            + (f" bei {company}." if company else "."),
            "",
            brief,
            "",
            e1,
            e2,
            "",
            "Über die Einladung zu einem persönlichen Gespräch freue ich mich.",
            "",
            "Mit freundlichen Grüßen",
            name,
        ]
    text = "\n".join(x for x in lines if x is not None)
    # hard limit ~380 words
    words = text.split()
    if len(words) > 380:
        text = " ".join(words[:380])
    return text.strip() + "\n"


async def generate_cover(
    facts: dict[str, Any],
    plan: dict[str, Any],
    job_analysis: dict[str, Any] | None = None,
    job_text: str = "",
    *,
    db=None,
    generate_fn: GenerateFn | None = None,
    use_llm: bool = False,
) -> str:
    baseline = build_cover_template(facts, plan, job_analysis)
    if not use_llm:
        return baseline
    gen = generate_fn or generate
    prompt = render_prompt(
        "generate_cover.j2",
        factlock_json=json.dumps(facts, ensure_ascii=False),
        plan_json=json.dumps(plan, ensure_ascii=False),
        job_analysis_json=json.dumps(job_analysis or {}, ensure_ascii=False),
        job_text=(job_text or "")[:3000],
    )
    try:
        raw = await gen(prompt, model_tier="strong", json_mode=False, temperature=0.4, db=db)
        text = (raw or "").strip()
        if len(text) < 80:
            return baseline
        words = text.split()
        if len(words) > 380:
            text = " ".join(words[:380])
        return text + ("\n" if not text.endswith("\n") else "")
    except LLMError as exc:
        logger.info("cover LLM failed: %s", exc)
        return baseline
