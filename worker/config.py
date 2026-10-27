"""
Worker Configuration Settings
Compatible with Neon PostgreSQL and standard PostgreSQL.
Automatically and reliably discovers the root .env file.
"""

from typing import Optional
import os
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_root_env() -> Optional[Path]:
    """Locates the project root .env file by scanning upwards from __file__ and CWD."""
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


ROOT_ENV_PATH = find_root_env()
if ROOT_ENV_PATH:
    load_dotenv(dotenv_path=ROOT_ENV_PATH, override=True)


def sanitize_asyncpg_url(url: str) -> str:
    if not url:
        return url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not url.startswith("postgresql+asyncpg://"):
        url = re.sub(r"^postgresql\+[a-zA-Z0-9_]+://", "postgresql+asyncpg://", url)

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "sslmode" in qs:
        val = qs.pop("sslmode")[0]
        qs["ssl"] = [val]
    qs.pop("channel_binding", None)
    new_query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


class WorkerSettings(BaseSettings):
    # PostgreSQL Configuration
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "priceradar"
    DATABASE_URL: str = ""
    DATABASE_SYNC_URL: str = ""

    # Worker Tuning
    WORKER_POLL_INTERVAL_SECONDS: int = 15
    MAX_CONCURRENT_JOBS: int = 3
    FETCH_TIMEOUT_SECONDS: int = 20
    MAX_RETRIES: int = 3
    USER_AGENT: str = "PriceRadar/1.0 (+https://github.com/priceradar; legitimate price comparison crawler)"
    HEADLESS_BROWSER: bool = True

    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV_PATH) if ROOT_ENV_PATH else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def async_database_url(self) -> str:
        # Use DATABASE_URL for async connection
        if self.DATABASE_URL:
            return sanitize_asyncpg_url(self.DATABASE_URL)
        if self.DATABASE_SYNC_URL:
            return sanitize_asyncpg_url(self.DATABASE_SYNC_URL)
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def is_pooler_connection(self) -> bool:
        target = (self.DATABASE_SYNC_URL or "") + (self.DATABASE_URL or "") + self.POSTGRES_HOST
        return "pooler" in target.lower() or "neon.tech" in target.lower()


worker_settings = WorkerSettings()
