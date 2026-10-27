"""
API v1 Router Aggregator
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, products, alerts, jobs

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Scrape Jobs"])
