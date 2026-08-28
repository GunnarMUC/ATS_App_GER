from __future__ import annotations

import json
from pathlib import Path


def test_application_created_and_stage_on_dashboard(client, fixtures_dir: Path):
    r = client.post("/cv/load-fixture")
    assert r.status_code == 200
    cv_id = r.json()["cv_id"]
    facts = json.loads((fixtures_dir / "master-cv.json").read_text(encoding="utf-8"))
    r = client.post(f"/cv/{cv_id}/lock", json={"facts": facts})
    assert r.status_code == 200

    text = (fixtures_dir / "job-coo.txt").read_text(encoding="utf-8")
    r = client.post("/jobs", data={"text": text}, headers={"Accept": "application/json"})
    assert r.status_code == 200
    job_id = r.json()["job_id"]

    r = client.get("/")
    assert r.status_code == 200
    assert "Bewerbungen" in r.text
    assert "Offen" in r.text or "offen" in r.text

    import re

    m = re.search(r"/applications/([0-9a-f\-]{36})/stage", r.text)
    assert m, r.text[:800]
    app_id = m.group(1)

    r = client.post(
        f"/applications/{app_id}/stage",
        data={"stage": "eingereicht"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert "Eingereicht" in r.text
    assert job_id in r.text or "COO" in r.text
