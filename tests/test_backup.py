from __future__ import annotations

import sqlite3
from pathlib import Path

from app.services.backup import make_backup_zip, restore_backup


def test_backup_zip_roundtrip(tmp_path: Path):
    data = tmp_path / "data"
    (data / "uploads").mkdir(parents=True)
    (data / "generated" / "cv").mkdir(parents=True)
    db = data / "ats_app.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE t (id INTEGER)")
    conn.execute("INSERT INTO t VALUES (1)")
    conn.commit()
    conn.close()
    (data / "uploads" / "a.txt").write_text("hello", encoding="utf-8")
    (data / "generated" / "cv" / "x.txt").write_text("cv", encoding="utf-8")

    blob = make_backup_zip(data)
    assert blob[:2] == b"PK"

    empty = tmp_path / "empty"
    empty.mkdir()
    restore_backup(empty, blob)
    assert (empty / "ats_app.db").is_file()
    conn = sqlite3.connect(empty / "ats_app.db")
    assert conn.execute("SELECT id FROM t").fetchone() == (1,)
    conn.close()
    assert (empty / "uploads" / "a.txt").read_text(encoding="utf-8") == "hello"
    assert (empty / "generated" / "cv" / "x.txt").read_text(encoding="utf-8") == "cv"


def test_backup_zip_password_roundtrip(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "ats_app.db").write_bytes(b"sqlite-fake")
    blob = make_backup_zip(data, password="secret")
    dest = tmp_path / "out"
    dest.mkdir()
    restore_backup(dest, blob, password="secret")
    assert (dest / "ats_app.db").read_bytes() == b"sqlite-fake"


def test_backup_endpoint(client):
    r = client.get("/settings/backup")
    assert r.status_code == 200
    assert r.content[:2] == b"PK"
