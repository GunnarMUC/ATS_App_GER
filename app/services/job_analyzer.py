from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.services.llm_client import LLMError, extract_json_text, generate
from app.services.prompt_loader import render_prompt
from app.services.role_score import heuristic_job_analysis, score_roles

logger = logging.getLogger(__name__)
GenerateFn = Callable[..., Awaitable[str]]


async def analyze_and_detect(
    job_text: str,
    *,
    db=None,
    generate_fn: GenerateFn | None = None,
    use_llm: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (job_analysis, role_detection). Heuristic always; LLM optional enrich."""
    detection = score_roles(job_text)
    analysis = heuristic_job_analysis(job_text, detection)

    if not use_llm:
        return analysis, detection

    gen = generate_fn or generate
    hint = {
        "top": detection.get("top"),
        "candidates": detection.get("candidates"),
        "scores": detection.get("scores"),
    }
    prompt = render_prompt(
        "analyze_and_detect.j2",
        job_text=job_text[:12000],
        ranker_hint_json=json.dumps(hint, ensure_ascii=False),
    )
    try:
        raw = await gen(prompt, model_tier="fast", json_mode=True, temperature=0.1, db=db)
        data = json.loads(extract_json_text(raw))
        if isinstance(data.get("job_analysis"), dict):
            analysis = {**analysis, **data["job_analysis"]}
            analysis["schema_version"] = "1.0"
            analysis["injection_risk"] = (
                analysis.get("injection_risk") or detection["injection_risk"]
            )
        if isinstance(data.get("role_detection"), dict):
            # keep heuristic top if LLM disagrees weakly — prefer LLM only if confident
            rd = data["role_detection"]
            rd["injection_risk"] = rd.get("injection_risk") or detection["injection_risk"]
            rd["schema_version"] = "1.0"
            detection = rd
    except (LLMError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.info("analyze_and_detect LLM skipped: %s", exc)

    return analysis, detection
