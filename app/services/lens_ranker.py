from __future__ import annotations

from typing import Any

from app.domain.normalize import normalize_term
from app.domain.role_taxonomy import LABELS_DE
from app.services.keyword_match import coverage_against_facts, expand_aliases, find_in_text
from app.services.role_score import load_weights


def build_plan_skeleton(
    facts: dict[str, Any],
    *,
    role_family: str,
    job_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    weights = load_weights()
    cfg = (weights.get("role_family_weights") or {}).get(role_family) or {
        "terms": [],
        "downweight_terms": [],
    }
    boost_terms = [normalize_term(t) for t in (cfg.get("terms") or [])]
    boost_set: set[str] = set()
    for t in boost_terms:
        boost_set |= expand_aliases(t) | {t}
    down_set: set[str] = set()
    for t in cfg.get("downweight_terms") or []:
        down_set |= expand_aliases(t) | {normalize_term(t)}

    must = list((job_analysis or {}).get("must_keywords") or [])
    nice = list((job_analysis or {}).get("nice_keywords") or [])
    all_kw = must + nice

    exp_scores: list[tuple[str, float, dict]] = []
    for exp in facts.get("experience") or []:
        blob = " ".join(
            [
                exp.get("title") or "",
                exp.get("employer") or "",
                " ".join(b.get("text") or "" for b in exp.get("bullets") or []),
            ]
        )
        bn = normalize_term(blob)
        score = 0.0
        for t in boost_set:
            if t and t in bn:
                score += 1.2
        for t in down_set:
            if t and t in bn:
                score -= 0.6
        for kw in must:
            if find_in_text(kw, blob):
                score += 1.5
        for kw in nice:
            if find_in_text(kw, blob):
                score += 0.4
        # recency light boost
        start = exp.get("start") or "0000"
        try:
            year = int(str(start)[:4])
            score += (year - 2000) * 0.02
        except ValueError:
            pass
        exp_scores.append((exp["id"], score, exp))

    exp_scores.sort(key=lambda x: x[1], reverse=True)
    order = [e[0] for e in exp_scores]
    hidden: list[str] = []
    # hide only clearly weak and not first two
    if len(exp_scores) > 2:
        for eid, sc, _ in exp_scores[2:]:
            if sc < 0.3:
                hidden.append(eid)
        order = [e for e in order if e not in hidden] + hidden
        # final experience_order excludes hidden per schema practice — keep all non-hidden first
        order = [e for e in order if e not in hidden]

    # skills
    skill_scores: list[tuple[str, float]] = []
    for sk in facts.get("skills") or []:
        blob = " ".join([sk.get("name") or ""] + list(sk.get("aliases") or []))
        bn = normalize_term(blob)
        sc = 0.0
        for t in boost_set:
            if t and t in bn:
                sc += 1.5
        for kw in must:
            if find_in_text(kw, blob):
                sc += 1.2
        skill_scores.append((sk["id"], sc))
    skill_scores.sort(key=lambda x: x[1], reverse=True)
    skill_order = [s[0] for s in skill_scores]

    # bullets / kpis emphasis
    emphasis_bullets: list[tuple[str, float]] = []
    for exp in facts.get("experience") or []:
        if exp["id"] in hidden:
            continue
        for b in exp.get("bullets") or []:
            bt = b.get("text") or ""
            bn = normalize_term(bt)
            sc = 0.0
            for t in boost_set:
                if t and t in bn:
                    sc += 1.0
            for kw in must:
                if find_in_text(kw, bt):
                    sc += 1.0
            emphasis_bullets.append((b["id"], sc))
    emphasis_bullets.sort(key=lambda x: x[1], reverse=True)
    emphasis_bullet_ids = [b[0] for b in emphasis_bullets if b[1] > 0][:8]

    emphasis_kpis: list[tuple[str, float]] = []
    for kpi in facts.get("kpis") or []:
        blob = f"{kpi.get('label', '')} {kpi.get('raw', '')}"
        bn = normalize_term(blob)
        sc = 0.0
        for t in boost_set:
            if t and t in bn:
                sc += 1.2
        for kw in must:
            if find_in_text(kw, blob):
                sc += 1.0
        kpi_terms = [normalize_term(t) for t in (cfg.get("kpi_terms") or [])]
        if any(x and x in bn for x in kpi_terms):
            sc += 0.8
        emphasis_kpis.append((kpi["id"], sc))
    emphasis_kpis.sort(key=lambda x: x[1], reverse=True)
    emphasis_kpi_ids = [k[0] for k in emphasis_kpis if k[1] > 0][:6]

    cov = coverage_against_facts(all_kw or must, facts)
    bindings = []
    gaps = []
    for row in cov:
        if row["present"] and row["fact_id"] and row["fact_kind"]:
            bindings.append(
                {
                    "job_keyword": row["job_keyword"],
                    "fact_kind": row["fact_kind"],
                    "fact_id": row["fact_id"],
                    "via_alias": bool(row.get("via_alias")),
                }
            )
        elif not row["present"] and row["job_keyword"] in must:
            gaps.append(
                {
                    "job_keyword": row["job_keyword"],
                    "severity": "must",
                    "message_de": (
                        f"Die Stelle verlangt {row['job_keyword']}. "
                        "Das steht nicht in Ihren Fakten. Wir erfinden es nicht."
                    ),
                }
            )

    brief = _template_brief(role_family, emphasis_kpi_ids, facts)

    # ensure experience_order has all non-hidden
    all_ids = [e["id"] for e in facts.get("experience") or []]
    for eid in all_ids:
        if eid not in hidden and eid not in order:
            order.append(eid)

    return {
        "schema_version": "1.0",
        "role_family": role_family,
        "experience_order": order,
        "hidden_experience_ids": hidden,
        "skill_order": skill_order,
        "emphasis_kpi_ids": emphasis_kpi_ids,
        "emphasis_bullet_ids": emphasis_bullet_ids,
        "summary_brief": brief,
        "keyword_bindings": bindings,
        "gaps": gaps,
        "warnings_de": _warnings(role_family, facts),
        "coverage": cov,
    }


def _template_brief(role_family: str, kpi_ids: list[str], facts: dict[str, Any]) -> str:
    label = LABELS_DE.get(role_family, role_family)
    kpi_map = {k["id"]: k for k in facts.get("kpis") or []}
    bits = []
    for kid in kpi_ids[:4]:
        k = kpi_map.get(kid)
        if k:
            bits.append(f"{k.get('label')} {k.get('value')}".strip())
    focus = {
        "ceo": "P&L, Organisation, unternehmerische Ownership",
        "coo": "OTIF, S&OP, Delivery, operative Exzellenz",
        "cfo": "Finanzen, Controlling, Kapital",
        "cso_sales": "Pipeline, Key Accounts, Wachstum",
        "cto": "Technologie, Architektur, Engineering-Organisation",
        "chro": "Personal, Talent, Organisation",
        "head_ops": "Tagesgeschäft, SLA, operative Prozesse",
        "head_logistics": "Netz, Lager, Transport, OTIF",
        "plant_ops": "Produktion, OEE, Safety",
        "program": "Governance, Change, Multi-Projekt",
        "project": "Scope, Meilensteine, Stakeholder",
        "consultant": "Analyse, Empfehlung, Mandanten",
        "product": "Roadmap, Discovery, Go-to-Market",
        "eng_lead": "Engineering-Führung, Plattform, Delivery",
    }.get(role_family, "rollenspezifische Schwerpunkte aus den Fakten")
    extra = ("; ".join(bits)) if bits else ""
    text = f"{label}: {focus}."
    if extra:
        text += f" Betonung: {extra}."
    text += " Keine neuen Fakten."
    return text[:600]


def _warnings(role_family: str, facts: dict[str, Any]) -> list[str]:
    out = []
    if role_family == "ceo":
        titles = {e.get("title") for e in facts.get("experience") or []}
        if "Geschäftsleitung Operations" in titles:
            out.append("Titel bleibt „Geschäftsleitung Operations“. Kein Umbennen in CEO.")
    return out
