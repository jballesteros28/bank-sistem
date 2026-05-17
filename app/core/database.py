from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


engine = create_engine(settings.DATABASE_URL, future=True, **_engine_kwargs(settings.DATABASE_URL))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def assert_test_database_url(database_url: str) -> None:
    url = make_url(database_url)
    database_name = url.database or database_url
    if database_url.startswith("sqlite") and database_name == ":memory:" and settings.ENVIRONMENT in {"test", "testing"}:
        return
    if "test" not in database_name.lower():
        raise RuntimeError(
            "Test database refused: the database name/path must contain 'test'."
        )
