"""
Application Configuration Module
Validates environment settings with Pydantic v2 Settings.
Enforces strict PostgreSQL usage (SQLite is explicitly disallowed).
Optimized for Neon PostgreSQL, connection poolers, and standard PostgreSQL instances.
Automatically and reliably discovers the root .env file from any execution directory.
"""

from typing import List, Optional
import os
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_root_env() -> Optional[Path]:
    """
    Locates the project root .env file by scanning upwards from:
    1. The directory of this config file (__file__).
    2. The current working directory (Path.cwd()).
    Returns the absolute Path to .env if found, else None.
    """
    # 1. Search upwards starting from __file__
    current_file = Path(__file__).resolve()
    for parent in [current_file.parent, *current_file.parents]:
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate

    # 2. Search upwards starting from current working directory
    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate

    return None


# Discover and load root .env into os.environ before Settings instantiation
ROOT_ENV_PATH = find_root_env()
if ROOT_ENV_PATH:
    load_dotenv(dotenv_path=ROOT_ENV_PATH, override=True)


def sanitize_asyncpg_url(url: str) -> str:
    """
    Transforms any PostgreSQL URL into a valid asyncpg format:
    1. Driver: postgresql+asyncpg://
    2. Translates sslmode -> ssl (e.g. sslmode=require -> ssl=require)
    3. Strips libpq-only parameters not accepted by asyncpg (such as channel_binding)
    """
    if not url:
        return url

    # Ensure asyncpg driver prefix
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not url.startswith("postgresql+asyncpg://"):
        url = re.sub(r"^postgresql\+[a-zA-Z0-9_]+://", "postgresql+asyncpg://", url)

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    # Convert sslmode to ssl for asyncpg
    if "sslmode" in qs:
        val = qs.pop("sslmode")[0]
        qs["ssl"] = [val]

    # Remove channel_binding (libpq specific, unsupported by asyncpg)
    qs.pop("channel_binding", None)

    new_query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def sanitize_psycopg2_url(url: str) -> str:
    """
    Transforms any PostgreSQL URL into a valid psycopg2 format for Alembic:
    Driver: postgresql+psycopg2://
    """
    if not url:
        return url

    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    elif not url.startswith("postgresql+psycopg2://"):
        url = re.sub(r"^postgresql\+[a-zA-Z0-9_]+://", "postgresql+psycopg2://", url)

    return url


class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "PriceRadar API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # PostgreSQL Configuration (Strictly PostgreSQL - never SQLite)
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="priceradar")

    # Explicit URLs
    DATABASE_URL: Optional[str] = None
    DATABASE_SYNC_URL: Optional[str] = None

    # SSRF & Scraping Security Policies
    ALLOWED_SCRAPE_DOMAINS: List[str] = []
    MAX_FETCH_REDIRECTS: int = 3
    FETCH_TIMEOUT_SECONDS: int = 10
    USER_AGENT: str = "PriceRadar/1.0 (+https://github.com/priceradar; legitimate price comparison crawler)"

    # Worker configuration
    WORKER_POLL_INTERVAL_SECONDS: int = 60
    HEADLESS_BROWSER: bool = True

    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV_PATH) if ROOT_ENV_PATH else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DATABASE_URL", mode="before")
    def validate_database_url(cls, v):
        if v and "sqlite" in v.lower():
            raise ValueError("SQLite is strictly prohibited in PriceRadar. You must use PostgreSQL.")
        return v

    @field_validator("DATABASE_SYNC_URL", mode="before")
    def validate_database_sync_url(cls, v):
        if v and "sqlite" in v.lower():
            raise ValueError("SQLite is strictly prohibited in PriceRadar. You must use PostgreSQL.")
        return v

    @property
    def async_database_url(self) -> str:
        """
        Asynchronous SQLAlchemy connection URL (uses DATABASE_URL).
        """
        if self.DATABASE_URL:
            return sanitize_asyncpg_url(self.DATABASE_URL)
        if self.DATABASE_SYNC_URL:
            return sanitize_asyncpg_url(self.DATABASE_SYNC_URL)
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def sync_database_url(self) -> str:
        """
        Synchronous Alembic connection URL (uses DATABASE_SYNC_URL).
        """
        if self.DATABASE_SYNC_URL:
            return sanitize_psycopg2_url(self.DATABASE_SYNC_URL)
        if self.DATABASE_URL:
            return sanitize_psycopg2_url(self.DATABASE_URL)
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def is_pooler_connection(self) -> bool:
        """Detects if Neon or PgBouncer transaction pooler is used."""
        target = (self.DATABASE_SYNC_URL or "") + (self.DATABASE_URL or "") + self.POSTGRES_HOST
        return "pooler" in target.lower() or "neon.tech" in target.lower()


settings = Settings()
