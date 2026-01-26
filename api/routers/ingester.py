"""
Universal Ingester API Router
Provides endpoints for AI-powered multi-modal data ingestion
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pillars.config_vault import EffectiveSettings
from utils.universal_ingester import UniversalIngester

router = APIRouter(prefix="/api/v1/ingester", tags=["ingester"])


class FolderMappingRequest(BaseModel):
    folder_id: str
    master_category: str
    sub_tag: Optional[str] = None
    archive_folder_id: Optional[str] = None
    failed_folder_id: Optional[str] = None


class IngestResponse(BaseModel):
    ok: bool
    message: str
    job_id: Optional[str] = None
    total: int = 0
    success: int = 0
    failed: int = 0
    files: List[Dict[str, Any]] = []


# In-memory job status (in production, use Redis)
_ingestion_jobs: Dict[str, Dict[str, Any]] = {}


def _get_bq_client():
    try:
        from google.cloud import bigquery
        import os
        
        cfg = EffectiveSettings()
        key_file = getattr(cfg, "KEY_FILE", "service-key.json")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
        
        if not os.path.exists(key_path):
            return None
        return bigquery.Client.from_service_account_json(key_path)
    except Exception:
        return None


@router.get("/service-account")
def get_service_account_email() -> Dict[str, Any]:
    """
    Get the service account email for Google Drive folder sharing.
    Users must share their Drive folders with this email.
    """
    try:
        cfg = EffectiveSettings()
        client = _get_bq_client()
        
        if not client:
            raise HTTPException(
                status_code=400,
                detail="BigQuery not connected. Check service-key.json"
            )
        
        ingester = UniversalIngester(cfg, client)
        email = ingester.get_service_account_email()
        
        return {
            "ok": True,
            "service_account_email": email,
            "instructions": [
                "1. Open your Google Drive folder containing data files",
                "2. Click 'Share' button",
                "3. Add this email with 'Viewer' permission",
                f"4. Share with: {email}",
                "5. Use the Folder ID from the URL in the ingestion API"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", response_model=IngestResponse)
def ingest_folder(req: FolderMappingRequest, background_tasks: BackgroundTasks) -> IngestResponse:
    """
    Ingest all files from a Google Drive folder.
    Supports: Excel, CSV, PDF, Images
    
    Files are processed with AI-powered schema mapping:
    - First 50 rows sent to LLM for intelligent column mapping
    - Rest parsed with Pandas using mapped schema
    - PDFs/Images processed with Gemini Vision
    
    Successfully processed files moved to archive_folder_id.
    Failed files moved to failed_folder_id.
    """
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(
            status_code=400,
            detail="BigQuery not connected. Check service-key.json"
        )
    
    # Generate job ID
    job_id = f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize job status
    _ingestion_jobs[job_id] = {
        "status": "queued",
        "started_at": datetime.now().isoformat(),
        "folder_id": req.folder_id,
        "category": req.master_category,
        "results": None
    }
    
    def _run_ingestion():
        try:
            _ingestion_jobs[job_id]["status"] = "running"
            
            ingester = UniversalIngester(cfg, client)
            results = ingester.ingest_from_folder(
                folder_id=req.folder_id,
                master_category=req.master_category,
                sub_tag=req.sub_tag,
                archive_folder_id=req.archive_folder_id,
                failed_folder_id=req.failed_folder_id
            )
            
            _ingestion_jobs[job_id]["status"] = "completed"
            _ingestion_jobs[job_id]["completed_at"] = datetime.now().isoformat()
            _ingestion_jobs[job_id]["results"] = results
            
        except Exception as e:
            _ingestion_jobs[job_id]["status"] = "failed"
            _ingestion_jobs[job_id]["error"] = str(e)
            _ingestion_jobs[job_id]["completed_at"] = datetime.now().isoformat()
    
    # Queue background task
    background_tasks.add_task(_run_ingestion)
    
    return IngestResponse(
        ok=True,
        message="Ingestion job started in background",
        job_id=job_id
    )


@router.get("/status/{job_id}", response_model=IngestResponse)
def get_ingestion_status(job_id: str) -> IngestResponse:
    """
    Get the status of an ingestion job.
    """
    job = _ingestion_jobs.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = job.get("status", "unknown")
    results = job.get("results", {})
    
    if status == "completed" and results:
        return IngestResponse(
            ok=True,
            message="Ingestion completed",
            job_id=job_id,
            total=results.get("total", 0),
            success=results.get("success", 0),
            failed=results.get("failed", 0),
            files=results.get("files", [])
        )
    elif status == "failed":
        return IngestResponse(
            ok=False,
            message=f"Ingestion failed: {job.get('error', 'Unknown error')}",
            job_id=job_id
        )
    else:
        return IngestResponse(
            ok=True,
            message=f"Job status: {status}",
            job_id=job_id
        )


@router.get("/jobs", response_model=Dict[str, Any])
def list_jobs() -> Dict[str, Any]:
    """
    List all ingestion jobs (last 50).
    """
    jobs_list = []
    for job_id, job_data in list(_ingestion_jobs.items())[-50:]:
        jobs_list.append({
            "job_id": job_id,
            "status": job_data.get("status"),
            "category": job_data.get("category"),
            "started_at": job_data.get("started_at"),
            "completed_at": job_data.get("completed_at")
        })
    
    return {
        "ok": True,
        "jobs": jobs_list,
        "total": len(jobs_list)
    }


@router.post("/test-connection")
def test_drive_connection(folder_id: str) -> Dict[str, Any]:
    """
    Test connection to a Google Drive folder.
    Verifies that the service account has access.
    """
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(
            status_code=400,
            detail="BigQuery not connected. Check service-key.json"
        )
    
    try:
        ingester = UniversalIngester(cfg, client)
        
        # Try to list files in folder
        response = ingester.drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, mimeType)",
            pageSize=5
        ).execute()
        
        files = response.get('files', [])
        
        return {
            "ok": True,
            "accessible": True,
            "folder_id": folder_id,
            "sample_files": [
                {"name": f['name'], "type": f['mimeType']} 
                for f in files
            ],
            "file_count": len(files),
            "message": "Connection successful! Service account has access to this folder."
        }
        
    except Exception as e:
        return {
            "ok": False,
            "accessible": False,
            "folder_id": folder_id,
            "error": str(e),
            "message": "Connection failed. Ensure the folder is shared with the service account email."
        }
