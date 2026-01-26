"""
Ensure dev_evolution_log and system_error_log exist in BigQuery. Create if missing.
Run: python scripts/ensure_dev_evolution_log.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import settings
from pillars.evolution import ensure_dev_evolution_table
from pillars.system_logger import ensure_system_error_log_table

def main():
    try:
        from google.cloud import bigquery
        client = bigquery.Client.from_service_account_json(settings.KEY_FILE)
        client.get_dataset(f"{settings.PROJECT_ID}.{settings.DATASET_ID}")
    except Exception as e:
        print(f"ERROR: BigQuery connection failed: {e}")
        sys.exit(1)
    e1, c1 = ensure_dev_evolution_table(client, settings)
    print("OK: dev_evolution_log created." if c1 else "OK: dev_evolution_log exists.")
    e2, c2 = ensure_system_error_log_table(client, settings)
    print("OK: system_error_log created." if c2 else "OK: system_error_log exists.")

if __name__ == "__main__":
    main()
