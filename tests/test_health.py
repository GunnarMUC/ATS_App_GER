from __future__ import annotations

from unittest.mock import AsyncMock, patch

from app.config import get_settings


def test_health_without_ollama(client):
    with patch(
        "app.services.llm_client.list_models",
        new=AsyncMock(side_effect=Exception("down")),
    ):
        r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["app"] == "ok"
    assert data["ollama"] == "down"
    assert "selected" in data
    assert "fast" in data["selected"]
    assert "strong" in data["selected"]
    assert data["fast_present"] is False
    assert data["strong_present"] is False


def test_health_with_models(client):
    with patch(
        "app.services.llm_client.list_models",
        new=AsyncMock(return_value=["llama3.2:3b", "qwen2.5:7b"]),
    ):
        r = client.post(
            "/api/settings",
            json={
                "model_fast": "llama3.2:3b",
                "model_strong": "llama3.2:3b",
                "same_model": True,
            },
        )
        assert r.status_code == 200
        r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ollama"] == "connected"
    assert "llama3.2:3b" in data["models_installed"]
    assert data["selected"]["fast"] == "llama3.2:3b"
    assert data["fast_present"] is True
    assert data["strong_present"] is True


def test_config_default_bind_loopback():
    get_settings.cache_clear()
    s = get_settings()
    assert s.app_host == "127.0.0.1"


def test_settings_accepts_identical_tags(client):
    with patch(
        "app.services.llm_client.list_models",
        new=AsyncMock(return_value=["gemma2:9b"]),
    ):
        r = client.post(
            "/api/settings",
            json={
                "ollama_host": "http://127.0.0.1:11434",
                "model_fast": "gemma2:9b",
                "model_strong": "gemma2:9b",
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["settings"]["model_fast"] == "gemma2:9b"
    assert body["settings"]["model_strong"] == "gemma2:9b"


def test_dashboard_renders_when_ollama_down(client):
    with patch(
        "app.services.llm_client.list_models",
        new=AsyncMock(side_effect=Exception("down")),
    ):
        r = client.get("/")
    assert r.status_code == 200
    assert "Übersicht" in r.text
