"""
Universal Adapter API Router
============================
Exposes all Universal Adapter functionality through REST API.

Endpoints:
- Airlock: /api/v1/adapter/ingest/* - Data ingestion
- Refinery: /api/v1/adapter/transform - Manual transformation
- Guard: /api/v1/adapter/quarantine/* - Quarantine management
- Processor: /api/v1/adapter/process/* - Processing control
- Stats: /api/v1/adapter/stats - System statistics
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, UploadFile, File, Form, Query
from pydantic import BaseModel

# Import Universal Adapter components
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.universal_adapter.airlock import (
    router as airlock_router,
    init_airlock_tables
)
from backend.universal_adapter.refinery import (
    transform_data, transform_petpooja_order, TransformResult
)
from backend.universal_adapter.guard import (
    quarantine_record, get_quarantined_records,
    approve_quarantined_record, reject_quarantined_record,
    get_quarantine_stats, write_to_main_db
)
from backend.universal_adapter.processor import (
    process_single_record, process_pending_batch, process_failed_batch,
    start_background_processing, stop_background_processing, get_processor_stats,
    process_pending_async, process_single_async
)
from backend.universal_adapter.golden_schema import (
    get_schema_json, GOLDEN_SCHEMAS
)

router = APIRouter(prefix="/api/v1/adapter", tags=["universal-adapter"])


# =============================================================================
# Request/Response Models
# =============================================================================

class TransformRequest(BaseModel):
    data: Dict[str, Any]
    target_schema: str  # "order", "expense", "purchase"
    source_identifier: Optional[str] = "manual"


class TransformResponse(BaseModel):
    ok: bool
    result: str  # "success", "validation_failed", "ai_error"
    transformed_data: Optional[Dict[str, Any]] = None
    errors: List[str] = []


class QuarantineApproveRequest(BaseModel):
    quarantine_id: str
    corrected_data: Dict[str, Any]
    reviewed_by: str = "human"
    correction_notes: Optional[str] = None


class QuarantineRejectRequest(BaseModel):
    quarantine_id: str
    reviewed_by: str = "human"
    reason: str = ""


class ProcessRequest(BaseModel):
    log_id: Optional[str] = None
    batch_size: Optional[int] = 10


# =============================================================================
# Initialization
# =============================================================================

@router.on_event("startup")
async def startup_event():
    """Initialize Universal Adapter on startup"""
    init_airlock_tables()


@router.get("/health")
async def health_check():
    """Health check for Universal Adapter"""
    return {
        "ok": True,
        "service": "universal-adapter",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


# =============================================================================
# Schema Endpoints
# =============================================================================

@router.get("/schemas")
async def list_schemas():
    """List available Golden Schemas"""
    return {
        "ok": True,
        "schemas": list(GOLDEN_SCHEMAS.keys()),
        "descriptions": {
            "order": "Sales orders with items, payments, discounts",
            "expense": "Business expenses with categorization",
            "purchase": "Inventory purchases from vendors"
        }
    }


@router.get("/schemas/{schema_name}")
async def get_schema(schema_name: str):
    """Get JSON schema for a specific Golden Schema"""
    if schema_name not in GOLDEN_SCHEMAS:
        raise HTTPException(status_code=404, detail=f"Schema '{schema_name}' not found")
    
    return {
        "ok": True,
        "schema_name": schema_name,
        "json_schema": json.loads(get_schema_json(schema_name))
    }


# =============================================================================
# Transform Endpoints (Manual Testing)
# =============================================================================

@router.post("/transform", response_model=TransformResponse)
async def transform_manual(req: TransformRequest):
    """
    Manually transform data to Golden Schema.
    Useful for testing and validation.
    """
    result_status, validated, errors = transform_data(
        req.data, req.target_schema, req.source_identifier or "manual"
    )
    
    return TransformResponse(
        ok=result_status == TransformResult.SUCCESS,
        result=result_status.value,
        transformed_data=validated.model_dump() if validated and hasattr(validated, 'model_dump') else None,
        errors=errors
    )


@router.post("/transform/petpooja")
async def transform_petpooja(data: Dict[str, Any]):
    """
    Transform Petpooja API data to Golden Order.
    Uses optimized Petpooja-specific transformer.
    """
    result_status, validated, errors = transform_petpooja_order(data)
    
    return {
        "ok": result_status == TransformResult.SUCCESS,
        "result": result_status.value,
        "transformed_data": validated.model_dump() if validated else None,
        "errors": errors
    }


# =============================================================================
# Quarantine Endpoints
# =============================================================================

@router.get("/quarantine")
async def list_quarantine(
    status: str = Query(default="pending", description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=200)
):
    """List quarantined records"""
    records = get_quarantined_records(status, limit)
    return {
        "ok": True,
        "count": len(records),
        "records": records
    }


@router.get("/quarantine/stats")
async def quarantine_stats():
    """Get quarantine statistics"""
    return get_quarantine_stats()


@router.post("/quarantine/approve")
async def approve_quarantine(req: QuarantineApproveRequest):
    """Approve a quarantined record with corrections"""
    success, error = approve_quarantined_record(
        req.quarantine_id,
        req.corrected_data,
        req.reviewed_by,
        req.correction_notes
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {"ok": True, "message": "Record approved and written to main database"}


@router.post("/quarantine/reject")
async def reject_quarantine(req: QuarantineRejectRequest):
    """Reject a quarantined record"""
    success = reject_quarantined_record(req.quarantine_id, req.reviewed_by, req.reason)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to reject record")
    
    return {"ok": True, "message": "Record rejected"}


# =============================================================================
# Processing Endpoints
# =============================================================================

@router.post("/process/single/{log_id}")
async def process_single(log_id: str):
    """Process a single raw_log entry"""
    result = await process_single_async(log_id)
    return result


@router.post("/process/batch")
async def process_batch(batch_size: int = Query(default=10, ge=1, le=100)):
    """Process a batch of pending raw_logs"""
    result = await process_pending_async(batch_size)
    return result


@router.post("/process/retry")
async def retry_failed(
    limit: int = Query(default=5, ge=1, le=50),
    max_retries: int = Query(default=3, ge=1, le=10)
):
    """Retry failed records"""
    result = process_failed_batch(limit, max_retries)
    return result


@router.post("/process/start-background")
async def start_background():
    """Start background processing"""
    result = start_background_processing()
    return result


@router.post("/cancel/{entity_type}/{entity_id}")
async def cancel_entity(entity_type: str, entity_id: str, reason: str = ""):
    """
    Cancel/soft-delete an entity. Creates a CANCELLED event in the ledger.
    The entity is NOT physically deleted - it's marked as cancelled.
    """
    from backend.universal_adapter.event_ledger import (
        EntityType as ET, EventType, log_event, get_latest_version
    )
    
    # Map string to EntityType
    entity_map = {
        "order": ET.ORDER, "expense": ET.EXPENSE, "purchase": ET.PURCHASE
    }
    if entity_type.lower() not in entity_map:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {entity_type}")
    
    et = entity_map[entity_type.lower()]
    
    # Get current state
    version, current_data, _ = get_latest_version(entity_type.lower(), entity_id)
    if version == 0:
        raise HTTPException(status_code=404, detail=f"Entity {entity_type}:{entity_id} not found")
    
    # Add cancellation markers
    cancelled_data = current_data.copy() if current_data else {}
    cancelled_data["_status"] = "cancelled"
    cancelled_data["_cancelled_at"] = datetime.utcnow().isoformat()
    cancelled_data["_cancel_reason"] = reason
    
    # Log cancellation event
    event = log_event(
        entity_type=et,
        entity_id=entity_id,
        event_type=EventType.CANCELLED,
        data_after=cancelled_data,
        data_before=current_data,
        source_system="api_cancel",
        change_reason=reason or "User cancelled"
    )
    
    if event:
        return {
            "ok": True,
            "message": f"{entity_type} {entity_id} cancelled",
            "version": event.version,
            "event_id": event.event_id
        }
    return {"ok": False, "error": "Failed to cancel entity"}


@router.post("/process/stop-background")
async def stop_background():
    """Stop background processing"""
    result = stop_background_processing()
    return result


@router.get("/process/status")
async def processor_status():
    """Get processor status and statistics"""
    return get_processor_stats()


# =============================================================================
# Statistics Endpoints
# =============================================================================

@router.get("/stats")
async def system_stats():
    """Get overall Universal Adapter statistics"""
    from backend.universal_adapter.airlock import _get_bq_client
    
    client, cfg = _get_bq_client()
    if not client:
        return {"ok": False, "error": "Database not available"}
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        
        # Raw logs stats
        raw_logs_query = f"""
        SELECT status, COUNT(*) as count
        FROM `{project_id}.{dataset_id}.raw_logs`
        WHERE received_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        GROUP BY status
        """
        raw_result = list(client.query(raw_logs_query).result())
        raw_stats = {row.status: row.count for row in raw_result}
        
        # Quarantine stats
        quar_stats = get_quarantine_stats()
        
        # Processing stats
        proc_stats = get_processor_stats()
        
        return {
            "ok": True,
            "timestamp": datetime.utcnow().isoformat(),
            "last_24h": {
                "raw_logs": raw_stats,
                "total_ingested": sum(raw_stats.values())
            },
            "quarantine": quar_stats.get("stats", {}),
            "processor": proc_stats
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/stats/mappings")
async def mapping_stats():
    """Get schema mapping cache statistics"""
    from backend.universal_adapter.airlock import _get_bq_client
    
    client, cfg = _get_bq_client()
    if not client:
        return {"ok": False, "error": "Database not available"}
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        
        query = f"""
        SELECT 
            source_identifier,
            target_schema,
            use_count,
            confidence,
            created_by,
            CAST(created_at AS STRING) as created_at,
            CAST(last_used_at AS STRING) as last_used_at
        FROM `{project_id}.{dataset_id}.schema_mappings`
        ORDER BY use_count DESC
        LIMIT 50
        """
        result = list(client.query(query).result())
        
        mappings = [
            {
                "source_identifier": row.source_identifier,
                "target_schema": row.target_schema,
                "use_count": row.use_count,
                "confidence": row.confidence,
                "created_by": row.created_by,
                "created_at": row.created_at,
                "last_used_at": row.last_used_at
            }
            for row in result
        ]
        
        return {
            "ok": True,
            "count": len(mappings),
            "mappings": mappings
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =============================================================================
# Event Ledger - Immutable Audit Trail
# =============================================================================

@router.get("/events/history/{entity_type}/{entity_id}")
async def get_entity_history(entity_type: str, entity_id: str, limit: int = 50):
    """
    Get the full history of an entity (all versions/changes).
    Perfect for auditing "who changed what, when".
    """
    from backend.universal_adapter.event_ledger import get_entity_history as get_history
    
    history = get_history(entity_type, entity_id, limit=limit)
    
    return {
        "ok": True,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "version_count": len(history),
        "history": history
    }


@router.get("/events/latest/{entity_type}/{entity_id}")
async def get_entity_latest(entity_type: str, entity_id: str):
    """Get the current/latest state of an entity"""
    from backend.universal_adapter.event_ledger import get_latest_state
    
    state = get_latest_state(entity_type, entity_id)
    
    if state is None:
        raise HTTPException(status_code=404, detail=f"Entity {entity_type}:{entity_id} not found")
    
    return {
        "ok": True,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "data": state
    }


@router.get("/events/changes")
async def get_recent_changes(
    entity_type: Optional[str] = None,
    hours: int = 24
):
    """Get summary of all changes in the last N hours"""
    from backend.universal_adapter.event_ledger import get_change_summary
    from datetime import datetime, timezone, timedelta
    
    start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    summary = get_change_summary(entity_type=entity_type, start_time=start_time)
    
    return {
        "ok": True,
        "period_hours": hours,
        "filter_entity_type": entity_type,
        "summary": summary
    }


@router.post("/events/init-views")
async def init_event_views():
    """Create/update BigQuery views for latest state queries"""
    from backend.universal_adapter.event_ledger import create_latest_state_views, ensure_event_log_table
    
    ensure_event_log_table()
    success = create_latest_state_views()
    
    return {
        "ok": success,
        "message": "Event views created" if success else "Failed to create views"
    }


# =============================================================================
# Reconciliation - Gap Detection & Recovery
# =============================================================================

@router.get("/reconciliation/unprocessed")
async def get_unprocessed_logs(hours_back: int = 24, limit: int = 100):
    """Find raw_logs that weren't processed into event_log (potential gaps)"""
    from backend.universal_adapter.reconciliation import find_unprocessed_raw_logs
    
    gaps = find_unprocessed_raw_logs(hours_back=hours_back, limit=limit)
    
    return {
        "ok": True,
        "hours_checked": hours_back,
        "gaps_found": len(gaps),
        "gaps": gaps
    }


@router.get("/reconciliation/time-gaps")
async def get_time_gaps(
    entity_type: str = "order",
    hours_back: int = 24,
    min_gap_minutes: int = 120
):
    """Find time periods with no events (potential outage periods)"""
    from backend.universal_adapter.reconciliation import find_time_gaps
    from datetime import datetime, timezone, timedelta
    
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours_back)
    
    gaps = find_time_gaps(
        entity_type=entity_type,
        start_time=start_time,
        end_time=end_time,
        expected_interval_minutes=min_gap_minutes
    )
    
    return {
        "ok": True,
        "entity_type": entity_type,
        "period_hours": hours_back,
        "min_gap_minutes": min_gap_minutes,
        "gaps_found": len(gaps),
        "gaps": [
            {"start": g[0].isoformat() if g[0] else None, 
             "end": g[1].isoformat() if g[1] else None}
            for g in gaps
        ]
    }


@router.post("/reconciliation/run")
async def run_reconciliation(hours_back: int = 24, background_tasks: BackgroundTasks = None):
    """Run the reconciliation check (finds missing data, doesn't auto-recover)"""
    from backend.universal_adapter.reconciliation import run_daily_reconciliation
    
    result = run_daily_reconciliation(hours_back=hours_back)
    
    return {
        "ok": True,
        "result": result.to_dict()
    }


@router.get("/reconciliation/consistency/{entity_type}/{entity_id}")
async def check_consistency(entity_type: str, entity_id: str):
    """Check if event_log state matches main table for an entity"""
    from backend.universal_adapter.reconciliation import check_data_consistency
    
    result = check_data_consistency(entity_type, entity_id)
    
    return {
        "ok": result.get("status") == "consistent",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "result": result
    }


@router.get("/reconciliation/hourly-check")
async def hourly_health_check():
    """Quick hourly check for critical issues (stuck records, etc.)"""
    from backend.universal_adapter.reconciliation import hourly_check
    
    return hourly_check()


# =============================================================================
# Include Airlock Router
# =============================================================================

# The airlock router is mounted separately to maintain its /webhook prefix
# Include it in main.py alongside this router
