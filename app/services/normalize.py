from __future__ import annotations

import re
import unicodedata


def normalize_term(text: str) -> str:
    t = (text or "").lower().replace("ß", "ss")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    t = re.sub(r"[&+/]", " ", t)
    t = re.sub(r"[^a-z0-9]+", "", t)
    return t


def normalize_loose(text: str) -> str:
    return normalize_term(text)
