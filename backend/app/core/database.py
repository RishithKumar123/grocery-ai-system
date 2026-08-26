from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

from sqlalchemy.exc import OperationalError
from app.core.logging import logger

# Create engine with PostgreSQL and fallback to SQLite if offline
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    # Test connection quickly
    with engine.connect() as conn:
        logger.info("Successfully connected to PostgreSQL database.")
except (OperationalError, Exception) as e:
    logger.warning(f"PostgreSQL connection failed ({str(e)}).")
    logger.warning("Falling back to local SQLite database (sqlite:///./grocery_sqlite.db) for validation.")
    engine = create_engine(
        "sqlite:///./grocery_sqlite.db",
        connect_args={"check_same_thread": False}
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Declarative Base for models
class Base(DeclarativeBase):
    pass


# Dependency to get db session
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
