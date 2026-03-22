from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "oscar_task2.sqlite3"


def get_engine(db_path: Path | None = None, echo: bool = False):
    database_path = db_path or DEFAULT_DB_PATH
    return create_engine(f"sqlite:///{database_path}", echo=echo, future=True)


SessionLocal = sessionmaker(autoflush=False, expire_on_commit=False, future=True)


def configure_session(db_path: Path | None = None, echo: bool = False) -> None:
    SessionLocal.configure(bind=get_engine(db_path=db_path, echo=echo))
