"""
Pydantic Schemas for Products, Tracking, Price Snapshots, and Scrape Jobs
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class ProductSubmissionRequest(BaseModel):
    url: str = Field(..., description="Target product page URL to track", min_length=10, max_length=2048)
    target_price: Optional[Decimal] = Field(None, description="Optional target price to trigger alerts", ge=0)
    user_email: Optional[str] = Field(None, description="Optional notification email", max_length=255)
    notify_on_drop: bool = Field(True, description="Alert whenever any price drop occurs")
    notify_on_target: bool = Field(True, description="Alert when price drops below target_price")


class PriceSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    price: Decimal
    original_price: Optional[Decimal] = None
    currency: str
    in_stock: bool
    seller: Optional[str] = None
    scraped_at: datetime


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    canonical_url: str
    domain: str
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    sku: Optional[str] = None
    currency: str
    created_at: datetime
    updated_at: datetime


class TrackedProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    product: ProductResponse
    user_email: Optional[str] = None
    target_price: Optional[Decimal] = None
    is_active: bool
    notify_on_drop: bool
    notify_on_target: bool
    created_at: datetime
    updated_at: datetime
    latest_snapshot: Optional[PriceSnapshotResponse] = None
    price_change_amount: Optional[Decimal] = None
    price_change_percent: Optional[float] = None


class ScrapeJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    url: str
    status: str
    error_message: Optional[str] = None
    retry_count: int
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tracked_product_id: uuid.UUID
    alert_type: str
    threshold_price: Optional[Decimal] = None
    triggered_price: Decimal
    message: str
    is_read: bool
    triggered_at: datetime


class ProductSubmissionResponse(BaseModel):
    message: str
    is_safe: bool
    canonical_url: str
    job_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
