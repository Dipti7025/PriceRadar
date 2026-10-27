"""
Unit Tests for Health Endpoints
Verifies that health checks return structured status without crashing when DB is offline.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint_response_structure():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] in ("ok", "degraded")
        assert data["service"] == "PriceRadar API"
        assert "components" in data
        assert "database" in data["components"]
        assert "system" in data["components"]
        assert data["components"]["database"]["dialect"] == "postgresql"


@pytest.mark.asyncio
async def test_api_v1_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "database" in data["components"]


@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "PostgreSQL" in data["database_backend"]
