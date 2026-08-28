from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Literal

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings, is_loopback_host
from app.models.orm import AppSettings

logger = logging.getLogger(__name__)

_semaphore = asyncio.Semaphore(1)


class LLMError(Exception):
    def __init__(self, message: str, code: str = "llm_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class OllamaUnavailable(LLMError):
    def __init__(self, message: str = "Ollama ist nicht erreichbar.") -> None:
        super().__init__(message, code="ollama_down")


def get_runtime_settings(db: Session | None = None) -> dict[str, str]:
    settings = get_settings()
    host = settings.ollama_host
    fast = settings.ollama_model_fast
    strong = settings.ollama_model_strong
    if db is not None:
        row = db.get(AppSettings, 1)
        if row is not None:
            host = row.ollama_host
            fast = row.model_fast
            strong = row.model_strong
    return {"ollama_host": host, "model_fast": fast, "model_strong": strong}


def ensure_host_allowed(host: str) -> None:
    settings = get_settings()
    if is_loopback_host(host):
        return
    if settings.ollama_allow_nonlocal:
        return
    raise LLMError(
        "OLLAMA_HOST muss Loopback sein (127.0.0.1/localhost), "
        "oder OLLAMA_ALLOW_NONLOCAL=true setzen.",
        code="host_not_allowed",
    )


def tag_looks_cloud(tag: str) -> bool:
    return "cloud" in (tag or "").lower()


async def list_models(host: str | None = None) -> list[str]:
    settings = get_settings()
    base = (host or settings.ollama_host).rstrip("/")
    ensure_host_allowed(base)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{base}/api/tags")
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        logger.info("ollama tags failed: %s", type(exc).__name__)
        raise OllamaUnavailable() from exc
    models = []
    for m in data.get("models") or []:
        name = m.get("name") or m.get("model")
        if name:
            models.append(name)
    return sorted(set(models))


async def check_health(db: Session | None = None) -> dict[str, Any]:
    rt = get_runtime_settings(db)
    host = rt["ollama_host"]
    selected = {"fast": rt["model_fast"], "strong": rt["model_strong"]}
    privacy_note = None
    if tag_looks_cloud(selected["fast"]) or tag_looks_cloud(selected["strong"]):
        privacy_note = "ollama_cloud_tag"
    if not is_loopback_host(host) and get_settings().ollama_allow_nonlocal:
        privacy_note = privacy_note or "ollama_nonlocal_host"

    result: dict[str, Any] = {
        "app": "ok",
        "ollama": "down",
        "models_installed": [],
        "selected": selected,
        "fast_present": False,
        "strong_present": False,
        "privacy_note": privacy_note,
        "ollama_host": host,
    }
    try:
        ensure_host_allowed(host)
        models = await list_models(host)
        result["ollama"] = "connected"
        result["models_installed"] = models
        result["fast_present"] = _tag_present(selected["fast"], models)
        result["strong_present"] = _tag_present(selected["strong"], models)
    except LLMError:
        pass
    except Exception:
        pass
    return result


def _tag_present(tag: str, models: list[str]) -> bool:
    if not tag:
        return False
    if tag in models:
        return True
    # ollama often returns name:tag; allow prefix match on base name
    base = tag.split(":")[0]
    return any(m == tag or m.startswith(tag) or m.split(":")[0] == base for m in models)


def _split_system_user(prompt: str) -> tuple[str, str]:
    if "---USER---" in prompt:
        system, user = prompt.split("---USER---", 1)
        return system.strip(), user.strip()
    return "", prompt.strip()


async def generate(
    prompt: str,
    *,
    model_tier: Literal["fast", "strong"] | None = None,
    model: str | None = None,
    json_mode: bool = False,
    timeout_s: int | None = None,
    temperature: float | None = None,
    db: Session | None = None,
) -> str:
    settings = get_settings()
    rt = get_runtime_settings(db)
    host = rt["ollama_host"].rstrip("/")
    ensure_host_allowed(host)

    if model:
        tag = model
    elif model_tier == "strong":
        tag = rt["model_strong"]
    else:
        tag = rt["model_fast"]

    if temperature is None:
        temperature = 0.1 if json_mode else 0.3
    timeout = timeout_s or (60 if model_tier == "fast" else settings.llm_timeout_s)

    system, user = _split_system_user(prompt)
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user or prompt})

    payload: dict[str, Any] = {
        "model": tag,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_ctx": 8192,
        },
    }
    if json_mode:
        payload["format"] = "json"

    async with _semaphore:
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    r = await client.post(f"{host}/api/chat", json=payload)
                    if r.status_code >= 500:
                        raise OllamaUnavailable(f"Ollama HTTP {r.status_code}")
                    r.raise_for_status()
                    data = r.json()
                    content = (
                        (data.get("message") or {}).get("content") or data.get("response") or ""
                    )
                    if not content:
                        raise LLMError("Leere Modell-Antwort.", code="empty_response")
                    return content
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_err = exc
                logger.warning(
                    "ollama transport attempt %s failed: %s", attempt + 1, type(exc).__name__
                )
                await asyncio.sleep(0.4 * (attempt + 1))
            except OllamaUnavailable:
                raise
            except httpx.HTTPStatusError as exc:
                raise LLMError(
                    f"Ollama-Fehler: HTTP {exc.response.status_code}",
                    code="ollama_http",
                ) from exc
        raise OllamaUnavailable(str(last_err) if last_err else "Ollama nicht erreichbar.")


def extract_json_text(raw: str) -> str:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence:
        return fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text
