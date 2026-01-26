"""
R2 Storage Upload Endpoint - Secure file uploads to Cloudflare R2
"""
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/upload", tags=["File Upload"])


class UploadResponse(BaseModel):
    success: bool
    filename: str
    r2_key: str
    size_bytes: int
    uploaded_at: str


@router.post("/r2", response_model=UploadResponse)
async def upload_to_r2(
    file: UploadFile = File(...),
    org_id: str = Form(...),
    location_id: str = Form(...),
):
    """
    Upload files securely to Cloudflare R2 storage
    
    CRITICAL: Files are stored in R2, NOT in the database.
    This prevents database bloat and ensures scalability.
    """
    try:
        from backend.adapters.storage_adapter import StorageAdapter
        
        # Validate file type
        allowed_extensions = {".xlsx", ".xls", ".csv", ".pdf", ".json"}
        filename = file.filename or "unknown"
        ext = os.path.splitext(filename)[1].lower()
        
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {ext} not allowed. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        
        if len(content) > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=400, detail="File too large (max 50MB)")
        
        # Generate R2 key with tenant isolation
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        r2_key = f"{org_id}/{location_id}/uploads/{timestamp}_{filename}"
        
        # Upload to R2
        storage = StorageAdapter()
        success = storage.upload(r2_key, content)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to upload to R2 storage")
        
        # Log upload to BigQuery for audit trail
        try:
            from google.cloud import bigquery
            from pillars.config_vault import EffectiveSettings
            
            cfg = EffectiveSettings()
            key_file = getattr(cfg, "KEY_FILE", "service-key.json")
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
            
            if os.path.exists(key_path):
                client = bigquery.Client.from_service_account_json(key_path)
                
                # Insert audit log
                log_entry = {
                    "org_id": org_id,
                    "location_id": location_id,
                    "r2_key": r2_key,
                    "filename": filename,
                    "size_bytes": len(content),
                    "uploaded_at": datetime.utcnow().isoformat(),
                    "file_type": ext,
                }
                
                table_id = f"{cfg.PROJECT_ID}.{cfg.DATASET_ID}.file_upload_audit"
                errors = client.insert_rows_json(table_id, [log_entry])
                
                if not errors:
                    pass  # Audit logged successfully
        except:
            pass  # Audit is optional, don't fail the upload
        
        return UploadResponse(
            success=True,
            filename=filename,
            r2_key=r2_key,
            size_bytes=len(content),
            uploaded_at=datetime.utcnow().isoformat(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
