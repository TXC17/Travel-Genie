"""
Database engine and session dependency manager.
Supports PostgreSQL and SQLite out of the box.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Configure connection arguments based on DB driver
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session per request.
    Closes the session after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
