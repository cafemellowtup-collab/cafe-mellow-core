"""
TIMEKEEPER - Cron Router for Serverless Automation
Secured endpoints for Google Cloud Scheduler (no APScheduler/Celery)
"""
import os
from datetime import date, timedelta, datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends

from backend.core.events import EventBus, Event

router = APIRouter(prefix="/api/v1/cron", tags=["cron"])

CRON_SECRET = os.getenv("CRON_SECRET", "")


def verify_cron_secret(x_cron_secret: Optional[str] = Header(None)):
    """
    Security middleware for cron endpoints
    Only Google Cloud Scheduler should know this secret
    """
    if not CRON_SECRET:
        raise HTTPException(status_code=500, detail="CRON_SECRET not configured")
    
    if x_cron_secret != CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid cron secret")
    
    return True


@router.post("/daily_close")
async def daily_close(
    target_date: Optional[str] = None,
    _: bool = Depends(verify_cron_secret)
):
    """
    Daily Closing Job
    Triggered by Cloud Scheduler at 2 AM daily
    
    Tasks:
    - Generate daily operations brief
    - Calculate daily metrics
    - Emit daily_close event for subscribers
    """
    try:
        closing_date = date.fromisoformat(target_date) if target_date else (date.today() - timedelta(days=1))
        
        event_bus = EventBus()
        event = Event(
            event_type="system.daily_close",
            timestamp=datetime.now(),
            org_id="*",  # Multi-tenant: will be processed per org
            location_id="*",
            payload={
                "closing_date": str(closing_date),
                "trigger": "cloud_scheduler"
            }
        )
        event_bus.emit(event)
        
        return {
            "ok": True,
            "job": "daily_close",
            "date": str(closing_date),
            "message": "Daily close initiated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run_payroll")
async def run_payroll(
    period_end: Optional[str] = None,
    _: bool = Depends(verify_cron_secret)
):
    """
    Payroll Processing Job
    Triggered monthly by Cloud Scheduler
    """
    try:
        period_end_date = date.fromisoformat(period_end) if period_end else date.today()
        
        event_bus = EventBus()
        event = Event(
            event_type="payroll.process",
            timestamp=datetime.now(),
            org_id="*",
            location_id="*",
            payload={
                "period_end": str(period_end_date),
                "trigger": "cloud_scheduler"
            }
        )
        event_bus.emit(event)
        
        return {
            "ok": True,
            "job": "run_payroll",
            "period_end": str(period_end_date),
            "message": "Payroll processing initiated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync_sales")
async def sync_sales(
    _: bool = Depends(verify_cron_secret)
):
    """
    Sales Sync Job
    Triggered every 4 hours by Cloud Scheduler
    
    IMPORTANT: This emits 'sales.synced' event instead of chaining functions
    """
    try:
        from pillars.config_vault import EffectiveSettings
        
        cfg = EffectiveSettings()
        
        event_bus = EventBus()
        event = Event(
            event_type="sales.sync_requested",
            timestamp=datetime.now(),
            org_id="*",
            location_id="*",
            payload={
                "trigger": "cloud_scheduler",
                "timestamp": str(date.today())
            }
        )
        event_bus.emit(event)
        
        return {
            "ok": True,
            "job": "sync_sales",
            "message": "Sales sync initiated via event bus"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate_data_quality")
async def calculate_data_quality(
    _: bool = Depends(verify_cron_secret)
):
    """
    Data Quality Calculation Job
    Triggered weekly by Cloud Scheduler
    
    Calculates data quality score and emits event if tier changes
    """
    try:
        event_bus = EventBus()
        event = Event(
            event_type="data_quality.calculate",
            timestamp=datetime.now(),
            org_id="*",
            location_id="*",
            payload={
                "trigger": "cloud_scheduler"
            }
        )
        event_bus.emit(event)
        
        return {
            "ok": True,
            "job": "calculate_data_quality",
            "message": "Data quality calculation initiated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def cron_health():
    """Health check (no auth required)"""
    return {
        "ok": True,
        "service": "cron",
        "cron_secret_set": bool(CRON_SECRET)
    }
