"""
GENESIS PROTOCOL - Ledger API Router
Universal Ledger CRUD operations with tenant isolation
"""
import os
import uuid
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from google.cloud import bigquery
import logging

from backend.core.ledger import LedgerEntry, LedgerType, LedgerSource
from backend.core.security import TenantIsolation
from backend.core.validators import TenantValidator, LedgerValidator, QueryValidator
from backend.core.exceptions import (
    LedgerValidationError, 
    TenantIsolationError, 
    BigQueryError,
    raise_http_400,
    raise_http_500
)
from pillars.config_vault import EffectiveSettings
from utils.bq_guardrails import estimate_query_cost

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ledger", tags=["ledger"])

class LedgerCreateRequest(BaseModel):
    """Request to create a ledger entry"""
    org_id: str
    location_id: str
    timestamp: datetime
    entry_date: date
    type: LedgerType
    amount: float
    entry_source: LedgerSource
    source_id: Optional[str] = None
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    metadata: dict = {}


@router.post("/entries")
async def create_ledger_entry(request: LedgerCreateRequest):
    """
    Create a new ledger entry
    This is the universal entry point for all financial events
    """
    try:
        import uuid
        from google.cloud import bigquery
        from pillars.config_vault import EffectiveSettings
        
        cfg = EffectiveSettings()
        client = bigquery.Client.from_service_account_json(cfg.KEY_FILE)
        
        entry = LedgerEntry(
            id=str(uuid.uuid4()),
            org_id=request.org_id,
            location_id=request.location_id,
            timestamp=request.timestamp,
            entry_date=request.entry_date,
            type=request.type,
            amount=request.amount,
            entry_source=request.entry_source,
            source_id=request.source_id,
            entity_id=request.entity_id,
            entity_name=request.entity_name,
            category=request.category,
            subcategory=request.subcategory,
            description=request.description,
            metadata=request.metadata,
        )
        
        table_id = f"{cfg.PROJECT_ID}.{cfg.DATASET_ID}.ledger_universal"
        
        rows = [entry.dict()]
        errors = client.insert_rows_json(table_id, rows)
        
        if errors:
            raise HTTPException(status_code=500, detail=f"Insert failed: {errors}")
        
        return {"ok": True, "entry_id": entry.id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entries")
async def query_ledger_entries(
    org_id: str = Query(...),
    location_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    type: Optional[LedgerType] = Query(None),
    limit: int = Query(100, le=1000)
):
    """
    Query ledger entries with tenant isolation
    """
    try:
        from google.cloud import bigquery
        from pillars.config_vault import EffectiveSettings
        from utils.bq_guardrails import query_to_df
        
        cfg = EffectiveSettings()
        client = bigquery.Client.from_service_account_json(cfg.KEY_FILE)
        
        context = TenantContext(org_id=org_id, location_id=location_id or "", user_id="system")
        
        where_conditions = [context.to_sql_where()]
        
        if start_date:
            where_conditions.append(f"entry_date >= DATE('{start_date}')")
        if end_date:
            where_conditions.append(f"entry_date <= DATE('{end_date}')")
        if type:
            where_conditions.append(f"type = '{type.value}'")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT *
        FROM `{cfg.PROJECT_ID}.{cfg.DATASET_ID}.ledger_universal`
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        
        df, _ = query_to_df(client, cfg, query, purpose="api.ledger.query")
        
        return {
            "ok": True,
            "entries": df.to_dict("records") if not df.empty else [],
            "count": len(df)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
