"""
PriceRadar Backend Application Entrypoint
FastAPI application with PostgreSQL (SQLAlchemy 2.x), Pydantic v2, and SSRF security.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import check_db_health, engine
from app.api.v1.router import api_router
from app.api.v1.endpoints.health import get_health

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("priceradar")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Manager
    Runs initialization checks on startup and cleans up on shutdown.
    """
    logger.info("Starting PriceRadar API [%s]...", settings.APP_VERSION)
    logger.info("Target PostgreSQL: %s:%s/%s", settings.POSTGRES_HOST, settings.POSTGRES_PORT, settings.POSTGRES_DB)
    
    # Check PostgreSQL connection status
    db_status = await check_db_health()
    if db_status.get("status") == "connected":
        logger.info("PostgreSQL connection confirmed active.")
    else:
        logger.warning(
            "PostgreSQL is NOT currently connected: %s. "
            "Please ensure PostgreSQL / Neon is reachable on port %s.",
            db_status.get("message"),
            settings.POSTGRES_PORT,
        )

    yield

    logger.info("Shutting down PriceRadar API...")
    await engine.dispose()
    logger.info("Database engine connections closed.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-time Price Tracking and Product Monitoring API with SSRF Protection and strict PostgreSQL support.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS with permissive localhost regex to prevent browser origin blocks
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint aliases (accessible at /health, /api/health, and /api/v1/health)
app.add_api_route("/health", get_health, methods=["GET"], tags=["Health"])
app.add_api_route("/health/", get_health, methods=["GET"], include_in_schema=False)
app.add_api_route("/api/health", get_health, methods=["GET"], include_in_schema=False)
app.add_api_route("/api/health/", get_health, methods=["GET"], include_in_schema=False)

# Include versioned API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs",
        "health": "/health",
        "database_backend": "PostgreSQL (Strict)",
    }
