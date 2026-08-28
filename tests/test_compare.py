from __future__ import annotations

import json
from pathlib import Path


def test_compare_page_shows_master_and_plan(client, fixtures_dir: Path):
    r = client.post("/cv/load-fixture")
    cv_id = r.json()["cv_id"]
    facts = json.loads((fixtures_dir / "master-cv.json").read_text(encoding="utf-8"))
    client.post(f"/cv/{cv_id}/lock", json={"facts": facts})
    text = (fixtures_dir / "job-coo.txt").read_text(encoding="utf-8")
    r = client.post("/jobs", data={"text": text}, headers={"Accept": "application/json"})
    job_id = r.json()["job_id"]
    r = client.post(f"/jobs/{job_id}/role", data={"role_family": "coo"}, follow_redirects=True)
    assert r.status_code == 200
    import re

    m = re.search(r"/jobs/" + job_id + r"/plan/([0-9a-f\-]{36})/confirm", r.text)
    assert m
    client.post(f"/jobs/{job_id}/plan/{m.group(1)}/confirm", data={})

    r = client.get(f"/cv/compare/{job_id}")
    assert r.status_code == 200
    assert "Vorher / Nachher" in r.text
    assert "Master (gesperrt)" in r.text
    assert "Rollensicht" in r.text
    assert "FactGuard" in r.text
    assert "Nordkamm Logistik" in r.text
