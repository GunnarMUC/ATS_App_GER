from __future__ import annotations

import json
from pathlib import Path

from app.services.lens_ranker import build_plan_skeleton
from app.services.role_score import heuristic_job_analysis, score_roles


def test_plan_orders_differ_ceo_vs_coo(fixtures_dir: Path):
    facts = json.loads((fixtures_dir / "master-cv.json").read_text(encoding="utf-8"))
    coo_job = (fixtures_dir / "job-coo.txt").read_text(encoding="utf-8")
    ceo_job = (fixtures_dir / "job-ceo.txt").read_text(encoding="utf-8")
    coo_an = heuristic_job_analysis(coo_job, score_roles(coo_job))
    ceo_an = heuristic_job_analysis(ceo_job, score_roles(ceo_job))
    coo = build_plan_skeleton(facts, role_family="coo", job_analysis=coo_an)
    ceo = build_plan_skeleton(facts, role_family="ceo", job_analysis=ceo_an)

    assert set(coo["experience_order"]) | set(coo["hidden_experience_ids"]) <= {
        e["id"] for e in facts["experience"]
    }
    assert set(coo["hidden_experience_ids"]).issubset({e["id"] for e in facts["experience"]})
    # skill emphasis differs
    assert (
        coo["skill_order"][0] != ceo["skill_order"][0]
        or set(coo["emphasis_kpi_ids"]) != set(ceo["emphasis_kpi_ids"])
        or set(coo["emphasis_bullet_ids"]) != set(ceo["emphasis_bullet_ids"])
    )
    assert "kpi_otif" in coo["emphasis_kpi_ids"] or "sk_otif" in coo["skill_order"][:4]
    assert "kpi_revenue" in ceo["emphasis_kpi_ids"] or "sk_pl" in ceo["skill_order"][:4]
    assert "McKinsey" not in json.dumps(coo)
    assert coo["summary_brief"] != ceo["summary_brief"]
