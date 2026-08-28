from __future__ import annotations

import json
from pathlib import Path


def _seed_lock(client, fixtures_dir: Path) -> None:
    r = client.post("/cv/load-fixture")
    assert r.status_code == 200
    cv_id = r.json()["cv_id"]
    facts = json.loads((fixtures_dir / "master-cv.json").read_text(encoding="utf-8"))
    r = client.post(f"/cv/{cv_id}/lock", json={"facts": facts})
    assert r.status_code == 200


def test_job_flow_coo_to_zip(client, fixtures_dir: Path):
    _seed_lock(client, fixtures_dir)
    text = (fixtures_dir / "job-coo.txt").read_text(encoding="utf-8")
    r = client.post("/jobs", data={"text": text}, follow_redirects=False)
    assert r.status_code in (303, 200)
    # find job via creating and reading location or second post with accept json
    r = client.post(
        "/jobs",
        data={"text": text},
        headers={"Accept": "application/json"},
    )
    # may redirect; try again without follow
    if r.status_code == 200 and r.headers.get("content-type", "").startswith("application/json"):
        job_id = r.json()["job_id"]
    else:
        r = client.post("/jobs", data={"text": text}, follow_redirects=True)
        assert r.status_code == 200
        # extract from URL after redirect chain — use API-style by parsing last request
        # simpler: create via internal helper path
        # use jobs list: scrape job id from HTML
        import re
        m = re.search(r"/jobs/([0-9a-f\-]{36})", r.text)
        assert m, r.text[:500]
        job_id = m.group(1)

    r = client.post(f"/jobs/{job_id}/role", data={"role_family": "coo"}, follow_redirects=True)
    assert r.status_code == 200
    assert "Anpassungsplan" in r.text

    # get plan id from page
    import re
    m = re.search(r"/jobs/" + job_id + r"/plan/([0-9a-f\-]{36})/confirm", r.text)
    assert m
    plan_id = m.group(1)
    r = client.post(f"/jobs/{job_id}/plan/{plan_id}/confirm", data={}, follow_redirects=True)
    assert r.status_code == 200

    r = client.post(
        f"/jobs/{job_id}/generate?type=both",
        headers={"Accept": "application/json"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("document_ids")

    r = client.get(f"/jobs/{job_id}/review")
    assert r.status_code == 200

    r = client.get(f"/jobs/{job_id}/zip")
    assert r.status_code == 200
    assert r.content[:2] == b"PK"


def test_generate_without_confirm_409(client, fixtures_dir: Path):
    _seed_lock(client, fixtures_dir)
    text = (fixtures_dir / "job-ceo.txt").read_text(encoding="utf-8")
    r = client.post("/jobs", data={"text": text}, headers={"Accept": "application/json"})
    if r.status_code != 200:
        r = client.post("/jobs", data={"text": text}, follow_redirects=True)
        import re
        m = re.search(r"/jobs/([0-9a-f\-]{36})", r.url.path + r.text)
        assert m
        job_id = m.group(1)
    else:
        job_id = r.json()["job_id"]
    r = client.post(f"/jobs/{job_id}/generate?type=cv")
    assert r.status_code == 409
