"""
Health Check Endpoints
Provides system diagnostic information, uptime, and live PostgreSQL connectivity testing.
"""

import sys
import platform
from datetime import datetime, timezone
from fastapi import APIRouter, Response, status
from app.core.config import settings
from app.core.database import check_db_health
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System and Database Health Check",
    description="Returns current status of the backend API and PostgreSQL connectivity.",
)
async def get_health(response: Response):
    db_health = await check_db_health()
    
    is_db_connected = db_health.get("status") == "connected"
    overall_status = "ok" if is_db_connected else "degraded"
    
    # If database is offline, respond with 200 OK + degraded status so monitoring UI can render diagnostics
    return HealthResponse(
        status=overall_status,
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc),
        components={
            "database": db_health,
            "system": {
                "os": platform.system(),
                "os_release": platform.release(),
                "python_version": sys.version.split()[0],
                "environment": settings.ENVIRONMENT,
            },
        },
    )
