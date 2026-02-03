"""
Quarantine API - UniversalEvent Review System
==============================================
Phase 3D: API endpoints for reviewing and resolving quarantined events.

Endpoints:
- GET /list - List quarantined events for a tenant
- POST /resolve - Approve or reject a quarantined event

This is the NEW quarantine flow for UniversalEvent objects.
(Old flow at /adapter/quarantine uses raw_logs-based validation)
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel

# Windows encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class QuarantinedEvent(BaseModel):
    """Quarantined event for review"""
    event_id: str
    entity_name: str
    category: str
    sub_category: str
    amount: Optional[float] = None
    confidence_score: float
    ai_reasoning: str
    quarantine_reason: str
    status: str
    timestamp: str
    rich_data: Optional[str] = None


class QuarantineListResponse(BaseModel):
    """Response for quarantine list endpoint"""
    ok: bool
    count: int
    events: List[Dict[str, Any]]
    tenant_id: str


class ResolveRequest(BaseModel):
    """Request to resolve a quarantined event"""
    event_id: str
    decision: str  # "APPROVE" or "REJECT"
    correction: Optional[Dict[str, Any]] = None
    reviewed_by: str = "human"
    notes: Optional[str] = None


class ResolveResponse(BaseModel):
    """Response for resolve endpoint"""
    ok: bool
    message: str
    event_id: str
    decision: str
    learned: bool = False


# =============================================================================
# Helper Functions
# =============================================================================

def _get_quarantine_file(tenant_id: str) -> Path:
    """Get path to quarantine file for tenant"""
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data" / "ledger"
    safe_tenant = tenant_id.replace("/", "_").replace("\\", "_")
    return data_dir / f"{safe_tenant}_quarantine.jsonl"


def _load_quarantine_events(tenant_id: str) -> List[Dict[str, Any]]:
    """Load all quarantined events for a tenant"""
    file_path = _get_quarantine_file(tenant_id)
    events = []
    
    if not file_path.exists():
        return events
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        event = json.loads(line)
                        events.append(event)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"[QUARANTINE API] Error loading events: {e}")
    
    return events


def _save_quarantine_events(tenant_id: str, events: List[Dict[str, Any]]) -> bool:
    """Save quarantined events back to file (overwrites)"""
    file_path = _get_quarantine_file(tenant_id)
    
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            for event in events:
                f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        return True
    except Exception as e:
        print(f"[QUARANTINE API] Error saving events: {e}")
        return False


def _remove_event_from_quarantine(tenant_id: str, event_id: str) -> Optional[Dict[str, Any]]:
    """Remove an event from quarantine and return it"""
    events = _load_quarantine_events(tenant_id)
    removed_event = None
    remaining_events = []
    
    for event in events:
        if event.get("event_id") == event_id:
            removed_event = event
        else:
            remaining_events.append(event)
    
    if removed_event:
        _save_quarantine_events(tenant_id, remaining_events)
    
    return removed_event


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/list", response_model=QuarantineListResponse)
async def list_quarantined_events(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    status: str = Query(default="pending_review", description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=200)
):
    """
    List quarantined events for a tenant.
    
    These are UniversalEvent objects that had low confidence scores
    and need human review before entering the main ledger.
    """
    events = _load_quarantine_events(x_tenant_id)
    
    # Filter by status if specified
    if status != "all":
        events = [e for e in events if e.get("_status") == status]
    
    # Apply limit
    events = events[:limit]
    
    # Format for response
    formatted_events = []
    for event in events:
        formatted_events.append({
            "event_id": event.get("event_id"),
            "entity_name": event.get("entity_name"),
            "category": event.get("category"),
            "sub_category": event.get("sub_category"),
            "amount": event.get("amount"),
            "confidence_score": event.get("confidence_score"),
            "ai_reasoning": event.get("ai_reasoning"),
            "quarantine_reason": event.get("_quarantine_reason", "Low confidence"),
            "status": event.get("_status", "pending_review"),
            "timestamp": event.get("timestamp"),
            "rich_data": event.get("rich_data"),
            "written_at": event.get("_written_at")
        })
    
    return QuarantineListResponse(
        ok=True,
        count=len(formatted_events),
        events=formatted_events,
        tenant_id=x_tenant_id
    )


@router.post("/resolve", response_model=ResolveResponse)
async def resolve_quarantined_event(
    req: ResolveRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID")
):
    """
    Resolve a quarantined event by approving or rejecting it.
    
    - APPROVE: Moves event to main ledger, updates brain cache
    - REJECT: Removes event from quarantine (discarded)
    """
    decision = req.decision.upper()
    if decision not in ["APPROVE", "REJECT"]:
        raise HTTPException(
            status_code=400,
            detail="Decision must be 'APPROVE' or 'REJECT'"
        )
    
    # Find and remove event from quarantine
    event = _remove_event_from_quarantine(x_tenant_id, req.event_id)
    
    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Event {req.event_id} not found in quarantine"
        )
    
    learned = False
    
    if decision == "REJECT":
        # Event is simply discarded
        print(f"[QUARANTINE API] REJECTED event {req.event_id}: {event.get('entity_name')}")
        return ResolveResponse(
            ok=True,
            message=f"Event rejected and removed from quarantine",
            event_id=req.event_id,
            decision="REJECT",
            learned=False
        )
    
    # === APPROVE FLOW ===
    
    # Apply corrections if provided
    if req.correction:
        for key, value in req.correction.items():
            if key in event and key not in ["event_id", "tenant_id"]:
                event[key] = value
                print(f"[QUARANTINE API] Applied correction: {key} = {value}")
    
    # Set verified and confidence
    event["verified"] = True
    event["verified_by"] = req.reviewed_by
    event["verified_at"] = datetime.utcnow().isoformat()
    event["confidence_score"] = 1.0  # Human-verified = trusted
    
    # Remove quarantine metadata
    event.pop("_quarantine_reason", None)
    event.pop("_status", None)
    event.pop("_written_at", None)
    
    # Move to main ledger using LedgerWriter
    try:
        from backend.universal_adapter.ledger_writer import LedgerWriter
        from backend.universal_adapter.polymorphic_ledger import UniversalEvent
        
        # Reconstruct UniversalEvent
        approved_event = UniversalEvent(
            event_id=event.get("event_id"),
            tenant_id=event.get("tenant_id", x_tenant_id),
            timestamp=event.get("timestamp"),
            source_system=event.get("source_system", "quarantine_approved"),
            category=event.get("category"),
            sub_category=event.get("sub_category"),
            confidence_score=1.0,
            ai_reasoning=f"Human approved by {req.reviewed_by}",
            amount=event.get("amount"),
            entity_name=event.get("entity_name"),
            reference_id=event.get("reference_id"),
            rich_data=event.get("rich_data"),
            schema_fingerprint=event.get("schema_fingerprint"),
            verified=True,
            verified_by=req.reviewed_by,
            verified_at=datetime.utcnow().isoformat()
        )
        
        # Write to main ledger (bypass Traffic Cop since verified=True)
        writer = LedgerWriter()
        result = writer.write_batch([approved_event], x_tenant_id)
        print(f"[QUARANTINE API] Wrote approved event to ledger: {result}")
        
    except Exception as e:
        print(f"[QUARANTINE API] Error writing to ledger: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write approved event to ledger: {str(e)}"
        )
    
    # Teach the brain
    try:
        from backend.universal_adapter.semantic_brain import get_brain
        
        brain = get_brain()
        brain.learn(approved_event)
        learned = True
        print(f"[QUARANTINE API] Brain learned from approved event")
        
    except Exception as e:
        print(f"[QUARANTINE API] Warning: Brain learning failed: {e}")
        # Don't fail the request - event was still approved
    
    return ResolveResponse(
        ok=True,
        message=f"Event approved, moved to ledger, brain updated",
        event_id=req.event_id,
        decision="APPROVE",
        learned=learned
    )


@router.get("/stats")
async def quarantine_stats(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID")
):
    """Get quarantine statistics for a tenant"""
    events = _load_quarantine_events(x_tenant_id)
    
    # Count by status
    status_counts = {}
    category_counts = {}
    
    for event in events:
        status = event.get("_status", "pending_review")
        status_counts[status] = status_counts.get(status, 0) + 1
        
        category = event.get("category", "UNKNOWN")
        category_counts[category] = category_counts.get(category, 0) + 1
    
    return {
        "ok": True,
        "tenant_id": x_tenant_id,
        "total": len(events),
        "by_status": status_counts,
        "by_category": category_counts,
        "file": str(_get_quarantine_file(x_tenant_id))
    }
