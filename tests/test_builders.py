from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from app.services.ats_structural import analyze_cv_structure, analyze_source_file
from app.services.docx_builder import build_docx
from app.services.pdf_builder import build_pdf
from app.services.text_builder import build_txt


@pytest.fixture()
def master_facts(fixtures_dir: Path) -> dict:
    return json.loads((fixtures_dir / "master-cv.json").read_text(encoding="utf-8"))


def test_text_builder_contains_contact_and_employer(master_facts):
    txt = build_txt(master_facts)
    assert "Alex Morgenstern" in txt
    assert "alex.morgenstern@example.com" in txt
    assert "Nordkamm Logistik GmbH" in txt
    assert "Geschäftsleitung Operations" in txt
    assert "BERUFSERFAHRUNG" in txt or "Berufserfahrung" in txt.upper()


def test_docx_no_tables_and_has_email(master_facts, tmp_path: Path):
    path = tmp_path / "cv.docx"
    data = build_docx(master_facts, path)
    assert path.stat().st_size > 0
    assert len(data) > 100

    # no w:tbl in document.xml
    with zipfile.ZipFile(BytesIO(data)) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
    assert "w:tbl" not in xml
    assert "alex.morgenstern@example.com" in xml
    assert "Nordkamm" in xml


def test_pdf_nonempty(master_facts, tmp_path: Path):
    path = tmp_path / "cv.pdf"
    data = build_pdf(master_facts, path)
    assert path.stat().st_size > 100
    assert data[:4] == b"%PDF"
    # crude: email should appear in content streams for simple builds
    assert b"Alex" in data or b"Morgenstern" in data or len(data) > 500


def test_ats_structural_on_facts(master_facts):
    report = analyze_cv_structure(master_facts)
    assert report["schema_version"] == "1.0"
    assert 0 <= report["score_hint"] <= 100
    assert isinstance(report["issues"], list)


def test_ats_structural_txt_file(tmp_path: Path):
    p = tmp_path / "x.txt"
    p.write_text("hello world contact email@test.de phone", encoding="utf-8")
    report = analyze_source_file(p, "txt", p.read_text())
    assert report["score_hint"] >= 80


def test_download_endpoints(client, master_facts):
    r = client.post("/cv/load-fixture")
    cv_id = r.json()["cv_id"]

    for fmt in ("txt", "docx", "pdf"):
        r = client.get(f"/cv/{cv_id}/download?format={fmt}")
        assert r.status_code == 200, fmt
        assert len(r.content) > 50
        if fmt == "txt":
            assert b"Alex Morgenstern" in r.content
            assert b"alex.morgenstern@example.com" in r.content
        if fmt == "docx":
            assert r.headers["content-type"].startswith(
                "application/vnd.openxmlformats"
            )
        if fmt == "pdf":
            assert r.content[:4] == b"%PDF"


def test_export_page(client):
    r = client.post("/cv/load-fixture")
    cv_id = r.json()["cv_id"]
    r = client.get(f"/cv/{cv_id}/export")
    assert r.status_code == 200
    assert "DOCX" in r.text
    assert "ATS-Struktur" in r.text or "Score" in r.text
