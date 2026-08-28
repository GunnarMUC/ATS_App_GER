from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _sqlite_on_connect(dbapi_conn, _connection_record) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def create_db_engine(url: str | None = None) -> Engine:
    settings = get_settings()
    db_url = url or settings.resolved_database_url()
    connect_args: dict = {}
    engine_kwargs: dict = {"future": True}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if db_url == "sqlite:///:memory:" or ":memory:" in db_url:
            engine_kwargs["poolclass"] = StaticPool
        else:
            path = db_url.replace("sqlite:///", "", 1)
            Path(path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(db_url, connect_args=connect_args, **engine_kwargs)
    if db_url.startswith("sqlite"):
        event.listen(engine, "connect", _sqlite_on_connect)
    return engine


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import orm  # noqa: F401

    Base.metadata.create_all(bind=engine)
