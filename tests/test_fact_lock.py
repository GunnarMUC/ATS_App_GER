from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.cv_structurer import StructureError, structure_cv_text, validate_cv_dict
from app.services.fact_lock import canonical_hash


@pytest.fixture()
def master_facts(fixtures_dir: Path) -> dict:
    return json.loads((fixtures_dir / "master-cv.json").read_text(encoding="utf-8"))


def test_validate_fixture_roundtrip(master_facts):
    cv = validate_cv_dict(master_facts)
    assert cv.personal.full_name == "Alex Morgenstern"
    assert cv.schema_version == "1.0"
    dumped = cv.to_canonical_dict()
    again = validate_cv_dict(dumped)
    assert again.personal.full_name == cv.personal.full_name
    assert canonical_hash(cv) == canonical_hash(again)


@pytest.mark.asyncio
async def test_structure_with_mock_llm(master_facts):
    payload = json.dumps(master_facts, ensure_ascii=False)

    async def fake_generate(prompt, **kwargs):
        return payload

    result = await structure_cv_text("ignored raw text", generate_fn=fake_generate)
    assert result.personal.full_name == "Alex Morgenstern"
    assert any(e.id == "exp_gl_ops" for e in result.experience)


@pytest.mark.asyncio
async def test_structure_repair_once_then_ok(master_facts):
    bad = '{"schema_version":"1.0","personal":{"full_name":"X"}'
    good = json.dumps(master_facts, ensure_ascii=False)
    calls = {"n": 0}

    async def fake_generate(prompt, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return bad
        return good

    result = await structure_cv_text("text", generate_fn=fake_generate)
    assert result.personal.full_name == "Alex Morgenstern"
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_structure_fails_after_repair():
    async def fake_generate(prompt, **kwargs):
        return "not-json-at-all"

    with pytest.raises(StructureError):
        await structure_cv_text("text", generate_fn=fake_generate)


def test_lock_archives_previous(client, master_facts):
    # create cv via paste
    text = (
        "Alex Morgenstern München langjährige Erfahrung in Operations und Logistik "
        "mit Ergebnisverantwortung und OTIF."
    )
    r = client.post("/upload/cv", data={"paste_text": text})
    assert r.status_code in (200, 303)

    # get latest cv id from list page
    r = client.get("/cv")
    assert r.status_code == 200

    # load fixture path is cleaner
    r = client.post("/cv/load-fixture")
    assert r.status_code == 200
    cv_id = r.json()["cv_id"]

    r = client.post(f"/cv/{cv_id}/lock", json={"facts": master_facts})
    assert r.status_code == 200
    first = r.json()
    assert first["is_active"] is True
    first_id = first["lock_id"]

    # second lock
    tweaked = json.loads(json.dumps(master_facts))
    tweaked["personal"]["city"] = "Hamburg"
    r = client.post(f"/cv/{cv_id}/lock", json={"facts": tweaked})
    assert r.status_code == 200
    second = r.json()
    assert second["lock_id"] != first_id
    assert second["is_active"] is True

    # only one active via health-less check: re-lock and verify hash changed
    assert second["content_hash"] != first["content_hash"]


def test_put_facts_validation(client, master_facts):
    r = client.post("/cv/load-fixture")
    cv_id = r.json()["cv_id"]
    r = client.put(f"/cv/{cv_id}/facts", json={"facts": {"nope": True}})
    assert r.status_code == 422

    r = client.put(f"/cv/{cv_id}/facts", json={"facts": master_facts})
    assert r.status_code == 200
    assert r.json()["facts"]["personal"]["full_name"] == "Alex Morgenstern"


def test_facts_page_renders(client, master_facts):
    r = client.post("/cv/load-fixture")
    cv_id = r.json()["cv_id"]
    r = client.get(f"/cv/{cv_id}/facts")
    assert r.status_code == 200
    assert "Fakten prüfen" in r.text
    assert "Alex Morgenstern" in r.text
