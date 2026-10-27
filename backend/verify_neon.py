"""
PriceRadar - Neon PostgreSQL Connection Verifier
Tests both synchronous (psycopg2 / Alembic) and asynchronous (asyncpg / FastAPI) connections.
Safeguards credentials: never prints or exposes database passwords or full connection strings.
Loads root .env reliably whether run from project root or the backend folder.
"""

import sys
import os
import re
import asyncio
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


def find_root_env() -> Path | None:
    """Finds root .env by checking parents of __file__ and CWD."""
    current_file = Path(__file__).resolve()
    for parent in [current_file.parent, *current_file.parents]:
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate

    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate

    return None


# Discover and load root .env
env_file = find_root_env()
if env_file:
    load_dotenv(dotenv_path=env_file, override=True)

from app.core.config import settings, ROOT_ENV_PATH
from app.core.database import check_db_health, engine
from sqlalchemy import create_engine, text


def mask_secrets(text_val: str) -> str:
    """Masks passwords or secrets in error or output strings."""
    return re.sub(r":([^:@\s]+)@", ":***@", str(text_val))


async def test_async_connection() -> bool:
    print("\n--------------------------------------------------")
    print(" 1. Asynchronous Connection (FastAPI / SQLAlchemy 2.x)")
    print("--------------------------------------------------")
    
    parsed = urlparse(settings.async_database_url)
    print(f" Source Config  : DATABASE_URL")
    print(f" Target Host    : {parsed.hostname}")
    print(f" Port           : {parsed.port or 5432}")
    print(f" Database       : {parsed.path.lstrip('/')}")
    print(f" User           : {parsed.username}")
    print(f" Password       : [PROTECTED / REDACTED]")
    print(f" Driver         : asyncpg")

    health = await check_db_health()
    if health.get("status") == "connected":
        print("\n [SUCCESS] Asyncpg connected to Neon PostgreSQL!")
        print(f"           Provider : {health.get('provider')}")
        print(f"           Message  : {health.get('message')}")
        return True
    else:
        print("\n [FAILED]  Asyncpg connection failed:")
        print(f"           {health.get('message')}")
        return False


def test_sync_connection() -> bool:
    print("\n--------------------------------------------------")
    print(" 2. Synchronous Connection (Alembic Migrations / psycopg2)")
    print("--------------------------------------------------")
    
    parsed = urlparse(settings.sync_database_url)
    print(f" Source Config  : DATABASE_SYNC_URL")
    print(f" Target Host    : {parsed.hostname}")
    print(f" Port           : {parsed.port or 5432}")
    print(f" Database       : {parsed.path.lstrip('/')}")
    print(f" User           : {parsed.username}")
    print(f" Password       : [PROTECTED / REDACTED]")
    print(f" Driver         : psycopg2")

    try:
        sync_engine = create_engine(settings.sync_database_url, pool_pre_ping=True)
        with sync_engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            row = result.scalar()
            short_version = row.split(',')[0] if row else 'PostgreSQL'
            print("\n [SUCCESS] Psycopg2 connected to Neon PostgreSQL!")
            print(f"           Server Version : {short_version}")
            return True
    except Exception as exc:
        sanitized_error = mask_secrets(str(exc))
        print("\n [FAILED]  Synchronous connection failed:")
        print(f"           {sanitized_error}")
        return False


async def main():
    print("==================================================")
    print("   PriceRadar - Neon PostgreSQL Connection Test   ")
    print("==================================================")
    print(f"Loaded .env from : {ROOT_ENV_PATH or env_file or 'Not found'}")

    sync_ok = test_sync_connection()
    async_ok = await test_async_connection()

    await engine.dispose()

    print("\n==================================================")
    if sync_ok and async_ok:
        print(">> RESULT: ALL DATABASE CONNECTIONS SUCCESSFUL! <<")
        print("Both DATABASE_URL (async) and DATABASE_SYNC_URL (sync) are verified.")
    else:
        print(">> RESULT: ONE OR MORE CONNECTIONS FAILED <<")
        print("Please check your network and credentials in the root .env file.")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())
