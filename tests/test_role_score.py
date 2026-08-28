from __future__ import annotations

from pathlib import Path

from app.services.role_score import detect_injection, score_roles


def _job(fixtures_dir: Path, name: str) -> str:
    return (fixtures_dir / name).read_text(encoding="utf-8")


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
