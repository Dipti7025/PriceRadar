"""
Alerts Management Endpoints
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db, check_db_health
from app.models.product import Alert
from app.schemas.product import AlertResponse

router = APIRouter()


@router.get(
    "/",
    response_model=List[AlertResponse],
    summary="List all price alerts",
)
async def list_alerts(
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    db_status = await check_db_health()
    if db_status.get("status") != "connected":
        return []

    stmt = select(Alert).order_by(desc(Alert.triggered_at))
    if unread_only:
        stmt = stmt.where(Alert.is_read == False)
    
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    return [AlertResponse.model_validate(a) for a in alerts]


@router.patch(
    "/{alert_id}/read",
    response_model=AlertResponse,
    summary="Mark an alert as read",
)
async def mark_alert_read(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    db_status = await check_db_health()
    if db_status.get("status") != "connected":
        raise HTTPException(status_code=503, detail="Database offline")

    stmt = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)
