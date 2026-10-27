"""
Pydantic Schemas for System Health Monitoring
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DatabaseHealthInfo(BaseModel):
    status: str = Field(..., description="connected, degraded, or disconnected")
    dialect: str = Field(default="postgresql")
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    message: str


class SystemHealthInfo(BaseModel):
    os: str
    python_version: str
    environment: str


class HealthResponse(BaseModel):
    status: str = Field(..., description="'ok' when fully operational, 'degraded' when database is unreachable")
    service: str
    version: str
    timestamp: datetime
    components: Dict[str, Any]
