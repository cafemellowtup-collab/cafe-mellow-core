"""
Generic Tabular Ingestion Endpoint
===================================
Phase 2B: Raw Ingestion Foundation for Excel and CSV files.
Phase 2C: Structure Detective - Auto-detect header rows.
Phase 2D: Short-Circuit + Multi-Table Intelligence with AI Judge.
Phase 2E: Universal Mapper - Fuzzy column matching to Universal Events.

This endpoint accepts file uploads (Excel/CSV), parses them into structured data,
maps them to Universal Events, and prepares them for the Universal Adapter.

Supported formats:
- .xlsx, .xls (Excel)
- .csv (Comma-separated values)

Features:
- Golden Path: Instant header detection for clean files (Row 0/1)
- Deep Scan: Finds headers buried up to Row 500
- AI Judge: Resolves ambiguous multi-table files
- Fuzzy Mapper: Auto-maps columns to semantic fields (date, amount, entity)
- Multi-tenant isolation via X-Tenant-ID header
- Safe JSON conversion

Future formats (not yet supported):
- PDF
- Images
"""

import sys
import os
import uuid
import io
import asyncio
import shutil
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Header, HTTPException, UploadFile, Query
from pydantic import BaseModel

import pandas as pd

from backend.universal_adapter.structure_detective import StructureDetective
from backend.universal_adapter.mapper import UniversalMapper
from backend.universal_adapter.ledger_writer import LedgerWriter
from backend.universal_adapter.semantic_brain import SemanticBrain, get_brain
from backend.core.titan_v3.unified_engine import get_titan_engine

# Windows console encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


router = APIRouter(prefix="/api/v1/ingest", tags=["Ingestion"])


class IngestResponse(BaseModel):
    """Response model for file ingestion"""
    status: str
    filename: str
    rows: int
    columns: List[str]
    sample_data: List[Dict[str, Any]] = []
    message: str = ""
    header_row_detected: int = 0
    detection_method: str = "golden_path"
    # Phase 2E: Mapping results
    mapped_events: int = 0
    failed_events: int = 0
    column_mapping: Dict[str, Any] = {}
    sample_event: Dict[str, Any] = {}
    # Phase 3A: Storage results
    storage_status: str = ""
    storage_details: Dict[str, Any] = {}
    # Phase 3B: Classification results
    classification_stats: Dict[str, Any] = {}


class AsyncUploadResponse(BaseModel):
    """Response for async file upload"""
    status: str
    file_id: str
    filename: str
    message: str


class FileStatusResponse(BaseModel):
    """Response for file status check"""
    file_id: str
    filename: str
    status: str  # queued, processing, completed, failed
    ai_detection: Optional[str] = None
    rows_processed: int = 0
    events_mapped: int = 0
    upload_time: str
    completed_time: Optional[str] = None
    error: Optional[str] = None
    ghost_items: int = 0
    duplicates: int = 0
    new_events: int = 0


# In-memory file status tracking (production would use Redis/DB)
_file_status: Dict[str, Dict[str, Any]] = {}

# Upload directory
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class IngestError(BaseModel):
    """Error response model"""
    status: str = "error"
    detail: str
    supported_formats: List[str] = [".xlsx", ".xls", ".csv"]


SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv"}
UNSUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}


def _detect_extension(filename: str) -> str:
    """Extract and normalize file extension"""
    if not filename:
        return ""
    parts = filename.rsplit(".", 1)
    if len(parts) < 2:
        return ""
    return f".{parts[1].lower()}"


def _sanitize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize column names for consistent processing"""
    df.columns = [
        str(col).strip().lower().replace(" ", "_").replace("-", "_")
        for col in df.columns
    ]
    return df


def _peek_columns(file_path: Path, ext: str) -> List[str]:
    """Quickly extract column names for Bouncer validation."""
    file_bytes = file_path.read_bytes()

    if ext in {".xlsx", ".xls"}:
        df_raw = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl", header=None)
        header_idx = StructureDetective.find_header_row(df_raw, max_scan=200)
        if header_idx > 0:
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl", header=header_idx)
        else:
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
    elif ext == ".csv":
        df_raw = pd.read_csv(io.BytesIO(file_bytes), header=None)
        header_idx = StructureDetective.find_header_row(df_raw, max_scan=200)
        if header_idx > 0:
            df = pd.read_csv(io.BytesIO(file_bytes), header=header_idx)
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))
    else:
        raise ValueError(f"Unknown format: {ext}")

    df = _sanitize_columns(df)
    return list(df.columns)


def _dataframe_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convert DataFrame to list of dicts, handling NaN/NaT values.
    This is the "Safety Step" - converts to JSON-serializable format.
    """
    df = df.fillna("")
    for col in df.columns:
        if df[col].dtype == "datetime64[ns]":
            df[col] = df[col].astype(str)
    return df.to_dict(orient="records")


def _process_file_background(file_id: str, file_path: Path, filename: str, tenant_id: str):
    """
    Background task to process uploaded file.
    Updates _file_status as it progresses.
    
    Phase 8 Fortress Upgrades:
    - Bouncer: Validates schema before processing (rejects junk files)
    - Sherlock: Classifies as STREAM (Sales) or STATE (Menu)
    - Ghost Logic: Creates provisional items for unknown menu items
    """
    global _file_status
    
    try:
        _file_status[file_id]["status"] = "processing"
        print(f"[ASYNC] Starting background processing for {filename} (ID: {file_id})")
        
        ext = _detect_extension(filename)
        file_bytes = file_path.read_bytes()
        detection_method = "golden_path"
        ai_detection = "Unknown"
        
        # Create AI Judge callback
        def ai_judge_callback(sample_rows: Dict[str, Any]) -> int:
            nonlocal detection_method
            try:
                engine = get_titan_engine(tenant_id=tenant_id)
                result = engine.analyze_file_structure(sample_rows)
                if result is not None:
                    detection_method = "ai_judge"
                return result
            except Exception as e:
                print(f"[AI JUDGE] Fallback failed: {e}")
                return None
        
        # Parse file based on extension
        if ext in {".xlsx", ".xls"}:
            df_raw = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl", header=None)
            candidates = StructureDetective.get_all_candidates(df_raw, max_scan=500)
            
            use_ai = False
            if len(candidates) >= 2:
                score_diff = abs(candidates[0]["final_score"] - candidates[1]["final_score"])
                if score_diff <= 2:
                    use_ai = True
                    detection_method = "deep_scan_ambiguous"
            
            header_idx = StructureDetective.find_header_row(
                df_raw, max_scan=500,
                ai_judge=ai_judge_callback if use_ai else None
            )
            
            if header_idx > 0:
                df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl", header=header_idx)
                if detection_method == "golden_path":
                    detection_method = "deep_scan"
            else:
                df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
                
        elif ext == ".csv":
            df_raw = pd.read_csv(io.BytesIO(file_bytes), header=None)
            candidates = StructureDetective.get_all_candidates(df_raw, max_scan=500)
            
            use_ai = False
            if len(candidates) >= 2:
                score_diff = abs(candidates[0]["final_score"] - candidates[1]["final_score"])
                if score_diff <= 2:
                    use_ai = True
                    detection_method = "deep_scan_ambiguous"
            
            header_idx = StructureDetective.find_header_row(
                df_raw, max_scan=500,
                ai_judge=ai_judge_callback if use_ai else None
            )
            
            if header_idx > 0:
                df = pd.read_csv(io.BytesIO(file_bytes), header=header_idx)
                if detection_method == "golden_path":
                    detection_method = "deep_scan"
            else:
                df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            raise ValueError(f"Unknown format: {ext}")
        
        # Sanitize and convert
        df = _sanitize_columns(df)
        records = _dataframe_to_records(df)
        
        _file_status[file_id]["rows_processed"] = len(df)
        
        # =====================================================================
        # PHASE 8: THE BOUNCER - Schema Validation
        # =====================================================================
        brain = get_brain()
        columns = list(df.columns)
        
        # Validate schema before processing
        classification = brain.classify_file(columns, filename)
        
        if not classification["valid"]:
            # REJECTED by Bouncer - mark as failed
            print(f"[BOUNCER] REJECTED {filename}: {classification['reason']}")
            _file_status[file_id]["status"] = "failed"
            _file_status[file_id]["error"] = f"File rejected: {classification['reason']}"
            _file_status[file_id]["ai_detection"] = "TYPE: UNKNOWN"
            _file_status[file_id]["completed_time"] = datetime.utcnow().isoformat()
            return  # Exit early - don't process junk files
        
        data_type = classification["data_type"]
        business_type = classification["business_type"]
        print(f"[SHERLOCK] Classified {filename} as {data_type} ({business_type}) with {classification['confidence']:.0%} confidence")
        
        # Store classification in status
        _file_status[file_id]["data_type"] = data_type
        _file_status[file_id]["business_type"] = business_type
        ai_detection = f"TYPE: {data_type}"
        
        # Map to Universal Events
        mapping_result = UniversalMapper.map_to_events(
            raw_data=records,
            tenant_id=tenant_id,
            source_system=f"file_upload:{filename}"
        )
        
        valid_events = mapping_result["valid_events"]
        _file_status[file_id]["events_mapped"] = len(valid_events)
        
        # Classify with SemanticBrain (Turbo Engine for large batches)
        if valid_events:
            turbo_size = getattr(brain, "TURBO_BATCH_SIZE", 50)
            if len(valid_events) >= turbo_size:
                try:
                    valid_events = asyncio.run(brain.classify_batch_async(valid_events))
                except RuntimeError:
                    # Fallback if event loop is already running
                    valid_events = brain.classify_batch(valid_events)
            else:
                valid_events = brain.classify_batch(valid_events)
            
            # Determine AI detection type from first event's category
            if valid_events and hasattr(valid_events[0], 'category'):
                cat = valid_events[0].category
                if cat:
                    ai_detection = f"TYPE: {cat.upper().replace(' ', '_')}"
            
            # Write to storage with Ghost Logic for STREAM data
            writer = LedgerWriter()
            storage_result = writer.write_batch(
                valid_events, 
                tenant_id,
                data_type=data_type  # Pass data type for Ghost Logic
            )
            # Update stats from storage result
            _file_status[file_id].update({
                'ghost_items': storage_result.get('ghost_items', 0),
                'duplicates': storage_result.get('duplicates', 0),
                'new_events': storage_result.get('count', 0)
            })
            print(f"[ASYNC] Stored {storage_result.get('count')} events for {filename} "
        
        # Detect file type from columns (fallback only)
        if not ai_detection or ai_detection == "Unknown":
            cols_lower = [c.lower() for c in df.columns]
            if any('recipe' in c or 'ingredient' in c for c in cols_lower):
                ai_detection = "TYPE: RECIPE_FILE"
            elif any('sale' in c or 'revenue' in c or 'total' in c for c in cols_lower):
                ai_detection = "TYPE: SALES_LEDGER"
            elif any('expense' in c or 'cost' in c or 'payment' in c for c in cols_lower):
                ai_detection = "TYPE: EXPENSE_LEDGER"
            elif any('inventory' in c or 'stock' in c or 'quantity' in c for c in cols_lower):
                ai_detection = "TYPE: INVENTORY_LOG"
            elif any('employee' in c or 'staff' in c or 'salary' in c for c in cols_lower):
                ai_detection = "TYPE: HR_DATA"
        
        # Mark completed
        _file_status[file_id]["status"] = "completed"
        _file_status[file_id]["ai_detection"] = ai_detection
        _file_status[file_id]["completed_time"] = datetime.utcnow().isoformat()
        
        print(f"[ASYNC] Completed processing {filename}: {len(valid_events)} events, detected as {ai_detection}")
        
    except Exception as e:
        # Full traceback for debugging
        full_traceback = traceback.format_exc()
        print(f"[ASYNC ERROR] Processing failed for {filename}:")
        print(full_traceback)
        
        _file_status[file_id]["status"] = "failed"
        _file_status[file_id]["error"] = f"{type(e).__name__}: {str(e)}"
        _file_status[file_id]["completed_time"] = datetime.utcnow().isoformat()


@router.post("/file", response_model=AsyncUploadResponse)
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Excel (.xlsx, .xls) or CSV file"),
    x_tenant_id: str = Header(..., alias="X-Tenant-ID", description="Tenant identifier"),
):
    """
    Async File Upload Endpoint (Phase 7B)
    
    Accepts file, saves to disk, and queues background processing.
    Returns immediately with file_id for status tracking.
    
    **Headers:**
    - `X-Tenant-ID`: Required. The tenant identifier for multi-tenant isolation.
    
    **Returns:**
    - `status`: "queued"
    - `file_id`: UUID for tracking processing status
    - `filename`: Original filename
    """
    global _file_status
    
    # Validate tenant_id
    tenant_id = x_tenant_id.strip()
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="X-Tenant-ID header is required and cannot be empty"
        )
    
    # Get filename and validate extension
    filename = file.filename or "unknown"
    ext = _detect_extension(filename)
    
    if ext in UNSUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format '{ext}' not supported yet. Supported formats: {list(SUPPORTED_EXTENSIONS)}"
        )
    
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: {list(SUPPORTED_EXTENSIONS)}"
        )
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())[:8]
    upload_time = datetime.utcnow().isoformat()
    file_path = UPLOAD_DIR / f"{file_id}_{filename}"
    
    try:
        # Use shutil.copyfileobj for safe streaming copy
        print(f"[UPLOAD] Saving {filename} to {file_path}")
        with open(file_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"[UPLOAD] Saved {filename} successfully")
        
    except Exception as e:
        error_msg = f"File save failed: {type(e).__name__}: {str(e)}"
        print(f"[UPLOAD ERROR] {error_msg}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)
    
    finally:
        # CRITICAL: Release Windows file lock
        try:
            file.file.close()
            print(f"[UPLOAD] File handle closed for {filename}")
        except Exception:
            pass

    # =====================================================================
    # PHASE 8: THE BOUNCER - Pre-Validation (reject UNKNOWN early)
    # =====================================================================
    try:
        columns = _peek_columns(file_path, ext)
        brain = get_brain()
        classification = brain.classify_file(columns, filename)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to parse file for schema validation: {type(e).__name__}: {str(e)}"
        )

    if not classification.get("valid") or classification.get("data_type") == "UNKNOWN":
        # Clean up rejected file
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(
            status_code=400,
            detail=f"File rejected: {classification.get('reason', 'Unknown or invalid schema')}"
        )
    
    # Initialize status tracking AFTER file is safely saved
    _file_status[file_id] = {
        "file_id": file_id,
        "filename": filename,
        "status": "queued",
        "ai_detection": None,
        "rows_processed": 0,
        "events_mapped": 0,
        "upload_time": upload_time,
        "completed_time": None,
        "error": None,
        "tenant_id": tenant_id
    }
    
    # Queue background processing AFTER file is closed
    background_tasks.add_task(
        _process_file_background,
        file_id,
        file_path,
        filename,
        tenant_id
    )
    
    print(f"[UPLOAD] Queued background task for {filename} (ID: {file_id})")
    
    return AsyncUploadResponse(
        status="queued",
        file_id=file_id,
        filename=filename,
        message="File uploaded. Processing in background."
    )


@router.get("/status", response_model=List[FileStatusResponse])
async def get_ingest_status(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID", description="Tenant identifier"),
    limit: int = Query(default=20, ge=1, le=100, description="Max files to return")
):
    """
    Get status of recent file uploads for this tenant.
    
    Returns list of files with their processing status:
    - queued: Waiting to be processed
    - processing: Currently being analyzed
    - completed: Successfully processed and indexed
    - failed: Processing failed (check error field)
    """
    tenant_id = x_tenant_id.strip()
    
    # Filter by tenant and sort by upload time (newest first)
    tenant_files = [
        FileStatusResponse(**{k: v for k, v in data.items() if k != "tenant_id"})
        for fid, data in _file_status.items()
        if data.get("tenant_id") == tenant_id
    ]
    
    # Sort by upload_time descending
    tenant_files.sort(key=lambda x: x.upload_time, reverse=True)
    
    return tenant_files[:limit]


@router.get("/health")
async def ingest_health():
    """Health check for ingestion endpoint"""
    return {
        "status": "healthy",
        "service": "ingest",
        "supported_formats": list(SUPPORTED_EXTENSIONS),
        "upcoming_formats": list(UNSUPPORTED_EXTENSIONS)
    }
