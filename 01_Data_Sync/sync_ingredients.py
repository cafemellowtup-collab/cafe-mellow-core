import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from titan_integrity import DataIntegrityError, crash_report, append_crash_state

import requests
import json
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import settings

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

API_TIMEOUT = 1800

if not os.path.exists(settings.KEY_FILE):
    print("❌ ERROR: Key file missing.")
    sys.exit(1)

bq_client = bigquery.Client.from_service_account_json(settings.KEY_FILE)
URL = "https://api.petpooja.com/V1/thirdparty/get_stock_api/"


def sync():
    print("📡 Contacting Petpooja Inventory...")
    today_str = datetime.now().strftime("%d-%m-%Y")
    payload = {
        "app_key": settings.PP_APP_KEY,
        "app_secret": settings.PP_APP_SECRET,
        "access_token": settings.PP_ACCESS_TOKEN,
        "menuSharingCode": settings.PP_MAPPING_CODE,
        "date": today_str
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(URL, headers=headers, data=json.dumps(payload), timeout=API_TIMEOUT)
    except requests.exceptions.Timeout:
        crash_report("sync_ingredients", "Petpooja get_stock_api timeout", {"date": today_str}, sys.exc_info())
    except Exception as e:
        crash_report("sync_ingredients", str(e), {"date": today_str}, sys.exc_info())

    if response.status_code != 200:
        crash_report("sync_ingredients", f"API HTTP {response.status_code}", {"date": today_str, "body": response.text[:500]}, None)

    try:
        data = response.json()
    except Exception as e:
        raise DataIntegrityError(f"Invalid JSON from Petpooja: {e}", {"date": today_str, "body_preview": response.text[:200]})

    if data.get("success") != "1":
        crash_report("sync_ingredients", f"API success != '1': {data.get('message', data)}", {"date": today_str, "data_keys": list(data.keys())}, None)

    if "closing_json" not in data:
        crash_report("sync_ingredients", "API response missing required 'closing_json'", {"date": today_str, "data_keys": list(data.keys())}, None)

    raw_list = data["closing_json"]
    if not isinstance(raw_list, list):
        crash_report("sync_ingredients", "closing_json is not a list", {"date": today_str, "type": type(raw_list).__name__}, None)

    df = pd.DataFrame(raw_list)
    if df.empty:
        print("API returned 0 items; writing empty table.")
    else:
        required = ['name', 'unit', 'qty', 'price', 'category']
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise DataIntegrityError(f"Petpooja closing_json missing columns: {missing}", {"date": today_str, "columns": list(df.columns)})
        df = df[required]
        df.columns = ['item_name', 'unit', 'current_stock', 'latest_price', 'category']
        df['current_stock'] = pd.to_numeric(df['current_stock'], errors='coerce').fillna(0)
        df['latest_price'] = pd.to_numeric(df['latest_price'], errors='coerce').fillna(0)
    df['last_updated'] = datetime.now()

    table_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}.{settings.TABLE_INGREDIENTS}"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", autodetect=True)
    job = bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result(timeout=None)
    print(f"✨ SUCCESS: Inventory Synced! ({len(df)} items)")


if __name__ == "__main__":
    try:
        sync()
    except DataIntegrityError as e:
        append_crash_state("sync_ingredients", str(e), getattr(e, 'state_of_data', {}))
        sys.exit(1)
