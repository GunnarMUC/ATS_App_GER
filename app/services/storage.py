from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.config import get_settings


def secure_filename(name: str) -> str:
    base = Path(name).name
    base = base.replace("\\", "_").replace("/", "_")
    base = re.sub(r"[^\w.\- äöüÄÖÜß()]+", "_", base, flags=re.UNICODE)
    base = base.strip(" ._") or "upload"
    return base[:180]


def store_upload(data: bytes, original_filename: str) -> tuple[str, Path]:
    settings = get_settings()
    settings.ensure_dirs()
    safe = secure_filename(original_filename)
    stored_name = f"{uuid.uuid4().hex}_{safe}"
    path = settings.uploads_dir / stored_name
    path.write_bytes(data)
    return stored_name, path
