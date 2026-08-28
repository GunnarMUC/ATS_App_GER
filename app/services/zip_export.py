from __future__ import annotations

import zipfile
from datetime import UTC, datetime
from io import BytesIO
from typing import Any


def build_application_zip(
    *,
    role: str,
    company: str,
    version: int,
    cv_docx: bytes,
    cv_pdf: bytes,
    cv_txt: bytes,
    cover_docx: bytes | None = None,
    cover_pdf: bytes | None = None,
    cover_txt: str | None = None,
    meta: dict[str, Any] | None = None,
) -> bytes:
    day = datetime.now(UTC).strftime("%Y%m%d")
    safe_role = _safe(role or "Rolle")
    safe_co = _safe(company or "Firma")
    root = f"Bewerbung_{safe_role}_{safe_co}_{day}"
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{root}/Lebenslauf_v{version}.docx", cv_docx)
        zf.writestr(f"{root}/Lebenslauf_v{version}.pdf", cv_pdf)
        zf.writestr(f"{root}/Lebenslauf_v{version}.txt", cv_txt)
        if cover_docx:
            zf.writestr(f"{root}/Anschreiben_v{version}.docx", cover_docx)
        if cover_pdf:
            zf.writestr(f"{root}/Anschreiben_v{version}.pdf", cover_pdf)
        if cover_txt:
            zf.writestr(f"{root}/Anschreiben_v{version}.txt", cover_txt.encode("utf-8"))
        inhalt = [
            f"Stelle: {(meta or {}).get('title', '')}",
            f"Rolle: {role}",
            f"Sprache: {(meta or {}).get('language', '')}",
            f"Version: {version}",
            f"Faktenstand: {(meta or {}).get('hash', '')}",
            "lokal erzeugt",
        ]
        zf.writestr(f"{root}/INHALT.txt", "\n".join(inhalt) + "\n")
    return buf.getvalue()


def _safe(s: str) -> str:
    out = []
    for ch in s:
        if ch.isalnum() or ch in "-_":
            out.append(ch)
        elif ch in " äöüÄÖÜß":
            out.append(ch.strip() or "_")
        else:
            out.append("_")
    return "".join(out)[:40] or "x"
