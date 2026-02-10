from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from shared.config import get_env


class Base(DeclarativeBase):
    pass


def create_session_factory(database_url: str):
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)
    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False)


DATABASE_URL = get_env("DATABASE_URL")
engine, SessionLocal = create_session_factory(DATABASE_URL)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
