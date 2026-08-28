from __future__ import annotations

import io
import shutil
import zipfile
from pathlib import Path

ALLOWED_TOP = {"ats_app.db", "uploads", "generated"}


def _iter_backup_files(data_dir: Path) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    db = data_dir / "ats_app.db"
    if db.is_file():
        out.append(("ats_app.db", db))
    for folder in ("uploads", "generated"):
        root = data_dir / folder
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file():
                rel = path.relative_to(data_dir).as_posix()
                out.append((rel, path))
    return out


def make_backup_zip(data_dir: Path, password: str | None = None) -> bytes:
    buf = io.BytesIO()
    files = _iter_backup_files(data_dir)
    if password:
        import pyzipper

        with pyzipper.AESZipFile(buf, "w", compression=pyzipper.ZIP_DEFLATED) as zf:
            zf.setpassword(password.encode("utf-8"))
            zf.setencryption(pyzipper.WZ_AES, nbits=256)
            for name, path in files:
                zf.write(path, name)
            if not files:
                zf.writestr(".keep", "")
    else:
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for name, path in files:
                zf.write(path, name)
            if not files:
                zf.writestr(".keep", "")
    return buf.getvalue()


def _safe_members(names: list[str]) -> list[str]:
    safe: list[str] = []
    for name in names:
        n = name.replace("\\", "/").lstrip("/")
        if n in {".keep", ""}:
            continue
        if ".." in Path(n).parts:
            raise ValueError(f"unsicherer Pfad: {name}")
        top = n.split("/", 1)[0]
        if top not in ALLOWED_TOP:
            raise ValueError(f"unerwarteter Eintrag: {name}")
        safe.append(n)
    return safe


def restore_backup(data_dir: Path, blob: bytes, password: str | None = None) -> None:
    buf = io.BytesIO(blob)
    tmp = data_dir / "_restore_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        if password:
            import pyzipper

            with pyzipper.AESZipFile(buf, "r") as zf:
                zf.setpassword(password.encode("utf-8"))
                members = _safe_members(zf.namelist())
                zf.extractall(tmp, members=members)
        else:
            with zipfile.ZipFile(buf, "r") as zf:
                members = _safe_members(zf.namelist())
                zf.extractall(tmp, members=members)
        data_dir.mkdir(parents=True, exist_ok=True)
        src_db = tmp / "ats_app.db"
        if src_db.is_file():
            dest_db = data_dir / "ats_app.db"
            shutil.copy2(src_db, dest_db)
        for folder in ("uploads", "generated"):
            src = tmp / folder
            dest = data_dir / folder
            if dest.exists():
                shutil.rmtree(dest)
            if src.exists():
                shutil.copytree(src, dest)
            else:
                dest.mkdir(parents=True, exist_ok=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
