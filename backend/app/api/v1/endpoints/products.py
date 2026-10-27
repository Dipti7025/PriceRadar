"""
Products & Price Tracking Endpoints
Enforces SSRF protection before accepting user-submitted URLs.
Supports both trailing and non-trailing slash routes.
"""

import logging
import uuid
from urllib.parse import urlparse
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db, check_db_health
from app.core.security import validate_url_ssrf_safe, is_scraping_permitted_by_robots
from app.core.config import settings
from app.models.product import Product, TrackedProduct, PriceSnapshot, ScrapeJob
from app.schemas.product import (
    ProductSubmissionRequest,
    ProductSubmissionResponse,
    TrackedProductResponse,
    ProductResponse,
    PriceSnapshotResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/submit",
    response_model=ProductSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Product URL for Tracking with SSRF Protection",
)
@router.post(
    "/submit/",
    response_model=ProductSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def submit_product_url(
    payload: ProductSubmissionRequest,
    db: AsyncSession = Depends(get_db),
):
    # 1. Enforce strict SSRF Validation
    is_safe, reason, canonical_url = validate_url_ssrf_safe(
        payload.url,
        allowed_domains=settings.ALLOWED_SCRAPE_DOMAINS if settings.ALLOWED_SCRAPE_DOMAINS else None,
    )
    if not is_safe or not canonical_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL Rejected by Security Policy (SSRF Prevention): {reason}",
        )

    # 2. Check Database connectivity
    db_status = await check_db_health()
    if db_status.get("status") != "connected":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PostgreSQL database is currently disconnected: {db_status.get('message')}. Please verify Neon connection.",
        )

    parsed = urlparse(canonical_url)
    domain = parsed.netloc

    # 3. Check robots.txt permissions
    robots_ok, robots_reason = await is_scraping_permitted_by_robots(canonical_url, settings.USER_AGENT)
    if not robots_ok:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot track URL: {robots_reason}. PriceRadar strictly respects website robots.txt policies.",
        )

    try:
        # 4. Check if product already exists
        stmt = select(Product).where(Product.canonical_url == canonical_url)
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            product = Product(
                canonical_url=canonical_url,
                domain=domain,
                title=f"Tracking: {parsed.path.split('/')[-1] or domain}",
                currency="USD",
            )
            db.add(product)
            await db.flush()

        # 5. Create or update tracked product record
        tracked_stmt = select(TrackedProduct).where(
            TrackedProduct.product_id == product.id,
            TrackedProduct.user_email == payload.user_email,
        )
        tracked_res = await db.execute(tracked_stmt)
        tracked = tracked_res.scalar_one_or_none()

        if not tracked:
            tracked = TrackedProduct(
                product_id=product.id,
                user_email=payload.user_email,
                target_price=payload.target_price,
                notify_on_drop=payload.notify_on_drop,
                notify_on_target=payload.notify_on_target,
            )
            db.add(tracked)

        # 6. Enqueue Scrape Job
        job = ScrapeJob(
            product_id=product.id,
            url=canonical_url,
            status="PENDING",
        )
        db.add(job)
        await db.commit()

        return ProductSubmissionResponse(
            message="Product successfully submitted and queued for price extraction.",
            is_safe=True,
            canonical_url=canonical_url,
            job_id=job.id,
            product_id=product.id,
        )

    except Exception as exc:
        await db.rollback()
        err_msg = str(exc)
        logger.error("Error submitting product: %s", err_msg)
        if "does not exist" in err_msg.lower() or "relation" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database tables have not been created yet. Please run 'alembic upgrade head' in the backend directory.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record product tracking request: {err_msg}",
        )


@router.get(
    "/tracked",
    response_model=List[TrackedProductResponse],
    summary="List all tracked products with latest price snapshots",
)
@router.get(
    "/tracked/",
    response_model=List[TrackedProductResponse],
    include_in_schema=False,
)
async def list_tracked_products(
    db: AsyncSession = Depends(get_db),
):
    db_status = await check_db_health()
    if db_status.get("status") != "connected":
        return []

    try:
        stmt = select(TrackedProduct).order_by(desc(TrackedProduct.created_at))
        result = await db.execute(stmt)
        tracked_items = result.scalars().all()
    except Exception as exc:
        logger.warning("Could not list tracked products (tables might not be migrated yet): %s", exc)
        return []

    response_items = []
    for item in tracked_items:
        try:
            prod_stmt = select(Product).where(Product.id == item.product_id)
            prod_res = await db.execute(prod_stmt)
            product = prod_res.scalar_one_or_none()
            if not product:
                continue

            snap_stmt = (
                select(PriceSnapshot)
                .where(PriceSnapshot.product_id == product.id)
                .order_by(desc(PriceSnapshot.scraped_at))
                .limit(1)
            )
            snap_res = await db.execute(snap_stmt)
            latest_snap = snap_res.scalar_one_or_none()

            response_items.append(
                TrackedProductResponse(
                    id=item.id,
                    product_id=item.product_id,
                    product=ProductResponse.model_validate(product),
                    user_email=item.user_email,
                    target_price=item.target_price,
                    is_active=item.is_active,
                    notify_on_drop=item.notify_on_drop,
                    notify_on_target=item.notify_on_target,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    latest_snapshot=PriceSnapshotResponse.model_validate(latest_snap) if latest_snap else None,
                )
            )
        except Exception as item_err:
            logger.warning("Error processing tracked product item %s: %s", item.id, item_err)

    return response_items


@router.get(
    "/{product_id}/history",
    response_model=List[PriceSnapshotResponse],
    summary="Get historical price snapshots for a product",
)
@router.get(
    "/{product_id}/history/",
    response_model=List[PriceSnapshotResponse],
    include_in_schema=False,
)
async def get_price_history(
    product_id: uuid.UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    db_status = await check_db_health()
    if db_status.get("status") != "connected":
        raise HTTPException(status_code=503, detail="Database offline")

    try:
        stmt = (
            select(PriceSnapshot)
            .where(PriceSnapshot.product_id == product_id)
            .order_by(desc(PriceSnapshot.scraped_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        snapshots = result.scalars().all()
        return [PriceSnapshotResponse.model_validate(s) for s in snapshots]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch price history: {str(exc)}")
