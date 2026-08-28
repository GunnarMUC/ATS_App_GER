from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.domain.normalize import normalize_term
from app.services.keyword_match import terms_match


@dataclass
class GuardResult:
    ok: bool
    errors: list[str] = field(default_factory=list)


_NUMBER_RE = re.compile(
    r"(?<![A-Za-z])(\d+(?:[.,]\d+)?)\s*(%|Mio\.?|FTE|pp|EUR|€|Tag|Tage|Wochen|Monate)?",
    re.IGNORECASE,
)


def _norm_employer(s: str) -> str:
    return normalize_term(s)


def _allowed_numbers(facts: dict[str, Any]) -> set[str]:
    allowed: set[str] = set()
    for kpi in facts.get("kpis") or []:
        for src in (kpi.get("value"), kpi.get("raw"), kpi.get("label")):
            for m in _NUMBER_RE.finditer(src or ""):
                allowed.add(_num_key(m.group(1)))
    for exp in facts.get("experience") or []:
        for d in (exp.get("start"), exp.get("end")):
            if d and d != "present":
                allowed.add(_num_key(str(d)[:4]))
                if len(str(d)) >= 7:
                    allowed.add(_num_key(str(d)[5:7]))
        for b in exp.get("bullets") or []:
            for m in _NUMBER_RE.finditer(b.get("text") or ""):
                allowed.add(_num_key(m.group(1)))
    for edu in facts.get("education") or []:
        for d in (edu.get("start"), edu.get("end")):
            if d:
                allowed.add(_num_key(str(d)[:4]))
    # phone fragments ignored later
    return allowed


def _num_key(raw: str) -> str:
    return raw.replace(",", ".").lstrip("0") or "0"


def validate_generated_cv(master: dict[str, Any], generated: dict[str, Any]) -> GuardResult:
    errors: list[str] = []
    master_exps = {e["id"]: e for e in master.get("experience") or []}
    gen_exps = generated.get("experience") or []

    master_employers = {_norm_employer(e.get("employer") or "") for e in master_exps.values()}

    for ge in gen_exps:
        eid = ge.get("id")
        if eid not in master_exps:
            errors.append(f"Unbekannte experience id: {eid}")
            continue
        me = master_exps[eid]
        if _norm_employer(ge.get("employer") or "") != _norm_employer(me.get("employer") or ""):
            errors.append(f"Employer geändert bei {eid}: {ge.get('employer')}")
        if (ge.get("title") or "") != (me.get("title") or ""):
            errors.append(f"Titel-Feld geändert bei {eid}: {ge.get('title')}")
        if (ge.get("start") or "") != (me.get("start") or ""):
            errors.append(f"Start-Datum geändert bei {eid}")
        if (ge.get("end") or "") != (me.get("end") or ""):
            errors.append(f"End-Datum geändert bei {eid}")

    # no new employers anywhere in narrative? check experience only for employer field
    for ge in gen_exps:
        emp = ge.get("employer") or ""
        if _norm_employer(emp) and _norm_employer(emp) not in master_employers:
            errors.append(f"Neuer Employer: {emp}")

    # skills
    master_skills = {s["id"]: s for s in master.get("skills") or []}
    for sk in generated.get("skills") or []:
        sid = sk.get("id")
        name = sk.get("name") or ""
        if sid and sid in master_skills:
            continue
        # allow if name matches master skill or alias
        ok = False
        for ms in master_skills.values():
            if terms_match(name, ms.get("name") or "") or any(
                terms_match(name, a) for a in (ms.get("aliases") or [])
            ):
                ok = True
                break
        if not ok:
            errors.append(f"Neuer Skill: {name}")

    # education institutions
    master_edu = {(e.get("institution") or "", e.get("degree") or "") for e in master.get("education") or []}
    for ed in generated.get("education") or []:
        key = (ed.get("institution") or "", ed.get("degree") or "")
        if key not in master_edu and (ed.get("institution") or ed.get("degree")):
            # allow subset match on institution
            inst = ed.get("institution") or ""
            if not any(terms_match(inst, m[0]) for m in master_edu if m[0]):
                errors.append(f"Neue Ausbildung: {inst} / {ed.get('degree')}")

    allowed_nums = _allowed_numbers(master)
    # scan generated narrative fields
    narrative_parts: list[str] = [generated.get("summary") or ""]
    for ge in gen_exps:
        for b in ge.get("bullets") or []:
            narrative_parts.append(b.get("text") or "")
    blob = "\n".join(narrative_parts)
    phone = (master.get("personal") or {}).get("phone") or ""
    for m in _NUMBER_RE.finditer(blob):
        num = m.group(1)
        key = _num_key(num)
        # skip years already in dates / phone
        if phone and num in phone.replace(" ", ""):
            continue
        if key not in allowed_nums:
            # allow pure year if in master years
            if re.fullmatch(r"19\d{2}|20\d{2}", num) and key in allowed_nums:
                continue
            if re.fullmatch(r"19\d{2}|20\d{2}", num) and key in allowed_nums:
                continue
            errors.append(f"Zahl ohne Herkunft: {m.group(0).strip()}")

    return GuardResult(ok=len(errors) == 0, errors=errors)


def validate_cover_text(master: dict[str, Any], cover: str) -> GuardResult:
    errors: list[str] = []
    master_employers = [
        e.get("employer") or "" for e in master.get("experience") or []
    ]
    # reject known fake
    banned = ["mckinsey", "harvard", "ifrs", "private equity exit"]
    low = (cover or "").lower()
    for b in banned:
        if b in low and not any(b in (e or "").lower() for e in master_employers):
            # only ban if not in master text
            master_blob = json_blob(master).lower()
            if b not in master_blob:
                errors.append(f"Cover enthält unzulässigen Begriff: {b}")

    # employers mentioned must be subset
    for emp in master_employers:
        pass
    # new employer heuristic: capitalized multi-word GmbH not in master
    for m in re.finditer(r"\b([A-ZÄÖÜ][\w\-]+(?:\s+[A-ZÄÖÜ][\w\-]+)*)\s+(GmbH|AG|KG)\b", cover or ""):
        name = m.group(0)
        if not any(terms_match(name, e) for e in master_employers):
            errors.append(f"Unbekannter Arbeitgeber im Anschreiben: {name}")

    allowed_nums = _allowed_numbers(master)
    phone = (master.get("personal") or {}).get("phone") or ""
    for m in _NUMBER_RE.finditer(cover or ""):
        num = m.group(1)
        if phone and num in phone.replace(" ", ""):
            continue
        key = _num_key(num)
        if key not in allowed_nums:
            errors.append(f"Zahl ohne Herkunft im Anschreiben: {m.group(0).strip()}")

    return GuardResult(ok=len(errors) == 0, errors=errors)


def json_blob(facts: dict[str, Any]) -> str:
    import json

    return json.dumps(facts, ensure_ascii=False)
