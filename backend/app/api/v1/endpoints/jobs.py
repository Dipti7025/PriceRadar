"""
Scrape Jobs Endpoints
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db, check_db_health
from app.models.product import ScrapeJob, Product
from app.schemas.product import ScrapeJobResponse

router = APIRouter()


@router.get(
    "/",
    response_model=List[ScrapeJobResponse],
    summary="List recent scrape and extraction jobs",
)
async def list_scrape_jobs(
    limit: int = 25,
    db: AsyncSession = Depends(get_db),
):
    db_status = await check_db_health()
    if db_status.get("status") != "connected":
        return []

    stmt = select(ScrapeJob).order_by(desc(ScrapeJob.scheduled_at)).limit(limit)
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    return [ScrapeJobResponse.model_validate(j) for j in jobs]


@router.post(
    "/trigger/{product_id}",
    response_model=ScrapeJobResponse,
    summary="Trigger a manual scrape job for a product",
)
async def trigger_manual_scrape(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    db_status = await check_db_health()
    if db_status.get("status") != "connected":
        raise HTTPException(status_code=503, detail="Database offline")

    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    job = ScrapeJob(
        product_id=product.id,
        url=product.canonical_url,
        status="PENDING",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return ScrapeJobResponse.model_validate(job)
