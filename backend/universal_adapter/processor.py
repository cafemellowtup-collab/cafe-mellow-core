"""
Background Processor - The Worker That Never Sleeps
===================================================
Processes raw_logs queue one by one.

CORE PRINCIPLE: Process data asynchronously, don't block the API.

Process:
1. Fetch pending raw_logs entries
2. For each entry:
   a. Parse raw_payload
   b. Determine target schema
   c. Use Refinery to transform
   d. Use Guard to validate and write
3. Update status (completed/quarantined)
4. Repeat

Can be run as:
- Background thread in FastAPI
- Standalone cron job
- Cloud Function trigger
"""

import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
import asyncio

from .refinery import (
    transform_data, transform_petpooja_order,
    TransformResult
)
from .guard import (
    quarantine_record, write_to_main_db
)


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


# =============================================================================
# Process Single Record
# =============================================================================

def process_single_record(log_id: str) -> Dict[str, Any]:
    """
    Process a single raw_log entry.
    Returns processing result with status.
    """
    client, cfg = _get_bq_client()
    if not client:
        return {"ok": False, "error": "BigQuery not available", "log_id": log_id}
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        raw_logs_table = f"{project_id}.{dataset_id}.raw_logs"
        
        # Fetch the record
        query = f"""
        SELECT log_id, source_type, source_identifier, raw_payload, target_schema, status
        FROM `{raw_logs_table}`
        WHERE log_id = '{log_id}'
        """
        result = list(client.query(query).result())
        
        if not result:
            return {"ok": False, "error": "Record not found", "log_id": log_id}
        
        row = result[0]
        
        if row.status not in ("pending", "failed"):
            return {"ok": False, "error": f"Record already {row.status}", "log_id": log_id}
        
        # Mark as processing
        update_sql = f"""
        UPDATE `{raw_logs_table}`
        SET status = 'processing'
        WHERE log_id = '{log_id}'
        """
        client.query(update_sql).result()
        
        # Parse raw payload
        try:
            raw_data = json.loads(row.raw_payload)
        except json.JSONDecodeError as e:
            _mark_failed(client, raw_logs_table, log_id, f"Invalid JSON: {e}")
            return {"ok": False, "error": "Invalid JSON payload", "log_id": log_id}
        
        # Handle batch records (from file uploads)
        if "records" in raw_data and isinstance(raw_data.get("records"), list):
            return _process_batch_records(
                client, cfg, log_id, raw_data["records"],
                row.source_type, row.source_identifier, row.target_schema
            )
        
        # Single record processing
        source_type = row.source_type or "unknown"
        source_identifier = row.source_identifier or source_type
        target_schema = row.target_schema or "unknown"
        
        # Use optimized Petpooja transformer if applicable
        if source_type == "petpooja" and target_schema == "order":
            result_status, validated, errors = transform_petpooja_order(raw_data)
        else:
            result_status, validated, errors = transform_data(raw_data, target_schema, source_identifier)
        
        # Handle result
        if result_status == TransformResult.SUCCESS and validated:
            # Write to main DB (with event ledger tracking)
            success, write_error = write_to_main_db(
                validated, 
                target_schema,
                raw_log_id=log_id,
                source_system=source_type
            )
            
            if success:
                _mark_completed(client, raw_logs_table, log_id)
                return {
                    "ok": True,
                    "log_id": log_id,
                    "status": "completed",
                    "target_schema": target_schema
                }
            else:
                # Write failed - quarantine
                quar_id = quarantine_record(
                    log_id, target_schema, [write_error or "Write failed"],
                    validated.model_dump() if hasattr(validated, 'model_dump') else None
                )
                return {
                    "ok": False,
                    "log_id": log_id,
                    "status": "quarantined",
                    "quarantine_id": quar_id,
                    "errors": [write_error]
                }
        else:
            # Validation/Transform failed - quarantine
            quar_id = quarantine_record(
                log_id, target_schema, errors,
                validated.model_dump() if validated and hasattr(validated, 'model_dump') else None
            )
            return {
                "ok": False,
                "log_id": log_id,
                "status": "quarantined",
                "quarantine_id": quar_id,
                "errors": errors
            }
            
    except Exception as e:
        if client:
            try:
                project_id = getattr(cfg, "PROJECT_ID", "")
                dataset_id = getattr(cfg, "DATASET_ID", "")
                raw_logs_table = f"{project_id}.{dataset_id}.raw_logs"
                _mark_failed(client, raw_logs_table, log_id, str(e))
            except:
                pass
        return {"ok": False, "error": str(e), "log_id": log_id}


def _process_batch_records(
    client, cfg, parent_log_id: str, records: List[Dict],
    source_type: str, source_identifier: str, target_schema: str
) -> Dict[str, Any]:
    """Process batch of records from file upload"""
    project_id = getattr(cfg, "PROJECT_ID", "")
    dataset_id = getattr(cfg, "DATASET_ID", "")
    raw_logs_table = f"{project_id}.{dataset_id}.raw_logs"
    
    results = {
        "ok": True,
        "log_id": parent_log_id,
        "total": len(records),
        "success": 0,
        "failed": 0,
        "quarantined": 0,
        "errors": []
    }
    
    for i, record in enumerate(records):
        try:
            result_status, validated, errors = transform_data(record, target_schema, source_identifier)
            
            if result_status == TransformResult.SUCCESS and validated:
                success, write_error = write_to_main_db(
                    validated, target_schema,
                    raw_log_id=f"{parent_log_id}_row{i}",
                    source_system=source_type
                )
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Record {i}: {write_error}")
            else:
                results["quarantined"] += 1
                # Create individual quarantine for batch failures
                quarantine_record(
                    f"{parent_log_id}_row{i}", target_schema, errors,
                    validated.model_dump() if validated and hasattr(validated, 'model_dump') else record
                )
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Record {i}: {str(e)}")
    
    # Mark parent log based on results
    if results["success"] == results["total"]:
        _mark_completed(client, raw_logs_table, parent_log_id)
        results["status"] = "completed"
    elif results["success"] > 0:
        _mark_completed(client, raw_logs_table, parent_log_id)
        results["status"] = "partial"
    else:
        _mark_failed(client, raw_logs_table, parent_log_id, f"All {results['total']} records failed")
        results["status"] = "failed"
        results["ok"] = False
    
    return results


def _mark_completed(client, table_id: str, log_id: str):
    """Mark a raw_log as completed"""
    update_sql = f"""
    UPDATE `{table_id}`
    SET status = 'completed', processed_at = CURRENT_TIMESTAMP()
    WHERE log_id = '{log_id}'
    """
    client.query(update_sql).result()


def _mark_failed(client, table_id: str, log_id: str, error_message: str):
    """Mark a raw_log as failed"""
    error_safe = error_message[:500].replace("'", "''")
    update_sql = f"""
    UPDATE `{table_id}`
    SET status = 'failed', 
        error_message = '{error_safe}',
        retry_count = retry_count + 1
    WHERE log_id = '{log_id}'
    """
    client.query(update_sql).result()


# =============================================================================
# Batch Processing
# =============================================================================

def process_pending_batch(limit: int = 10) -> Dict[str, Any]:
    """
    Process a batch of pending raw_logs.
    Returns summary of processing results.
    """
    client, cfg = _get_bq_client()
    if not client:
        return {"ok": False, "error": "BigQuery not available"}
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        raw_logs_table = f"{project_id}.{dataset_id}.raw_logs"
        
        # Get pending records
        query = f"""
        SELECT log_id
        FROM `{raw_logs_table}`
        WHERE status = 'pending'
        ORDER BY received_at ASC
        LIMIT {limit}
        """
        result = list(client.query(query).result())
        
        if not result:
            return {"ok": True, "message": "No pending records", "processed": 0}
        
        results = {
            "ok": True,
            "processed": 0,
            "success": 0,
            "failed": 0,
            "quarantined": 0,
            "details": []
        }
        
        for row in result:
            process_result = process_single_record(row.log_id)
            results["processed"] += 1
            
            if process_result.get("ok"):
                results["success"] += 1
            elif process_result.get("status") == "quarantined":
                results["quarantined"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append(process_result)
        
        return results
        
    except Exception as e:
        return {"ok": False, "error": str(e)}


def process_failed_batch(limit: int = 5, max_retries: int = 3) -> Dict[str, Any]:
    """
    Retry failed records (up to max_retries).
    """
    client, cfg = _get_bq_client()
    if not client:
        return {"ok": False, "error": "BigQuery not available"}
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        raw_logs_table = f"{project_id}.{dataset_id}.raw_logs"
        
        # Get failed records with retry count < max
        query = f"""
        SELECT log_id
        FROM `{raw_logs_table}`
        WHERE status = 'failed' AND retry_count < {max_retries}
        ORDER BY received_at ASC
        LIMIT {limit}
        """
        result = list(client.query(query).result())
        
        if not result:
            return {"ok": True, "message": "No retryable records", "retried": 0}
        
        # Reset status to pending for retry
        for row in result:
            reset_sql = f"""
            UPDATE `{raw_logs_table}`
            SET status = 'pending'
            WHERE log_id = '{row.log_id}'
            """
            client.query(reset_sql).result()
        
        # Process them
        return process_pending_batch(len(result))
        
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =============================================================================
# Continuous Processing (Background Worker)
# =============================================================================

class BackgroundProcessor:
    """
    Continuous background processor that runs in a separate thread.
    """
    
    def __init__(self, batch_size: int = 10, sleep_interval: int = 5):
        self.batch_size = batch_size
        self.sleep_interval = sleep_interval
        self.running = False
        self._stats = {
            "started_at": None,
            "total_processed": 0,
            "total_success": 0,
            "total_failed": 0,
            "total_quarantined": 0,
            "last_run_at": None
        }
    
    def start(self):
        """Start the background processor"""
        if self.running:
            return
        
        self.running = True
        self._stats["started_at"] = datetime.utcnow().isoformat()
        print("🚀 Background Processor started")
        
        while self.running:
            try:
                result = process_pending_batch(self.batch_size)
                
                if result.get("ok") and result.get("processed", 0) > 0:
                    self._stats["total_processed"] += result.get("processed", 0)
                    self._stats["total_success"] += result.get("success", 0)
                    self._stats["total_failed"] += result.get("failed", 0)
                    self._stats["total_quarantined"] += result.get("quarantined", 0)
                    self._stats["last_run_at"] = datetime.utcnow().isoformat()
                    
                    print(f"✅ Processed {result['processed']} records: "
                          f"{result['success']} success, {result['quarantined']} quarantined, {result['failed']} failed")
                
                time.sleep(self.sleep_interval)
                
            except Exception as e:
                print(f"❌ Processor error: {e}")
                time.sleep(self.sleep_interval * 2)  # Back off on error
    
    def stop(self):
        """Stop the background processor"""
        self.running = False
        print("🛑 Background Processor stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            **self._stats,
            "running": self.running
        }


# Global processor instance
_processor: Optional[BackgroundProcessor] = None


def get_processor() -> BackgroundProcessor:
    """Get or create the global processor instance"""
    global _processor
    if _processor is None:
        _processor = BackgroundProcessor()
    return _processor


def start_background_processing():
    """Start background processing in a thread"""
    import threading
    
    processor = get_processor()
    if processor.running:
        return {"ok": False, "message": "Processor already running"}
    
    thread = threading.Thread(target=processor.start, daemon=True)
    thread.start()
    
    return {"ok": True, "message": "Background processor started"}


def stop_background_processing():
    """Stop background processing"""
    processor = get_processor()
    processor.stop()
    return {"ok": True, "message": "Background processor stopped"}


def get_processor_stats() -> Dict[str, Any]:
    """Get processor statistics"""
    processor = get_processor()
    return processor.get_stats()


# =============================================================================
# Async Processing (for FastAPI)
# =============================================================================

async def process_pending_async(limit: int = 10) -> Dict[str, Any]:
    """Async version of process_pending_batch for FastAPI"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, process_pending_batch, limit)


async def process_single_async(log_id: str) -> Dict[str, Any]:
    """Async version of process_single_record"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, process_single_record, log_id)
