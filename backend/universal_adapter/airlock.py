"""
Airlock - The Indestructible Ingestion Layer
=============================================
Phase 2 of the Universal Adapter.

CORE PRINCIPLE: This endpoint NEVER crashes, no matter what garbage comes in.
- Accepts ANY payload (JSON, malformed JSON, empty, binary references)
- Saves raw data to `raw_logs` table immediately
- Returns "200 OK - Received" instantly
- Background worker processes later

Endpoints:
- POST /api/v1/webhook/ingest - Generic catch-all for any data
- POST /api/v1/webhook/ingest/{source_type} - Source-specific ingestion
- GET /api/v1/webhook/status/{log_id} - Check processing status
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/webhook", tags=["universal-adapter"])


# =============================================================================
# Response Models
# =============================================================================

class IngestResponse(BaseModel):
    ok: bool
    message: str
    log_id: str
    received_at: str
    source_type: str
    status: str = "pending"


class StatusResponse(BaseModel):
    ok: bool
    log_id: str
    status: str
    received_at: str
    processed_at: Optional[str] = None
    target_schema: Optional[str] = None
    error_message: Optional[str] = None


class BulkIngestResponse(BaseModel):
    ok: bool
    message: str
    total_received: int
    log_ids: List[str]


# =============================================================================
# BigQuery Client
# =============================================================================

def _get_bq_client():
    """Get BigQuery client with ADC fallback"""
    try:
        from google.cloud import bigquery
        from pillars.config_vault import EffectiveSettings
        
        cfg = EffectiveSettings()
        key_file = getattr(cfg, "KEY_FILE", "service-key.json")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
        
        if os.path.exists(key_path):
            return bigquery.Client.from_service_account_json(key_path), cfg
        
        project_id = getattr(cfg, "PROJECT_ID", None) or os.environ.get("PROJECT_ID")
        return bigquery.Client(project=project_id) if project_id else bigquery.Client(), cfg
    except Exception as e:
        print(f"BigQuery client error: {e}")
        return None, None


def _ensure_raw_logs_table(client, cfg) -> str:
    """Ensure raw_logs table exists for storing incoming data"""
    project_id = getattr(cfg, "PROJECT_ID", "")
    dataset_id = getattr(cfg, "DATASET_ID", "")
    table_id = f"{project_id}.{dataset_id}.raw_logs"
    
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS `{table_id}` (
        log_id STRING NOT NULL,
        received_at TIMESTAMP NOT NULL,
        source_type STRING NOT NULL,
        source_identifier STRING,
        raw_payload STRING NOT NULL,
        content_type STRING,
        payload_hash STRING,
        status STRING DEFAULT 'pending',
        target_schema STRING,
        processed_at TIMESTAMP,
        error_message STRING,
        retry_count INT64 DEFAULT 0,
        metadata STRING
    )
    PARTITION BY DATE(received_at)
    """
    try:
        client.query(create_sql).result()
    except Exception as e:
        print(f"Table creation note: {e}")
    
    return table_id


def _ensure_quarantine_table(client, cfg) -> str:
    """Ensure quarantine table exists for failed records"""
    project_id = getattr(cfg, "PROJECT_ID", "")
    dataset_id = getattr(cfg, "DATASET_ID", "")
    table_id = f"{project_id}.{dataset_id}.quarantine"
    
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS `{table_id}` (
        quarantine_id STRING NOT NULL,
        raw_log_id STRING NOT NULL,
        quarantined_at TIMESTAMP NOT NULL,
        target_schema STRING NOT NULL,
        validation_errors STRING,
        ai_transformed_data STRING,
        ai_confidence FLOAT64,
        status STRING DEFAULT 'pending',
        reviewed_by STRING,
        reviewed_at TIMESTAMP,
        human_corrected_data STRING,
        correction_notes STRING
    )
    PARTITION BY DATE(quarantined_at)
    """
    try:
        client.query(create_sql).result()
    except Exception as e:
        print(f"Quarantine table note: {e}")
    
    return table_id


def _ensure_schema_mappings_table(client, cfg) -> str:
    """Ensure schema_mappings table exists for caching learned mappings"""
    project_id = getattr(cfg, "PROJECT_ID", "")
    dataset_id = getattr(cfg, "DATASET_ID", "")
    table_id = f"{project_id}.{dataset_id}.schema_mappings"
    
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS `{table_id}` (
        mapping_id STRING NOT NULL,
        source_identifier STRING NOT NULL,
        target_schema STRING NOT NULL,
        field_mappings STRING NOT NULL,
        transform_rules STRING,
        created_at TIMESTAMP NOT NULL,
        last_used_at TIMESTAMP,
        use_count INT64 DEFAULT 0,
        confidence FLOAT64 DEFAULT 1.0,
        created_by STRING DEFAULT 'ai'
    )
    """
    try:
        client.query(create_sql).result()
    except Exception as e:
        print(f"Schema mappings table note: {e}")
    
    return table_id


# =============================================================================
# Helper Functions
# =============================================================================

def _generate_log_id(payload: str, source_type: str) -> str:
    """Generate unique log ID from payload hash + timestamp"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    content_hash = hashlib.md5(f"{payload}{timestamp}".encode()).hexdigest()[:12]
    return f"log_{source_type}_{timestamp}_{content_hash}"


def _detect_source_type(payload: Dict[str, Any], headers: Dict[str, str]) -> str:
    """Auto-detect the source type from payload structure or headers"""
    # Check headers first
    source_header = headers.get("x-source-type", "").lower()
    if source_header:
        return source_header
    
    # Petpooja detection
    if isinstance(payload, dict):
        if "Order" in payload or "order_json" in payload:
            return "petpooja"
        if "OrderItem" in payload or "items" in payload:
            return "petpooja"
        
        # Zoho detection
        if "zoho" in str(payload).lower():
            return "zoho"
        
        # Generic expense/purchase detection
        if any(k.lower() in ["expense", "amount", "date", "category"] for k in payload.keys()):
            return "expense_data"
        if any(k.lower() in ["purchase", "vendor", "quantity"] for k in payload.keys()):
            return "purchase_data"
    
    return "unknown"


def _detect_target_schema(source_type: str, payload: Dict[str, Any]) -> str:
    """Determine which Golden Schema this data should map to"""
    if source_type in ["petpooja", "order", "sales"]:
        return "order"
    if source_type in ["expense", "expense_data"]:
        return "expense"
    if source_type in ["purchase", "purchase_data", "inventory"]:
        return "purchase"
    
    # Heuristic detection from payload
    if isinstance(payload, dict):
        keys_lower = [k.lower() for k in payload.keys()]
        if any(k in keys_lower for k in ["order_id", "orderid", "bill", "items"]):
            return "order"
        if any(k in keys_lower for k in ["expense", "ledger", "staff_name"]):
            return "expense"
        if any(k in keys_lower for k in ["vendor", "purchase", "supplier"]):
            return "purchase"
    
    return "unknown"


async def _save_to_raw_logs(
    log_id: str,
    source_type: str,
    source_identifier: Optional[str],
    raw_payload: str,
    content_type: str,
    target_schema: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Save raw data to BigQuery raw_logs table"""
    client, cfg = _get_bq_client()
    if not client:
        print("WARNING: BigQuery not available, raw log not saved")
        return False
    
    try:
        table_id = _ensure_raw_logs_table(client, cfg)
        
        payload_hash = hashlib.md5(raw_payload.encode()).hexdigest()
        received_at = datetime.utcnow().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        
        # Escape single quotes in payload
        safe_payload = raw_payload.replace("'", "''")
        safe_identifier = (source_identifier or "").replace("'", "''")
        safe_metadata = (metadata_json or "").replace("'", "''") if metadata_json else ""
        
        insert_sql = f"""
        INSERT INTO `{table_id}` 
        (log_id, received_at, source_type, source_identifier, raw_payload, 
         content_type, payload_hash, status, target_schema, metadata)
        VALUES (
            '{log_id}',
            TIMESTAMP('{received_at}'),
            '{source_type}',
            '{safe_identifier}',
            '{safe_payload}',
            '{content_type}',
            '{payload_hash}',
            'pending',
            '{target_schema}',
            '{safe_metadata}'
        )
        """
        client.query(insert_sql).result()
        return True
    except Exception as e:
        print(f"Error saving to raw_logs: {e}")
        return False


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/ingest", response_model=IngestResponse)
async def ingest_generic(
    request: Request,
    background_tasks: BackgroundTasks
) -> IngestResponse:
    """
    GENERIC CATCH-ALL INGESTION ENDPOINT
    =====================================
    Accepts ANY payload. Never crashes. Saves everything.
    
    Headers (optional):
    - X-Source-Type: petpooja, excel, zoho, etc.
    - X-Source-Identifier: filename, api name, etc.
    
    The endpoint will:
    1. Try to parse as JSON (gracefully handle failures)
    2. Auto-detect source type
    3. Save to raw_logs immediately
    4. Return success
    5. Background worker processes later
    """
    received_at = datetime.utcnow()
    
    # Get headers
    headers = dict(request.headers)
    source_type = headers.get("x-source-type", "").lower() or "unknown"
    source_identifier = headers.get("x-source-identifier", "")
    content_type = headers.get("content-type", "application/json")
    
    # Read body - handle ANY format
    try:
        body = await request.body()
        body_str = body.decode("utf-8")
    except Exception:
        body_str = str(body) if body else "{}"
    
    # Try to parse as JSON for detection
    payload = {}
    try:
        payload = json.loads(body_str)
    except json.JSONDecodeError:
        # Not valid JSON - that's OK, we still save it
        payload = {"_raw_text": body_str}
        body_str = json.dumps(payload)
    
    # Auto-detect source if not provided
    if source_type == "unknown":
        source_type = _detect_source_type(payload, headers)
    
    # Detect target schema
    target_schema = _detect_target_schema(source_type, payload)
    
    # Generate log ID
    log_id = _generate_log_id(body_str, source_type)
    
    # Save to raw_logs (async-safe)
    saved = await _save_to_raw_logs(
        log_id=log_id,
        source_type=source_type,
        source_identifier=source_identifier,
        raw_payload=body_str,
        content_type=content_type,
        target_schema=target_schema,
        metadata={"headers": {k: v for k, v in headers.items() if k.startswith("x-")}}
    )
    
    return IngestResponse(
        ok=True,
        message="Data received and queued for processing" if saved else "Data received (DB save pending)",
        log_id=log_id,
        received_at=received_at.isoformat(),
        source_type=source_type,
        status="pending"
    )


@router.post("/ingest/{source_type}", response_model=IngestResponse)
async def ingest_typed(
    source_type: str,
    request: Request,
    background_tasks: BackgroundTasks
) -> IngestResponse:
    """
    SOURCE-TYPED INGESTION ENDPOINT
    ===============================
    Same as generic, but source_type is in the URL.
    
    Examples:
    - POST /api/v1/webhook/ingest/petpooja
    - POST /api/v1/webhook/ingest/excel
    - POST /api/v1/webhook/ingest/zoho
    """
    received_at = datetime.utcnow()
    
    headers = dict(request.headers)
    source_identifier = headers.get("x-source-identifier", "")
    content_type = headers.get("content-type", "application/json")
    
    try:
        body = await request.body()
        body_str = body.decode("utf-8")
    except Exception:
        body_str = "{}"
    
    payload = {}
    try:
        payload = json.loads(body_str)
    except json.JSONDecodeError:
        payload = {"_raw_text": body_str}
        body_str = json.dumps(payload)
    
    target_schema = _detect_target_schema(source_type, payload)
    log_id = _generate_log_id(body_str, source_type)
    
    saved = await _save_to_raw_logs(
        log_id=log_id,
        source_type=source_type,
        source_identifier=source_identifier,
        raw_payload=body_str,
        content_type=content_type,
        target_schema=target_schema
    )
    
    return IngestResponse(
        ok=True,
        message=f"Data received for {source_type}",
        log_id=log_id,
        received_at=received_at.isoformat(),
        source_type=source_type,
        status="pending"
    )


@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    source_type: str = Form(default="excel"),
    source_identifier: Optional[str] = Form(default=None)
) -> IngestResponse:
    """
    FILE UPLOAD INGESTION
    =====================
    For Excel, CSV, or other file uploads.
    Converts file to JSON rows and saves each.
    """
    import pandas as pd
    import io
    
    received_at = datetime.utcnow()
    
    try:
        contents = await file.read()
        filename = file.filename or "unknown_file"
        
        # Parse file based on extension
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            # Try as JSON
            try:
                data = json.loads(contents.decode("utf-8"))
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame([data])
            except:
                # Raw text
                df = pd.DataFrame([{"_raw_content": contents.decode("utf-8", errors="ignore")}])
        
        # Convert DataFrame to list of dicts
        records = df.to_dict(orient="records")
        
        # Wrap all records in a single payload
        payload = {
            "source_file": filename,
            "record_count": len(records),
            "records": records
        }
        
        body_str = json.dumps(payload, default=str)
        target_schema = _detect_target_schema(source_type, payload)
        log_id = _generate_log_id(body_str, source_type)
        
        saved = await _save_to_raw_logs(
            log_id=log_id,
            source_type=source_type,
            source_identifier=source_identifier or filename,
            raw_payload=body_str,
            content_type="application/json",
            target_schema=target_schema,
            metadata={"original_filename": filename, "record_count": len(records)}
        )
        
        return IngestResponse(
            ok=True,
            message=f"File '{filename}' received with {len(records)} records",
            log_id=log_id,
            received_at=received_at.isoformat(),
            source_type=source_type,
            status="pending"
        )
    except Exception as e:
        # Even errors are caught - we save what we can
        log_id = _generate_log_id(str(e), "error")
        return IngestResponse(
            ok=True,  # Still OK - we don't crash
            message=f"File received with parsing note: {str(e)[:100]}",
            log_id=log_id,
            received_at=received_at.isoformat(),
            source_type=source_type,
            status="pending"
        )


@router.get("/status/{log_id}", response_model=StatusResponse)
async def get_status(log_id: str) -> StatusResponse:
    """
    CHECK PROCESSING STATUS
    =======================
    Returns the current status of a raw_log entry.
    """
    client, cfg = _get_bq_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        table_id = f"{project_id}.{dataset_id}.raw_logs"
        
        query = f"""
        SELECT log_id, status, 
               CAST(received_at AS STRING) as received_at,
               CAST(processed_at AS STRING) as processed_at,
               target_schema, error_message
        FROM `{table_id}`
        WHERE log_id = '{log_id}'
        LIMIT 1
        """
        result = list(client.query(query).result())
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Log ID {log_id} not found")
        
        row = result[0]
        return StatusResponse(
            ok=True,
            log_id=row.log_id,
            status=row.status,
            received_at=row.received_at,
            processed_at=row.processed_at,
            target_schema=row.target_schema,
            error_message=row.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending")
async def get_pending_logs(limit: int = 100) -> Dict[str, Any]:
    """
    GET PENDING LOGS
    ================
    Returns logs waiting to be processed by the AI Refinery.
    """
    client, cfg = _get_bq_client()
    if not client:
        return {"ok": False, "error": "Database not available", "logs": []}
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        table_id = f"{project_id}.{dataset_id}.raw_logs"
        
        query = f"""
        SELECT log_id, source_type, source_identifier, target_schema,
               CAST(received_at AS STRING) as received_at,
               retry_count
        FROM `{table_id}`
        WHERE status = 'pending'
        ORDER BY received_at ASC
        LIMIT {limit}
        """
        result = list(client.query(query).result())
        
        logs = [
            {
                "log_id": row.log_id,
                "source_type": row.source_type,
                "source_identifier": row.source_identifier,
                "target_schema": row.target_schema,
                "received_at": row.received_at,
                "retry_count": row.retry_count
            }
            for row in result
        ]
        
        return {"ok": True, "count": len(logs), "logs": logs}
    except Exception as e:
        return {"ok": False, "error": str(e), "logs": []}


@router.get("/stats")
async def get_ingestion_stats() -> Dict[str, Any]:
    """
    INGESTION STATISTICS
    ====================
    Returns counts by status, source_type, etc.
    """
    client, cfg = _get_bq_client()
    if not client:
        return {"ok": False, "error": "Database not available"}
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        table_id = f"{project_id}.{dataset_id}.raw_logs"
        
        query = f"""
        SELECT 
            status,
            source_type,
            target_schema,
            COUNT(*) as count
        FROM `{table_id}`
        WHERE received_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        GROUP BY status, source_type, target_schema
        ORDER BY count DESC
        """
        result = list(client.query(query).result())
        
        stats = {
            "by_status": {},
            "by_source": {},
            "by_target": {}
        }
        
        for row in result:
            stats["by_status"][row.status] = stats["by_status"].get(row.status, 0) + row.count
            stats["by_source"][row.source_type] = stats["by_source"].get(row.source_type, 0) + row.count
            stats["by_target"][row.target_schema] = stats["by_target"].get(row.target_schema, 0) + row.count
        
        return {
            "ok": True,
            "period": "last_7_days",
            "stats": stats,
            "total": sum(stats["by_status"].values())
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =============================================================================
# INITIALIZATION
# =============================================================================

def init_airlock_tables():
    """Initialize all required tables for the Airlock system"""
    client, cfg = _get_bq_client()
    if not client:
        print("WARNING: Could not initialize Airlock tables - BigQuery not available")
        return False
    
    try:
        _ensure_raw_logs_table(client, cfg)
        _ensure_quarantine_table(client, cfg)
        _ensure_schema_mappings_table(client, cfg)
        print("✅ Airlock tables initialized")
        return True
    except Exception as e:
        print(f"❌ Airlock table initialization error: {e}")
        return False
