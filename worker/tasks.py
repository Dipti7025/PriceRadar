"""
ETL Job Processing Pipeline
Manages pending scrape jobs, extracts product pricing, saves snapshots,
and evaluates alert conditions in PostgreSQL.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from worker.config import worker_settings
from worker.extractor import fetch_and_extract_product
from app.models.product import Product, TrackedProduct, PriceSnapshot, ScrapeJob, Alert

logger = logging.getLogger(__name__)

connect_args = {}
if worker_settings.is_pooler_connection:
    connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    worker_settings.async_database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=connect_args,
)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def evaluate_alerts(
    session: AsyncSession,
    product: Product,
    new_price: Decimal,
    previous_price: Optional[Decimal],
    in_stock: bool,
):
    """Evaluates target-price and price-drop alerts for all subscribers."""
    stmt = select(TrackedProduct).where(
        TrackedProduct.product_id == product.id,
        TrackedProduct.is_active == True,
    )
    result = await session.execute(stmt)
    tracked_items = result.scalars().all()

    for item in tracked_items:
        # 1. Target Price Alert
        if item.notify_on_target and item.target_price is not None:
            if new_price <= item.target_price:
                alert = Alert(
                    tracked_product_id=item.id,
                    alert_type="TARGET_REACHED",
                    threshold_price=item.target_price,
                    triggered_price=new_price,
                    message=f"Target price reached! {product.title} is now ${new_price:.2f} (Target was ${item.target_price:.2f}).",
                )
                session.add(alert)
                logger.info("Target price alert triggered for product %s (Price: %s)", product.id, new_price)

        # 2. General Price Drop Alert
        if item.notify_on_drop and previous_price is not None:
            if new_price < previous_price:
                diff = previous_price - new_price
                percent = (diff / previous_price) * 100
                alert = Alert(
                    tracked_product_id=item.id,
                    alert_type="PRICE_DROP",
                    threshold_price=previous_price,
                    triggered_price=new_price,
                    message=f"Price dropped by {percent:.1f}% (-${diff:.2f})! Now ${new_price:.2f} (was ${previous_price:.2f}).",
                )
                session.add(alert)
                logger.info("Price drop alert triggered for product %s (-$%s)", product.id, diff)


async def process_single_job(session: AsyncSession, job: ScrapeJob):
    """Executes extraction and ETL for a single ScrapeJob."""
    job.status = "RUNNING"
    job.started_at = datetime.now(timezone.utc)
    await session.commit()

    try:
        data = await fetch_and_extract_product(job.url)
        extracted_price = data.get("price")

        if extracted_price is None:
            raise ValueError("Price could not be extracted from product page")

        # Fetch product
        prod_stmt = select(Product).where(Product.id == job.product_id)
        prod_res = await session.execute(prod_stmt)
        product = prod_res.scalar_one_or_none()
        if not product:
            raise ValueError(f"Product {job.product_id} not found in database")

        # Update product metadata if new info found
        if data.get("title") and product.title.startswith("Tracking:"):
            product.title = data["title"]
        if data.get("image_url") and not product.image_url:
            product.image_url = data["image_url"]
        if data.get("description") and not product.description:
            product.description = data["description"]

        # Get previous price snapshot
        prev_stmt = (
            select(PriceSnapshot)
            .where(PriceSnapshot.product_id == product.id)
            .order_by(desc(PriceSnapshot.scraped_at))
            .limit(1)
        )
        prev_res = await session.execute(prev_stmt)
        previous_snap = prev_res.scalar_one_or_none()
        previous_price = previous_snap.price if previous_snap else None

        # Create new price snapshot
        snapshot = PriceSnapshot(
            product_id=product.id,
            price=extracted_price,
            currency=data.get("currency", "USD"),
            in_stock=data.get("in_stock", True),
        )
        session.add(snapshot)

        # Trigger alerts
        await evaluate_alerts(
            session=session,
            product=product,
            new_price=extracted_price,
            previous_price=previous_price,
            in_stock=data.get("in_stock", True),
        )

        job.status = "COMPLETED"
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = None
        await session.commit()
        logger.info("Scrape job %s completed successfully for %s", job.id, job.url)

    except Exception as exc:
        logger.error("Job %s failed: %s", job.id, exc)
        job.retry_count += 1
        job.error_message = str(exc)
        if job.retry_count >= worker_settings.MAX_RETRIES:
            job.status = "FAILED"
        else:
            job.status = "PENDING"  # Eligible for retry
        await session.commit()


async def run_worker_cycle():
    """Polls database for pending extraction jobs and processes them."""
    async with SessionLocal() as session:
        stmt = (
            select(ScrapeJob)
            .where(ScrapeJob.status == "PENDING")
            .order_by(ScrapeJob.scheduled_at)
            .limit(worker_settings.MAX_CONCURRENT_JOBS)
        )
        result = await session.execute(stmt)
        pending_jobs = result.scalars().all()

        if not pending_jobs:
            return 0

        logger.info("Found %d pending scrape jobs to process.", len(pending_jobs))
        for job in pending_jobs:
            await process_single_job(session, job)

        return len(pending_jobs)
