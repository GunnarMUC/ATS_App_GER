from __future__ import annotations

import pytest

from app.config import get_settings
from app.security.bind import assert_bind_is_loopback


def test_post_without_csrf_403():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        r = c.post("/settings/wipe", data={"confirm": "LOESCHEN"})
    assert r.status_code == 403


def test_post_with_csrf_token_ok(client):
    r = client.post(
        "/api/settings",
        json={
            "ollama_host": "http://127.0.0.1:11434",
            "model_fast": "x:1",
            "model_strong": "x:1",
        },
    )
    assert r.status_code == 200


def test_non_loopback_start_blocked(monkeypatch):
    monkeypatch.setenv("APP_HOST", "0.0.0.0")
    monkeypatch.setenv("APP_ALLOW_NONLOCAL", "false")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="nicht Loopback"):
        assert_bind_is_loopback()
    get_settings.cache_clear()


def test_non_loopback_allowed_with_flag(monkeypatch):
    monkeypatch.setenv("APP_HOST", "0.0.0.0")
    monkeypatch.setenv("APP_ALLOW_NONLOCAL", "true")
    get_settings.cache_clear()
    assert_bind_is_loopback()
    get_settings.cache_clear()
