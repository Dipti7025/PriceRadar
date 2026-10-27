"""
Database Migration State Inspector
Safely checks Neon PostgreSQL database state without modifying data or running migrations.
Never prints passwords or sensitive credentials.
"""

import sys
import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings, ROOT_ENV_PATH
from sqlalchemy import create_engine, text


def inspect_migration_state():
    print("==================================================")
    print("   PriceRadar - Alembic & Database State Check   ")
    print("==================================================")
    
    parsed = urlparse(settings.sync_database_url)
    print(f"Loaded .env from  : {ROOT_ENV_PATH}")
    print(f"Target Neon Host  : {parsed.hostname}")
    print(f"Database          : {parsed.path.lstrip('/')}")
    print(f"User              : {parsed.username}")
    print(f"Password          : [PROTECTED / REDACTED]")
    print(f"Connection Source : DATABASE_SYNC_URL")
    print("--------------------------------------------------")

    try:
        engine = create_engine(settings.sync_database_url)
        with engine.connect() as conn:
            # 1. Fetch all tables currently in the public schema
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
                "ORDER BY table_name;"
            ))
            existing_tables = [row[0] for row in result.fetchall()]

            # 2. Check alembic_version
            has_alembic = "alembic_version" in existing_tables
            current_revision = None
            if has_alembic:
                ver_res = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1;"))
                row = ver_res.fetchone()
                if row:
                    current_revision = row[0]

            print(f"Total Existing Tables : {len(existing_tables)}")
            if existing_tables:
                print(f"Existing Table Names  : {', '.join(existing_tables)}")
            else:
                print("Existing Table Names  : (none - database is clean)")

            print("--------------------------------------------------")
            if not has_alembic and not existing_tables:
                print(">> MIGRATION STATUS: NO MIGRATIONS APPLIED YET <<")
                print("The database is completely fresh and clean.")
                print("It is 100% safe to run: alembic upgrade head")
            elif has_alembic:
                print(f">> MIGRATION STATUS: CURRENT REVISION = {current_revision} <<")
                if current_revision == "0001_initial_schema":
                    print("Initial schema (0001_initial_schema) has ALREADY been applied.")
                else:
                    print(f"Database is at revision: {current_revision}")
            else:
                print(">> NOTICE: Some tables exist, but alembic_version was not found. <<")

        engine.dispose()
    except Exception as exc:
        print(f"\n[ERROR] Could not inspect database state: {str(exc)}")
        sys.exit(1)

    print("==================================================")


if __name__ == "__main__":
    inspect_migration_state()
