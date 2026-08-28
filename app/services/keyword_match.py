from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.domain.normalize import normalize_term

_ALIASES_PATH = Path(__file__).resolve().parents[1] / "domain" / "aliases_de.json"


@lru_cache
def load_alias_map() -> dict[str, set[str]]:
    data = json.loads(_ALIASES_PATH.read_text(encoding="utf-8"))
    groups: dict[str, set[str]] = {}
    for a, b in data.get("pairs") or []:
        na, nb = normalize_term(a), normalize_term(b)
        if not na or not nb:
            continue
        root = groups.get(na) or groups.get(nb) or {na, nb}
        root.add(na)
        root.add(nb)
        for k in list(root):
            groups[k] = root
    return groups


def expand_aliases(term: str) -> set[str]:
    n = normalize_term(term)
    m = load_alias_map()
    if n in m:
        return set(m[n])
    return {n} if n else set()


def terms_match(a: str, b: str) -> bool:
    na, nb = normalize_term(a), normalize_term(b)
    if not na or not nb:
        return False
    if na == nb or na in nb or nb in na:
        return True
    ea, eb = expand_aliases(a), expand_aliases(b)
    return bool(ea & eb)


def find_in_text(keyword: str, text: str) -> bool:
    if not keyword or not text:
        return False
    nt = normalize_term(text)
    for cand in expand_aliases(keyword):
        if cand and cand in nt:
            return True
    return False


def extract_keyword_candidates(job_text: str, limit: int = 24) -> list[str]:
    """Lightweight keyword harvest without LLM — noun-ish tokens and known aliases."""

    alias_map = load_alias_map()
    known = set(alias_map.keys())
    text_n = normalize_term(job_text)
    hits: list[str] = []
    for k in sorted(known, key=len, reverse=True):
        if len(k) >= 3 and k in text_n:
            # prefer a readable form from pairs
            hits.append(k)
    # also keep distinctive raw phrases
    import re

    phrases = re.findall(
        r"\b(?:S&OP|OTIF|P&L|CEO|COO|CFO|3PL|SAP[\-\s]?WM|Control\s*Tower|Cost[\-\s]?to[\-\s]?serve)\b",
        job_text,
        flags=re.IGNORECASE,
    )
    for p in phrases:
        hits.append(p)
    # unique preserve order
    seen: set[str] = set()
    out: list[str] = []
    for h in hits:
        key = normalize_term(h)
        if key in seen:
            continue
        seen.add(key)
        out.append(h if not key.islower() or len(h) <= 12 else h)
        if len(out) >= limit:
            break
    return out


def coverage_against_facts(
    keywords: list[str],
    facts: dict[str, Any],
) -> list[dict[str, Any]]:
    blob_parts: list[str] = []
    for s in facts.get("skills") or []:
        blob_parts.append(s.get("name") or "")
        blob_parts.extend(s.get("aliases") or [])
    for e in facts.get("experience") or []:
        blob_parts.append(e.get("title") or "")
        blob_parts.append(e.get("employer") or "")
        for b in e.get("bullets") or []:
            blob_parts.append(b.get("text") or "")
    for k in facts.get("kpis") or []:
        blob_parts.append(k.get("label") or "")
        blob_parts.append(k.get("raw") or "")
        blob_parts.append(k.get("value") or "")
    blob = "\n".join(blob_parts)

    rows = []
    for kw in keywords:
        present = find_in_text(kw, blob)
        via_alias = False
        fact_id = None
        fact_kind = None
        if present:
            # try bind to skill
            for s in facts.get("skills") or []:
                if terms_match(kw, s.get("name") or "") or any(
                    terms_match(kw, a) for a in (s.get("aliases") or [])
                ):
                    fact_id = s["id"]
                    fact_kind = "skill"
                    via_alias = not terms_match(kw, s.get("name") or "")
                    break
            if not fact_id:
                for kpi in facts.get("kpis") or []:
                    if find_in_text(kw, f"{kpi.get('label', '')} {kpi.get('raw', '')}"):
                        fact_id = kpi["id"]
                        fact_kind = "kpi"
                        break
            if not fact_id:
                for e in facts.get("experience") or []:
                    for b in e.get("bullets") or []:
                        if find_in_text(kw, b.get("text") or ""):
                            fact_id = b["id"]
                            fact_kind = "bullet"
                            break
                    if fact_id:
                        break
        rows.append(
            {
                "job_keyword": kw,
                "present": present,
                "via_alias": via_alias,
                "fact_id": fact_id,
                "fact_kind": fact_kind,
            }
        )
    return rows
