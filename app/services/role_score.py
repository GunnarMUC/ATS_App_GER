from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.domain.normalize import normalize_term
from app.domain.role_taxonomy import LABELS_DE, ROLE_FAMILIES
from app.services.keyword_match import expand_aliases, find_in_text, load_alias_map

_WEIGHTS_PATH = Path(__file__).resolve().parents[1] / "domain" / "lens_weights.json"

INJECTION_PATTERNS = [
    r"ignore\s+all\s+previous",
    r"ignoriere\s+alle\s+(vorherigen\s+)?regeln",
    r"rewrite\s+the\s+candidate",
    r"set\s+ats\s+score",
    r"upload\s+the\s+cv\s+to\s+https?://",
    r"---\s*system\s*---",
]


@lru_cache
def load_weights() -> dict[str, Any]:
    return json.loads(_WEIGHTS_PATH.read_text(encoding="utf-8"))


def clear_domain_caches() -> None:
    load_weights.cache_clear()
    load_alias_map.cache_clear()


def detect_injection(text: str) -> bool:
    low = (text or "").lower()
    return any(re.search(p, low) for p in INJECTION_PATTERNS)


def detect_form_of_address(text: str) -> str:
    t = text or ""
    du_hits = len(re.findall(r"\b(du|dich|dir|dein|deine)\b", t, flags=re.I))
    sie_hits = len(re.findall(r"\b(sie|ihnen|ihr|ihre)\b", t, flags=re.I))
    # German job ads often use Sie capitalized mid-sentence
    if sie_hits >= du_hits and sie_hits > 0:
        return "sie"
    if du_hits > sie_hits:
        return "du"
    if "Sie-Form" in t or "Sie form" in t:
        return "sie"
    return "unknown"


def detect_language(text: str) -> str:
    t = text or ""
    de_markers = len(re.findall(r"\b(und|für|mit|Sie|Geschäfts|Erfahrung|Bewerbung)\b", t))
    en_markers = len(
        re.findall(r"\b(the|and|with|you|experience|role|responsibilities)\b", t, re.I)
    )
    return "de" if de_markers >= en_markers else "en"


def score_roles(job_text: str) -> dict[str, Any]:
    weights = load_weights()
    margin = float(weights.get("margin_for_top1") or 0.15)
    families = weights.get("role_family_weights") or {}
    text_n = normalize_term(job_text)
    raw = job_text or ""

    scores: dict[str, float] = {f: 0.0 for f in ROLE_FAMILIES}
    for family, cfg in families.items():
        if family not in scores:
            continue
        terms = cfg.get("terms") or []
        down = cfg.get("downweight_terms") or []
        s = 0.0
        for term in terms:
            variants = expand_aliases(term) | {normalize_term(term)}
            for v in variants:
                if v and v in text_n:
                    # longer terms weigh more
                    s += 1.0 + min(len(v), 20) / 40.0
                    break
            # also original readable match
            if find_in_text(term, raw):
                s += 0.25
        for term in down:
            v = normalize_term(term)
            if v and v in text_n:
                s -= 0.8
        scores[family] = max(0.0, s)

    first_line = (raw.strip().splitlines() or [""])[0]
    fl = normalize_term(first_line)
    for family, cfg in families.items():
        if family not in scores:
            continue
        for term in cfg.get("title_terms") or []:
            v = normalize_term(term)
            if v and v in fl:
                scores[family] += 4.0
                break
    if "geschaeftsleitungoperations" in fl or ("geschaeftsleitung" in fl and "operation" in fl):
        scores["coo"] += 3.5
        scores["ceo"] -= 0.5
    # body disambiguation: CEO ads stress P&L/Beirat; COO stress OTIF/S&OP
    if any(x in text_n for x in ("beirat", "gesellschafter", "gesamtverantwortung", "pandl")):
        scores["ceo"] += 2.0
    if any(x in text_n for x in ("otif", "sop", "costtoserve", "controltower", "3pl", "shopfloor")):
        scores["coo"] += 2.0
    if "wir suchen keine operative" in raw.lower() or "nicht eine rein funktionale" in raw.lower():
        scores["ceo"] += 2.5
        scores["coo"] -= 1.0

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_name, top_score = ranked[0]
    second_name, second_score = ranked[1] if len(ranked) > 1 else ("other", 0.0)

    def conf(name: str, sc: float) -> float:
        base = sc / (top_score + second_score + 1e-6) if top_score else 0.0
        return round(min(0.99, max(0.05, base)), 3)

    gap = (top_score - second_score) / (top_score + 1e-6) if top_score else 0.0
    confident_top1 = gap >= margin and top_score > 0

    candidates = []
    for name, sc in ranked[:5]:
        if sc <= 0 and name not in {top_name, second_name}:
            continue
        candidates.append(
            {
                "role_family": name,
                "label_de": LABELS_DE.get(name, name),
                "confidence": conf(name, sc),
                "score_raw": round(sc, 3),
            }
        )
    if not candidates:
        candidates = [
            {
                "role_family": "other",
                "label_de": LABELS_DE["other"],
                "confidence": 0.2,
                "score_raw": 0.0,
            }
        ]

    # normalize confidences to sum-ish reasonable top
    top = candidates[0]
    injection = detect_injection(raw)

    return {
        "schema_version": "1.0",
        "language": detect_language(raw),
        "form_of_address": detect_form_of_address(raw),
        "formality": "formal" if detect_form_of_address(raw) == "sie" else "unknown",
        "industry_hints": [],
        "company_size_hint": "unknown",
        "injection_risk": injection,
        "top": {
            "role_family": top["role_family"],
            "label_de": top["label_de"],
            "confidence": top["confidence"],
        },
        "candidates": [
            {
                "role_family": c["role_family"],
                "label_de": c["label_de"],
                "confidence": c["confidence"],
            }
            for c in candidates
        ],
        "rationale": "Heuristik role_score + lens_weights",
        "confident_top1": confident_top1,
        "scores": {k: round(v, 3) for k, v in ranked},
    }


def heuristic_job_analysis(
    job_text: str, role_detection: dict[str, Any] | None = None
) -> dict[str, Any]:
    from app.services.keyword_match import extract_keyword_candidates

    det = role_detection or score_roles(job_text)
    kws = extract_keyword_candidates(job_text)
    title = (job_text.strip().splitlines() or ["Stelle"])[0][:200]
    company = None
    m = re.search(
        r"\b([A-ZÄÖÜ][\w\-]*(?:\s+[A-ZÄÖÜ][\w\-]*)*\s+(?:GmbH|AG|KG|SE|Ltd|Inc)\.?)\b",
        job_text,
    )
    if m:
        company = m.group(1)

    must = kws[:12]
    nice = kws[12:20]
    # compact requirements: first 1500 chars of body
    body = "\n".join((job_text or "").splitlines()[1:])[:4000]

    return {
        "schema_version": "1.0",
        "title": title,
        "company": company,
        "language": det.get("language") or "de",
        "form_of_address": det.get("form_of_address") or "unknown",
        "formality": det.get("formality") or "unknown",
        "must_keywords": must or ["Operations"],
        "nice_keywords": nice,
        "requirements_compact": body or job_text[:2000],
        "seniority_hint": det.get("top", {}).get("role_family", ""),
        "injection_risk": bool(det.get("injection_risk")),
    }
