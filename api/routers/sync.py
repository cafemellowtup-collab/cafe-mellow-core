"""
Sync Router - Manual Data Synchronization with Status Tracking
Provides manual sync buttons for UI with real-time progress
"""
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import subprocess
import sys
import os

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])

# Track sync status in memory (in production, use Redis or database)
_sync_status: Dict[str, Dict[str, Any]] = {}


class SyncResponse(BaseModel):
    ok: bool
    sync_type: str
    status: str  # "queued", "running", "completed", "failed"
    message: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


def _get_project_root():
    """Get absolute path to project root"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


def _run_sync_script(sync_type: str, script_path: str):
    """Execute sync script and update status"""
    global _sync_status
    
    try:
        _sync_status[sync_type]["status"] = "running"
        _sync_status[sync_type]["started_at"] = datetime.now().isoformat()
        
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=_get_project_root(),
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            _sync_status[sync_type]["status"] = "completed"
            _sync_status[sync_type]["message"] = f"{sync_type} sync completed successfully"
            _sync_status[sync_type]["completed_at"] = datetime.now().isoformat()
        else:
            _sync_status[sync_type]["status"] = "failed"
            _sync_status[sync_type]["error"] = result.stderr or "Unknown error"
            _sync_status[sync_type]["completed_at"] = datetime.now().isoformat()
    
    except subprocess.TimeoutExpired:
        _sync_status[sync_type]["status"] = "failed"
        _sync_status[sync_type]["error"] = "Sync timeout (exceeded 5 minutes)"
        _sync_status[sync_type]["completed_at"] = datetime.now().isoformat()
    
    except Exception as e:
        _sync_status[sync_type]["status"] = "failed"
        _sync_status[sync_type]["error"] = str(e)
        _sync_status[sync_type]["completed_at"] = datetime.now().isoformat()


@router.post("/sales")
def sync_sales(background_tasks: BackgroundTasks) -> SyncResponse:
    """
    Sync sales data from Petpooja POS
    Runs: 01_Data_Sync/sync_sales_raw.py + titan_sales_parser.py
    """
    sync_type = "sales"
    project_root = _get_project_root()
    
    # Initialize status
    _sync_status[sync_type] = {
        "status": "queued",
        "message": "Sales sync queued",
        "started_at": None,
        "completed_at": None,
        "error": None
    }
    
    # Queue both scripts
    raw_script = os.path.join(project_root, "01_Data_Sync", "sync_sales_raw.py")
    parser_script = os.path.join(project_root, "01_Data_Sync", "titan_sales_parser.py")
    
    def _sync_sales_chain():
        # First sync raw data
        _run_sync_script("sales_raw", raw_script)
        
        # Then parse if raw succeeded
        if _sync_status.get("sales_raw", {}).get("status") == "completed":
            _run_sync_script(sync_type, parser_script)
        else:
            _sync_status[sync_type]["status"] = "failed"
            _sync_status[sync_type]["error"] = "Raw sales sync failed"
    
    background_tasks.add_task(_sync_sales_chain)
    
    return SyncResponse(
        ok=True,
        sync_type=sync_type,
        status="queued",
        message="Sales sync started in background"
    )


@router.post("/expenses")
def sync_expenses(background_tasks: BackgroundTasks) -> SyncResponse:
    """
    Sync expense data from Google Drive
    Runs: 01_Data_Sync/sync_expenses.py
    """
    sync_type = "expenses"
    project_root = _get_project_root()
    script_path = os.path.join(project_root, "01_Data_Sync", "sync_expenses.py")
    
    _sync_status[sync_type] = {
        "status": "queued",
        "message": "Expenses sync queued",
        "started_at": None,
        "completed_at": None,
        "error": None
    }
    
    background_tasks.add_task(_run_sync_script, sync_type, script_path)
    
    return SyncResponse(
        ok=True,
        sync_type=sync_type,
        status="queued",
        message="Expenses sync started in background"
    )


@router.post("/recipes")
def sync_recipes(background_tasks: BackgroundTasks) -> SyncResponse:
    """
    Sync recipe/BOM data from Google Drive
    Runs: 01_Data_Sync/sync_recipes.py
    """
    sync_type = "recipes"
    project_root = _get_project_root()
    script_path = os.path.join(project_root, "01_Data_Sync", "sync_recipes.py")
    
    _sync_status[sync_type] = {
        "status": "queued",
        "message": "Recipes sync queued",
        "started_at": None,
        "completed_at": None,
        "error": None
    }
    
    background_tasks.add_task(_run_sync_script, sync_type, script_path)
    
    return SyncResponse(
        ok=True,
        sync_type=sync_type,
        status="queued",
        message="Recipes sync started in background"
    )


@router.post("/purchases")
def sync_purchases(background_tasks: BackgroundTasks) -> SyncResponse:
    """
    Sync purchase data from Google Drive
    Runs: 01_Data_Sync/sync_purchases.py
    """
    sync_type = "purchases"
    project_root = _get_project_root()
    script_path = os.path.join(project_root, "01_Data_Sync", "sync_purchases.py")
    
    _sync_status[sync_type] = {
        "status": "queued",
        "message": "Purchases sync queued",
        "started_at": None,
        "completed_at": None,
        "error": None
    }
    
    background_tasks.add_task(_run_sync_script, sync_type, script_path)
    
    return SyncResponse(
        ok=True,
        sync_type=sync_type,
        status="queued",
        message="Purchases sync started in background"
    )


@router.post("/wastage")
def sync_wastage(background_tasks: BackgroundTasks) -> SyncResponse:
    """
    Sync wastage logs from Google Drive
    Runs: 01_Data_Sync/sync_wastage.py
    """
    sync_type = "wastage"
    project_root = _get_project_root()
    script_path = os.path.join(project_root, "01_Data_Sync", "sync_wastage.py")
    
    _sync_status[sync_type] = {
        "status": "queued",
        "message": "Wastage sync queued",
        "started_at": None,
        "completed_at": None,
        "error": None
    }
    
    background_tasks.add_task(_run_sync_script, sync_type, script_path)
    
    return SyncResponse(
        ok=True,
        sync_type=sync_type,
        status="queued",
        message="Wastage sync started in background"
    )


@router.post("/all")
def sync_all(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Master sync: Run all data syncs sequentially
    """
    project_root = _get_project_root()
    
    def _sync_all_chain():
        # Define sync order for data dependencies
        sync_order = [
            ("sales", ["01_Data_Sync/sync_sales_raw.py", "01_Data_Sync/titan_sales_parser.py"]),
            ("expenses", ["01_Data_Sync/sync_expenses.py"]),
            ("recipes", ["01_Data_Sync/sync_recipes.py"]),
            ("purchases", ["01_Data_Sync/sync_purchases.py"]),
            ("wastage", ["01_Data_Sync/sync_wastage.py"]),
        ]
        
        for sync_type, scripts in sync_order:
            for script_name in scripts:
                script_path = os.path.join(project_root, script_name)
                if os.path.exists(script_path):
                    _run_sync_script(f"{sync_type}_{os.path.basename(script_name)}", script_path)
    
    background_tasks.add_task(_sync_all_chain)
    
    return {
        "ok": True,
        "message": "Master sync started. All data sources will be synchronized sequentially.",
        "sync_types": ["sales", "expenses", "recipes", "purchases", "wastage"]
    }


@router.get("/status/{sync_type}")
def get_sync_status(sync_type: str) -> SyncResponse:
    """
    Get current status of a sync job
    """
    status_data = _sync_status.get(sync_type)
    
    if not status_data:
        return SyncResponse(
            ok=True,
            sync_type=sync_type,
            status="unknown",
            message=f"No sync history for {sync_type}"
        )
    
    return SyncResponse(
        ok=True,
        sync_type=sync_type,
        status=status_data.get("status", "unknown"),
        message=status_data.get("message", ""),
        started_at=status_data.get("started_at"),
        completed_at=status_data.get("completed_at"),
        error=status_data.get("error")
    )


@router.get("/status")
def get_all_sync_status() -> Dict[str, Any]:
    """
    Get status of all sync jobs
    """
    return {
        "ok": True,
        "syncs": _sync_status,
        "available_syncs": ["sales", "expenses", "recipes", "purchases", "wastage"]
    }
