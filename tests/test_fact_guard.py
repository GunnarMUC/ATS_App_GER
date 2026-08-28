from __future__ import annotations

import copy
import json
from pathlib import Path

from app.services.cv_generator import apply_plan_deterministically
from app.services.fact_guard import validate_cover_text, validate_generated_cv
from app.services.lens_ranker import build_plan_skeleton


def _master(fixtures_dir: Path) -> dict:
    return json.loads((fixtures_dir / "master-cv.json").read_text(encoding="utf-8"))


def test_guard_accepts_reordered_experience(fixtures_dir: Path):
    m = _master(fixtures_dir)
    g = copy.deepcopy(m)
    g["experience"] = list(reversed(g["experience"]))
    assert validate_generated_cv(m, g).ok


def test_guard_accepts_rephrased_bullet_without_new_numbers(fixtures_dir: Path):
    m = _master(fixtures_dir)
    g = copy.deepcopy(m)
    g["experience"][0]["bullets"][0]["text"] = (
        "Verantwortung für das operative Geschäft inklusive bestehender Kennzahlen."
    )
    assert validate_generated_cv(m, g).ok


def test_guard_rejects_new_employer(fixtures_dir: Path):
    m = _master(fixtures_dir)
    g = copy.deepcopy(m)
    g["experience"][0]["employer"] = "McKinsey"
    r = validate_generated_cv(m, g)
    assert not r.ok


def test_guard_rejects_title_changed_to_ceo(fixtures_dir: Path):
    m = _master(fixtures_dir)
    g = copy.deepcopy(m)
    g["experience"][0]["title"] = "CEO"
    r = validate_generated_cv(m, g)
    assert not r.ok


def test_guard_rejects_invented_kpi(fixtures_dir: Path):
    m = _master(fixtures_dir)
    g = copy.deepcopy(m)
    g["experience"][0]["bullets"][1]["text"] = "OTIF +40 pp gesteigert."
    r = validate_generated_cv(m, g)
    assert not r.ok


def test_guard_rejects_new_skill_entity(fixtures_dir: Path):
    m = _master(fixtures_dir)
    g = copy.deepcopy(m)
    g["skills"].append({"id": "sk_ifrs", "name": "IFRS", "aliases": [], "category": "functional"})
    r = validate_generated_cv(m, g)
    assert not r.ok


def test_guard_allows_alias_project_management(fixtures_dir: Path):
    m = _master(fixtures_dir)
    g = copy.deepcopy(m)
    # rename display via alias of existing skill
    for s in g["skills"]:
        if s["id"] == "sk_projects":
            s["name"] = "Project Management"
    assert validate_generated_cv(m, g).ok


def test_guard_rejects_date_shift(fixtures_dir: Path):
    m = _master(fixtures_dir)
    g = copy.deepcopy(m)
    g["experience"][0]["start"] = "2018-03"
    assert not validate_generated_cv(m, g).ok


def test_guard_numbers_need_kpi_or_field_origin(fixtures_dir: Path):
    m = _master(fixtures_dir)
    g = copy.deepcopy(m)
    g["summary"] = "Ich steigerte etwas um 99 Prozentpunkte."
    assert not validate_generated_cv(m, g).ok
    g2 = copy.deepcopy(m)
    g2["summary"] = "OTIF um 12 Prozentpunkte verbessert."
    assert validate_generated_cv(m, g2).ok


def test_deterministic_cv_passes_guard(fixtures_dir: Path):
    m = _master(fixtures_dir)
    plan = build_plan_skeleton(m, role_family="coo")
    g = apply_plan_deterministically(m, plan)
    r = validate_generated_cv(m, g)
    assert r.ok, r.errors


def test_cover_rejects_mckinsey(fixtures_dir: Path):
    m = _master(fixtures_dir)
    bad = "Ich war CEO bei McKinsey von 2010 bis 2018."
    assert not validate_cover_text(m, bad).ok
