from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.models.schemas import CVStructure
from app.services.llm_client import LLMError, extract_json_text, generate
from app.services.prompt_loader import render_prompt

logger = logging.getLogger(__name__)

GenerateFn = Callable[..., Awaitable[str]]


class StructureError(Exception):
    def __init__(self, message: str, code: str = "structure_failed") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def validate_cv_dict(data: dict[str, Any]) -> CVStructure:
    return CVStructure.model_validate(data)


async def structure_cv_text(
    cv_text: str,
    *,
    db=None,
    generate_fn: GenerateFn | None = None,
) -> CVStructure:
    gen = generate_fn or generate
    prompt = render_prompt("structure_cv.j2", cv_text=cv_text)
    try:
        raw = await gen(
            prompt,
            model_tier="strong",
            json_mode=True,
            temperature=0.1,
            db=db,
        )
    except LLMError as exc:
        raise StructureError(exc.message, code=exc.code) from exc

    try:
        return _parse_cv_json(raw)
    except Exception as first_err:
        logger.info("cv structure invalid, trying repair: %s", first_err)
        repaired = await _repair_once(raw, str(first_err), gen=gen, db=db)
        try:
            return _parse_cv_json(repaired)
        except Exception as second_err:
            raise StructureError(
                f"CV-JSON ungültig nach Repair: {second_err}",
                code="invalid_json",
            ) from second_err


async def _repair_once(
    bad_json: str,
    error: str,
    *,
    gen: GenerateFn,
    db=None,
) -> str:
    prompt = render_prompt(
        "json_repair.j2",
        error=error,
        bad_json=extract_json_text(bad_json),
    )
    try:
        return await gen(
            prompt,
            model_tier="fast",
            json_mode=True,
            temperature=0.0,
            db=db,
        )
    except LLMError as exc:
        raise StructureError(exc.message, code=exc.code) from exc


def _parse_cv_json(raw: str) -> CVStructure:
    text = extract_json_text(raw)
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be object")
    return validate_cv_dict(data)
