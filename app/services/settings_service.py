from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.config import get_settings, is_loopback_host
from app.models.orm import AppSettings
from app.services.llm_client import LLMError, ensure_host_allowed


def ensure_settings_row(db: Session) -> AppSettings:
    row = db.get(AppSettings, 1)
    if row is not None:
        return row
    s = get_settings()
    row = AppSettings(
        id=1,
        ollama_host=s.ollama_host,
        model_fast=s.ollama_model_fast,
        model_strong=s.ollama_model_strong,
        updated_at=datetime.now(UTC),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_settings(
    db: Session,
    *,
    ollama_host: str | None = None,
    model_fast: str | None = None,
    model_strong: str | None = None,
) -> AppSettings:
    row = ensure_settings_row(db)
    if ollama_host is not None:
        host = ollama_host.strip().rstrip("/")
        if not host.startswith("http"):
            host = f"http://{host}"
        try:
            ensure_host_allowed(host)
        except LLMError:
            if not is_loopback_host(host) and not get_settings().ollama_allow_nonlocal:
                raise
        row.ollama_host = host
    if model_fast is not None:
        row.model_fast = model_fast.strip()
    if model_strong is not None:
        row.model_strong = model_strong.strip()
    row.updated_at = datetime.now(UTC)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
