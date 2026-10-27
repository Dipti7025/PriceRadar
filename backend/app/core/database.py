"""
Database Configuration & Engine Module
Strictly uses SQLAlchemy 2.0 with asyncpg for PostgreSQL.
Compatible with Neon PostgreSQL (including serverless pooler) and local PostgreSQL.
SQLite is never used.
Credentials and passwords are never exposed in logs or health responses.
"""

import logging
import re
from typing import AsyncGenerator, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

logger = logging.getLogger(__name__)


def mask_credentials(msg: str) -> str:
    """Masks passwords or secrets in error messages."""
    return re.sub(r":([^:@\s]+)@", ":***@", str(msg))


# Strict verification: Ensure database URL is PostgreSQL
if "sqlite" in settings.async_database_url.lower():
    raise RuntimeError("CRITICAL: SQLite is strictly prohibited in PriceRadar. Please configure PostgreSQL.")

# Connection arguments for Neon / PgBouncer pooler compatibility
connect_args: Dict[str, Any] = {}
if settings.is_pooler_connection:
    # Disable asyncpg's statement cache to avoid 'prepared statement does not exist' in transaction poolers
    connect_args["statement_cache_size"] = 0

# Create asynchronous engine
engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=connect_args,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy 2.x models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for yielding database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> Dict[str, Any]:
    """
    Tests database connectivity asynchronously.
    Returns status dictionary without throwing uncaught exceptions or leaking credentials.
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1 AS alive"))
            row = result.scalar()
            if row == 1:
                return {
                    "status": "connected",
                    "dialect": "postgresql",
                    "provider": "Neon PostgreSQL" if "neon.tech" in settings.async_database_url else "PostgreSQL",
                    "message": "PostgreSQL connection active and responsive",
                }
            return {
                "status": "degraded",
                "dialect": "postgresql",
                "message": f"Unexpected health check response: {row}",
            }
    except Exception as exc:
        sanitized_error = mask_credentials(str(exc))
        logger.warning("PostgreSQL health check failed: %s", sanitized_error)
        return {
            "status": "disconnected",
            "dialect": "postgresql",
            "message": f"Could not establish connection to PostgreSQL server: {sanitized_error}",
        }
