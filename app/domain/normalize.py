from __future__ import annotations

import re
import unicodedata


def normalize_term(text: str) -> str:
    t = (text or "").lower().strip()
    t = t.replace("ß", "ss")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("&", "and")
    t = re.sub(r"[^a-z0-9]+", "", t)
    return t


def tokenize_meaningful(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-zÄÖÜäöüß0-9&+\-/]{2,}", text or "")
    out: list[str] = []
    for r in raw:
        n = normalize_term(r)
        if len(n) >= 2:
            out.append(n)
    return out
