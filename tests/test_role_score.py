from __future__ import annotations

from pathlib import Path

import pytest

from app.services.role_score import clear_domain_caches, detect_injection, score_roles

NEW_ROLE_FIXTURES = [
    ("job-cfo.txt", "cfo"),
    ("job-cso.txt", "cso_sales"),
    ("job-cto.txt", "cto"),
    ("job-head-ops.txt", "head_ops"),
    ("job-project.txt", "project"),
    ("job-consultant.txt", "consultant"),
    ("job-chro.txt", "chro"),
    ("job-product.txt", "product"),
    ("job-eng-lead.txt", "eng_lead"),
]


def _job(fixtures_dir: Path, name: str) -> str:
    return (fixtures_dir / name).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def _clear_caches():
    clear_domain_caches()
    yield
    clear_domain_caches()


def test_coo_job_detects_coo(fixtures_dir: Path):
    det = score_roles(_job(fixtures_dir, "job-coo.txt"))
    assert det["top"]["role_family"] == "coo"


def test_ceo_job_detects_ceo(fixtures_dir: Path):
    det = score_roles(_job(fixtures_dir, "job-ceo.txt"))
    assert det["top"]["role_family"] == "ceo"


def test_two_jobs_not_same_family(fixtures_dir: Path):
    a = score_roles(_job(fixtures_dir, "job-coo.txt"))["top"]["role_family"]
    b = score_roles(_job(fixtures_dir, "job-ceo.txt"))["top"]["role_family"]
    assert a != b


def test_injection_flagged(fixtures_dir: Path):
    text = _job(fixtures_dir, "job-inject.txt")
    assert detect_injection(text) is True
    det = score_roles(text)
    assert det["injection_risk"] is True
    assert det["top"]["role_family"] == "coo"


@pytest.mark.parametrize(("fixture", "family"), NEW_ROLE_FIXTURES)
def test_new_role_fixtures_detect_family(fixtures_dir: Path, fixture: str, family: str):
    det = score_roles(_job(fixtures_dir, fixture))
    assert det["top"]["role_family"] == family, det.get("scores")
