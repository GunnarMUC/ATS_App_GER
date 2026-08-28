from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# isolate test DB before app import side effects
os.environ.setdefault("DATA_DIR", str(Path(__file__).resolve().parent / "_testdata"))
os.environ.setdefault("OLLAMA_HOST", "http://127.0.0.1:11434")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("APP_HOST", "127.0.0.1")

from app.config import get_settings
from app.database import Base, get_db
from app.main import app

_SAFE = {"GET", "HEAD", "OPTIONS", "TRACE"}


def _csrf_client(inner: TestClient) -> TestClient:
    inner.get("/health")
    orig = inner.request

    def hooked(method, url, **kwargs):
        if str(method).upper() not in _SAFE:
            token = inner.cookies.get("csrf_token")
            if not token:
                inner.get("/health")
                token = inner.cookies.get("csrf_token")
            headers = dict(kwargs.get("headers") or {})
            lower = {k.lower() for k in headers}
            if token and "x-csrf-token" not in lower:
                headers["X-CSRF-Token"] = token
            kwargs["headers"] = headers
            data = kwargs.get("data")
            if isinstance(data, dict) and token and "csrf_token" not in data:
                data = dict(data)
                data["csrf_token"] = token
                kwargs["data"] = data
        return orig(method, url, **kwargs)

    inner.request = hooked  # type: ignore[method-assign]
    return inner


@pytest.fixture()
def client(tmp_path, monkeypatch):
    get_settings.cache_clear()
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    get_settings.cache_clear()
    settings = get_settings()
    settings.ensure_dirs()

    from sqlalchemy import create_engine, event

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _fk(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def _override():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield _csrf_client(c)
    app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.fixture()
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "spec" / "fixtures"
