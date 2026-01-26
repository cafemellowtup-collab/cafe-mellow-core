"""
Folder Watcher: Automated hourly monitoring of Google Drive folders for new data files
Automatically ingests, archives successful files, and quarantines failed files
"""
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from pillars.config_vault import EffectiveSettings
from utils.universal_ingester import UniversalIngester
from utils.db_lock_manager import SyncLockContext
from google.cloud import bigquery


def get_folder_mappings():
    """
    Get folder mappings from EffectiveSettings (UI-configured).
    Uses Titan_Archived and Titan_Failed folder convention.
    """
    try:
        cfg = EffectiveSettings()
        return [
            {
                "folder_id": getattr(cfg, "FOLDER_ID_EXPENSES", "") or os.getenv("FOLDER_ID_EXPENSES", ""),
                "master_category": "expenses",
                "sub_tag": "titan_auto_ingested",
                "archive_folder_id": os.getenv("TITAN_ARCHIVED_EXPENSES", ""),
                "failed_folder_id": os.getenv("TITAN_FAILED_EXPENSES", ""),
                "enabled": True
            },
            {
                "folder_id": getattr(cfg, "FOLDER_ID_PURCHASES", "") or os.getenv("FOLDER_ID_PURCHASES", ""),
                "master_category": "purchases",
                "sub_tag": "titan_auto_ingested",
                "archive_folder_id": os.getenv("TITAN_ARCHIVED_PURCHASES", ""),
                "failed_folder_id": os.getenv("TITAN_FAILED_PURCHASES", ""),
                "enabled": True
            },
            {
                "folder_id": getattr(cfg, "FOLDER_ID_INVENTORY", "") or os.getenv("FOLDER_ID_INVENTORY", ""),
                "master_category": "inventory",
                "sub_tag": "titan_auto_ingested",
                "archive_folder_id": os.getenv("TITAN_ARCHIVED_INVENTORY", ""),
                "failed_folder_id": os.getenv("TITAN_FAILED_INVENTORY", ""),
                "enabled": True
            },
            {
                "folder_id": getattr(cfg, "FOLDER_ID_RECIPES", "") or os.getenv("FOLDER_ID_RECIPES", ""),
                "master_category": "recipes",
                "sub_tag": "titan_auto_ingested",
                "archive_folder_id": os.getenv("TITAN_ARCHIVED_RECIPES", ""),
                "failed_folder_id": os.getenv("TITAN_FAILED_RECIPES", ""),
                "enabled": True
            },
            {
                "folder_id": getattr(cfg, "FOLDER_ID_WASTAGE", "") or os.getenv("FOLDER_ID_WASTAGE", ""),
                "master_category": "wastage",
                "sub_tag": "titan_auto_ingested",
                "archive_folder_id": os.getenv("TITAN_ARCHIVED_WASTAGE", ""),
                "failed_folder_id": os.getenv("TITAN_FAILED_WASTAGE", ""),
                "enabled": True
            },
        ]
    except Exception as e:
        print(f"⚠️ Error loading folder mappings from config: {e}")
        return []


def get_bq_client():
    """Initialize BigQuery client"""
    try:
        cfg = EffectiveSettings()
        key_file = getattr(cfg, "KEY_FILE", "service-key.json")
        key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
        
        if not os.path.exists(key_path):
            print(f"❌ Service key not found: {key_path}")
            return None
        
        return bigquery.Client.from_service_account_json(key_path)
    except Exception as e:
        print(f"❌ Failed to initialize BigQuery client: {e}")
        return None


def log_watcher_run(client: bigquery.Client, settings, results: Dict[str, Any]):
    """Log watcher run to BigQuery for monitoring"""
    try:
        project_id = getattr(settings, "PROJECT_ID", "")
        dataset_id = getattr(settings, "DATASET_ID", "")
        table_id = f"{project_id}.{dataset_id}.folder_watcher_log"
        
        # Create table if not exists
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS `{table_id}` (
            run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
            folders_processed INT64,
            files_total INT64,
            files_success INT64,
            files_failed INT64,
            duration_seconds FLOAT64,
            status STRING,
            error_message STRING
        )
        PARTITION BY DATE(run_timestamp)
        """
        client.query(create_sql).result()
        
        # Insert log
        insert_sql = f"""
        INSERT INTO `{table_id}`
        (run_timestamp, folders_processed, files_total, files_success, files_failed, duration_seconds, status, error_message)
        VALUES (
            CURRENT_TIMESTAMP(),
            {results.get('folders_processed', 0)},
            {results.get('files_total', 0)},
            {results.get('files_success', 0)},
            {results.get('files_failed', 0)},
            {results.get('duration_seconds', 0)},
            '{results.get('status', 'unknown')}',
            '{results.get('error_message', '').replace("'", "''")}'
        )
        """
        client.query(insert_sql).result()
        
    except Exception as e:
        print(f"⚠️ Failed to log watcher run: {e}")


def send_notification(results: Dict[str, Any]):
    """Send notification about watcher run (can be extended to email/Slack)"""
    status = results.get('status', 'unknown')
    
    if status == 'success':
        print(f"\n✅ Folder Watcher: {results.get('files_success', 0)} files processed successfully")
        if results.get('files_failed', 0) > 0:
            print(f"⚠️ {results.get('files_failed', 0)} files failed - check quarantine folder")
    else:
        print(f"\n❌ Folder Watcher failed: {results.get('error_message', 'Unknown error')}")


def watch_folders():
    """
    Main folder watcher function.
    Monitors configured folders and auto-ingests new files.
    """
    print(f"\n{'='*60}")
    print(f"🔍 TITAN Folder Watcher - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    start_time = datetime.now()
    results = {
        "folders_processed": 0,
        "files_total": 0,
        "files_success": 0,
        "files_failed": 0,
        "duration_seconds": 0,
        "status": "running",
        "error_message": ""
    }
    
    # Initialize
    cfg = EffectiveSettings()
    client = get_bq_client()
    
    if not client:
        results["status"] = "failed"
        results["error_message"] = "BigQuery client initialization failed"
        send_notification(results)
        return results
    
    try:
        ingester = UniversalIngester(cfg, client)
        
        # Process each configured folder (from UI settings)
        folder_mappings = get_folder_mappings()
        for folder_config in folder_mappings:
            if not folder_config.get("enabled", True):
                continue
            
            folder_id = folder_config.get("folder_id", "").strip()
            if not folder_id:
                print(f"⏭️ Skipping {folder_config.get('master_category')} - no folder_id configured")
                continue
            
            category = folder_config.get("master_category")
            lock_name = f"folder_watch_{category}"
            
            print(f"\n📁 Processing: {category.upper()}")
            print(f"   Folder ID: {folder_id}")
            
            # Use database lock to prevent simultaneous processing
            with SyncLockContext(client, cfg, lock_name) as lock:
                if not lock.acquired:
                    print(f"   ⏸️ Skipped - another process is already ingesting {category}")
                    continue
                
                try:
                    folder_results = ingester.ingest_from_folder(
                        folder_id=folder_id,
                        master_category=category,
                        sub_tag=folder_config.get("sub_tag"),
                        archive_folder_id=folder_config.get("archive_folder_id"),
                        failed_folder_id=folder_config.get("failed_folder_id")
                    )
                    
                    results["folders_processed"] += 1
                    results["files_total"] += folder_results.get("total", 0)
                    results["files_success"] += folder_results.get("success", 0)
                    results["files_failed"] += folder_results.get("failed", 0)
                    
                    print(f"   ✅ Total: {folder_results.get('total', 0)} | Success: {folder_results.get('success', 0)} | Failed: {folder_results.get('failed', 0)}")
                    
                    # Log failed files
                    if folder_results.get("failed", 0) > 0:
                        print(f"   ⚠️ Failed files:")
                        for file_info in folder_results.get("files", []):
                            if file_info.get("status") == "failed":
                                print(f"      - {file_info.get('name')}: {file_info.get('error', 'Unknown error')}")
                    
                except Exception as e:
                    print(f"   ❌ Error processing folder: {e}")
                    results["error_message"] += f"{category}: {str(e)}; "
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        results["duration_seconds"] = duration
        
        # Determine final status
        if results["files_failed"] == 0 and results["files_total"] > 0:
            results["status"] = "success"
        elif results["files_failed"] > 0:
            results["status"] = "partial_success"
        elif results["files_total"] == 0:
            results["status"] = "no_files"
        else:
            results["status"] = "success"
        
        # Log to BigQuery
        log_watcher_run(client, cfg, results)
        
        # Send notification
        send_notification(results)
        
        print(f"\n{'='*60}")
        print(f"⏱️ Duration: {duration:.2f} seconds")
        print(f"{'='*60}\n")
        
        return results
        
    except Exception as e:
        results["status"] = "failed"
        results["error_message"] = str(e)
        results["duration_seconds"] = (datetime.now() - start_time).total_seconds()
        
        print(f"\n❌ Critical error: {e}")
        
        # Try to log error
        try:
            log_watcher_run(client, cfg, results)
        except:
            pass
        
        send_notification(results)
        return results


def setup_instructions():
    """Print setup instructions for folder watcher"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║           TITAN FOLDER WATCHER - SETUP INSTRUCTIONS            ║
╚════════════════════════════════════════════════════════════════╝

1. GET SERVICE ACCOUNT EMAIL:
   Run: GET /api/v1/ingester/service-account
   Copy the service account email.

2. SHARE DRIVE FOLDERS:
   - Create folders: "Expenses_Watch", "Expenses_Archive", "Expenses_Failed"
   - Share ALL folders with the service account email (Viewer access)
   - Get Folder IDs from URLs

3. CONFIGURE ENVIRONMENT VARIABLES:
   Add to .env file:
   
   # Watch folders (where new files are uploaded)
   WATCH_FOLDER_EXPENSES=<folder_id>
   WATCH_FOLDER_PURCHASES=<folder_id>
   WATCH_FOLDER_INVENTORY=<folder_id>
   
   # Archive folders (successful files moved here)
   ARCHIVE_FOLDER_EXPENSES=<folder_id>
   ARCHIVE_FOLDER_PURCHASES=<folder_id>
   ARCHIVE_FOLDER_INVENTORY=<folder_id>
   
   # Failed folders (failed files moved here for review)
   FAILED_FOLDER_EXPENSES=<folder_id>
   FAILED_FOLDER_PURCHASES=<folder_id>
   FAILED_FOLDER_INVENTORY=<folder_id>

4. TEST MANUALLY:
   python scheduler/folder_watcher.py

5. SETUP CRON (Hourly):
   Windows Task Scheduler:
   - Trigger: Daily, repeat every 1 hour
   - Action: python C:\\path\\to\\scheduler\\folder_watcher.py
   
   Linux/Mac Crontab:
   0 * * * * cd /path/to/project && python scheduler/folder_watcher.py

6. MONITOR:
   Check BigQuery table: folder_watcher_log
   
╚════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="TITAN Folder Watcher")
    parser.add_argument("--setup", action="store_true", help="Show setup instructions")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_instructions()
    else:
        results = watch_folders()
        
        # Exit with appropriate code
        if results.get("status") in ["success", "no_files"]:
            sys.exit(0)
        elif results.get("status") == "partial_success":
            sys.exit(1)
        else:
            sys.exit(2)
