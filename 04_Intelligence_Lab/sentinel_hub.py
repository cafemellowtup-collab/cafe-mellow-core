import os
import importlib.util
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from datetime import datetime

# Fix Windows encoding issue
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Path Setup to reach settings.py in the root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from titan_integrity import DataIntegrityError, crash_report, append_crash_state

try:
    import settings
except ImportError:
    print("ERROR: Could not import settings.py. Make sure it exists in the root directory.")
    sys.exit(1)

def validate_connection():
    """Validate BigQuery connection"""
    try:
        client = bigquery.Client.from_service_account_json(settings.KEY_FILE)
        # Test connection
        client.get_dataset(f"{settings.PROJECT_ID}.{settings.DATASET_ID}")
        return True, client, None
    except NotFound as e:
        return False, None, f"Dataset or project not found: {e}"
    except Exception as e:
        return False, None, str(e)

# Validate connection
is_valid, client, error = validate_connection()
if not is_valid:
    print(f"ERROR: Connection validation failed: {error}")
    sys.exit(1)

def run_sentinel_hub():
    """Run Sentinel Hub with comprehensive error handling"""
    print(f"TITAN HUB: INITIATING MULTI-PILLAR SCAN | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("-" * 65)
    
    # Path to your pillars folder
    pillar_folder = os.path.join(os.path.dirname(__file__), "pillars")
    
    if not os.path.exists(pillar_folder):
        print(f"ERROR: Pillars folder not found: {pillar_folder}")
        return
    
    try:
        pillar_files = [f for f in os.listdir(pillar_folder) if f.endswith(".py") and f != "__init__.py"]
    except Exception as e:
        print(f"ERROR: Could not read pillars folder: {e}")
        return
    
    if not pillar_files:
        print("WARNING: No pillar files found.")
        return
    
    all_tasks = []
    successful_pillars = 0
    failed_pillars = 0
    
    # 1. DYNAMIC SCAN: Look for any .py file in the pillars folder
    for file in pillar_files:
        pillar_name = file[:-3]
        print(f"PLUGGING IN: {pillar_name.upper()}...")
        
        try:
            # Load the pillar dynamically
            file_path = os.path.join(pillar_folder, file)
            spec = importlib.util.spec_from_file_location(pillar_name, file_path)
            
            if spec is None or spec.loader is None:
                print(f"[WARNING] {pillar_name.upper()}: Could not load module.")
                failed_pillars += 1
                continue
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check if run_audit function exists
            if not hasattr(module, 'run_audit'):
                print(f"[WARNING] {pillar_name.upper()}: Missing run_audit function.")
                failed_pillars += 1
                continue
            
            # 2. EXECUTE: Every pillar MUST have a run_audit function
            try:
                findings = module.run_audit(client, settings)
                
                if findings and isinstance(findings, list):
                    # Validate findings structure
                    valid_findings = []
                    required_fields = ['created_at', 'target_date', 'department', 'task_type', 'item_involved', 'description', 'status', 'priority']
                    
                    for finding in findings:
                        if isinstance(finding, dict):
                            # Check if all required fields are present
                            if all(field in finding for field in required_fields):
                                valid_findings.append(finding)
                            else:
                                missing = [f for f in required_fields if f not in finding]
                                print(f"[WARNING] {pillar_name.upper()}: Finding missing fields: {missing}")
                    
                    if valid_findings:
                        all_tasks.extend(valid_findings)
                        print(f"[OK] {pillar_name.upper()}: Found {len(valid_findings)} issues.")
                    else:
                        print(f"[OK] {pillar_name.upper()}: System Healthy.")
                    successful_pillars += 1
                else:
                    print(f"[OK] {pillar_name.upper()}: System Healthy.")
                    successful_pillars += 1
                    
            except Exception as e:
                print(f"[WARNING] {pillar_name.upper()} FAILED: {e}")
                failed_pillars += 1
                import traceback
                traceback.print_exc()
                continue
                
        except Exception as e:
            print(f"[ERROR] {pillar_name.upper()}: Could not load: {e}")
            failed_pillars += 1
            continue
    
    print(f"\nPillar Summary: {successful_pillars} successful, {failed_pillars} failed")
    
    # 3. CONSOLIDATE: Batch upload to BigQuery
    if all_tasks:
        table_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}.ai_task_queue"
        try:
            df_tasks = pd.DataFrame(all_tasks)
            if 'created_at' in df_tasks.columns:
                df_tasks['created_at'] = pd.to_datetime(df_tasks['created_at'], errors='coerce')
            for c in ['target_date', 'department', 'task_type', 'item_involved', 'description', 'status', 'priority']:
                if c in df_tasks.columns:
                    df_tasks[c] = df_tasks[c].astype(str).fillna('').str.strip()
            df_tasks = df_tasks.dropna(subset=['created_at', 'target_date', 'task_type'])
            # Deduplicate within the batch to avoid spamming repeated alerts (common for audit pillars).
            dedupe_cols = [c for c in ['target_date', 'department', 'task_type', 'item_involved', 'description', 'status', 'priority'] if c in df_tasks.columns]
            if dedupe_cols:
                df_tasks = df_tasks.drop_duplicates(subset=dedupe_cols, keep='first')
            if df_tasks.empty:
                crash_report("sentinel_hub", "Pre-Validation: 0 valid tasks after cleaning; refusing WRITE_APPEND", {"all_tasks_count": len(all_tasks)}, None)
            
            job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
            job = client.load_table_from_dataframe(df_tasks, table_id, job_config=job_config)
            job.result(timeout=None)
            print(f"\nTOTAL HUB STATUS: {len(df_tasks)} alerts pushed to AI Task Queue.")
        except NotFound as e:
            crash_report("sentinel_hub", f"Table ai_task_queue not found: {e}", {"table_id": table_id}, sys.exc_info())
        except Exception as e:
            crash_report("sentinel_hub", f"BigQuery upload failed: {e}", {"rows": len(all_tasks), "table_id": table_id}, sys.exc_info())
    else:
        print("\nTOTAL HUB STATUS: No issues found across all pillars.")

if __name__ == "__main__":
    try:
        run_sentinel_hub()
    except KeyboardInterrupt:
        print("\n\nSENTINEL INTERRUPTED BY USER")
        sys.exit(0)
    except DataIntegrityError as e:
        append_crash_state("sentinel_hub", str(e), getattr(e, 'state_of_data', {}))
        sys.exit(1)
    except Exception as e:
        append_crash_state("sentinel_hub", str(e), {})
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
