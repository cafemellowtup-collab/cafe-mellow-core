import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from titan_integrity import DataIntegrityError, crash_report, append_crash_state

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import requests
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import json
import hashlib
from datetime import datetime, timedelta
import time

KEY_FILE = "service-key.json"
PROJECT_ID = "cafe-mellow-core-2026"
DATASET_ID = "cafe_operations"
RAW_TABLE = "sales_raw_layer"
STATE_FILE = "sales_sync_state.json"

PETPOOJA_API_URL = "https://api.petpooja.com/V1/thirdparty/generic_get_orders/"
APP_KEY = "uvw0th4nksi97o1bgqp35zjxr6e2may8"
APP_SECRET = "9450cbbbb22be056537e82138f1fa15220656e9b"
ACCESS_TOKEN = "9949a4aea79acad2e22e501e89c5ff3146f15e48"
REST_ID = "6skcngup"

# Slow-but-sure: 30 min for large historical syncs
API_TIMEOUT = 1800

def validate_setup():
    errors = []
    if not os.path.exists(KEY_FILE):
        errors.append(f"ERROR: {KEY_FILE} missing.")
        return False, errors
    try:
        test_client = bigquery.Client.from_service_account_json(KEY_FILE)
        test_client.get_dataset(f"{PROJECT_ID}.{DATASET_ID}")
    except NotFound:
        errors.append(f"ERROR: Dataset {DATASET_ID} not found in project {PROJECT_ID}")
        return False, errors
    except Exception as e:
        errors.append(f"ERROR: BigQuery connection failed: {e}")
        return False, errors
    return True, []

is_valid, errors = validate_setup()
if not is_valid:
    for e in errors:
        print(e)
    sys.exit(1)

bq_client = bigquery.Client.from_service_account_json(KEY_FILE)


def generate_hash(json_str):
    try:
        return hashlib.md5(json_str.encode('utf-8')).hexdigest()
    except Exception as e:
        raise DataIntegrityError(f"Hash generation failed: {e}", {"input_type": type(json_str).__name__, "input_len": len(str(json_str))})


def fetch_orders_for_date(target_date, max_retries=3):
    headers = {"Content-Type": "application/json"}
    payload = {
        "app_key": APP_KEY, "app_secret": APP_SECRET,
        "access_token": ACCESS_TOKEN, "restID": REST_ID,
        "order_date": target_date.strftime("%Y-%m-%d"),
        "refId": ""
    }
    for attempt in range(max_retries):
        try:
            response = requests.post(PETPOOJA_API_URL, json=payload, headers=headers, timeout=API_TIMEOUT)
            if response.status_code != 200:
                crash_report(
                    "sync_sales_raw",
                    f"Petpooja API returned HTTP {response.status_code}",
                    {"date": target_date.strftime("%Y-%m-%d"), "status": response.status_code, "body": response.text[:1000]},
                    sys.exc_info()
                )
            data = response.json()
            if data.get('success') != '1':
                crash_report(
                    "sync_sales_raw",
                    f"Petpooja API success != '1': {data.get('message', data)}",
                    {"date": target_date.strftime("%Y-%m-%d"), "data_keys": list(data.keys())},
                    None
                )
            return data.get('order_json', []) or []
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2)
                continue
            crash_report("sync_sales_raw", "Petpooja API timeout after retries", {"date": target_date.strftime("%Y-%m-%d"), "attempt": attempt + 1}, sys.exc_info())
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            crash_report("sync_sales_raw", str(e), {"date": target_date.strftime("%Y-%m-%d")}, sys.exc_info())
    return []


def process_orders(orders, date_str):
    if not orders:
        return
    # Petpooja sometimes returns duplicate orders for a date. Deduplicate by orderID to avoid
    # inflating counts and downstream revenue.
    dedup: dict[str, dict] = {}
    timestamp = datetime.now().isoformat()
    for outer_obj in orders:
        if not isinstance(outer_obj, dict):
            raise DataIntegrityError(f"Order is not dict: {type(outer_obj)}", {"date": date_str, "order_type": type(outer_obj).__name__})
        order_part = outer_obj.get('Order')
        if not order_part or not isinstance(order_part, dict):
            raise DataIntegrityError("Order missing or invalid 'Order' key", {"date": date_str, "keys": list(outer_obj.keys())})
        oid = order_part.get('orderID')
        if oid is None:
            raise DataIntegrityError("Order missing required 'orderID'", {"date": date_str, "order_keys": list(order_part.keys())})
        oid = str(oid)
        b_date = order_part.get('order_date', date_str)
        full_blob = json.dumps(outer_obj, ensure_ascii=False)
        row = {
            "order_id": oid,
            "bill_date": b_date,
            "full_json": full_blob,
            "ingested_at": timestamp,
            "row_hash": generate_hash(full_blob)
        }
        # Keep the latest occurrence if duplicates exist.
        dedup[oid] = row

    rows = list(dedup.values())

    # Pre-Validation: we must have rows before any DELETE
    if not rows:
        return

    df = pd.DataFrame(rows)
    df['bill_date'] = pd.to_datetime(df['bill_date'], errors='coerce').dt.date
    df['ingested_at'] = pd.to_datetime(df['ingested_at'], errors='coerce')
    df = df.dropna(subset=['bill_date', 'ingested_at'])
    if df.empty:
        crash_report("sync_sales_raw", "All rows had invalid dates after parse", {"date": date_str, "rows_before_dropna": len(rows)}, None)

    # Atomic: DELETE then INSERT. BigQuery job must complete fully.
    try:
        del_query = f"DELETE FROM `{PROJECT_ID}.{DATASET_ID}.{RAW_TABLE}` WHERE bill_date = '{date_str}'"
        job = bq_client.query(del_query)
        job.result(timeout=None)
    except Exception as e:
        crash_report("sync_sales_raw", f"DELETE failed: {e}", {"date": date_str, "rows_ready": len(df)}, sys.exc_info())

    job_config = bigquery.LoadJobConfig(
        schema=[bigquery.SchemaField("bill_date", "DATE"), bigquery.SchemaField("ingested_at", "TIMESTAMP")],
        write_disposition="WRITE_APPEND"
    )
    job = bq_client.load_table_from_dataframe(df, f"{PROJECT_ID}.{DATASET_ID}.{RAW_TABLE}", job_config=job_config)
    job.result(timeout=None)
    print(f"[OK] Saved {len(df)} raw orders for {date_str}")


def run_sync_engine():
    try:
        start_date = datetime(2023, 12, 1)
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    saved_date = datetime.strptime(state['last_synced'], "%Y-%m-%d")
                    if (datetime.now() - saved_date).days < 2:
                        start_date = datetime.now() - timedelta(days=90)
                    else:
                        start_date = saved_date
            except Exception as e:
                crash_report("sync_sales_raw", f"Invalid state file: {e}", {"file": STATE_FILE}, sys.exc_info())

        current_date = start_date
        today = datetime.now()
        print(f"RAW SYNC STARTED: {current_date.date()} -> {today.date()}")

        while current_date <= today:
            date_str = current_date.strftime("%Y-%m-%d")
            print(f"Scanning {date_str}...", end="\r")
            try:
                orders = fetch_orders_for_date(current_date)
                if orders:
                    process_orders(orders, date_str)
                with open(STATE_FILE, 'w') as f:
                    json.dump({"last_synced": date_str}, f)
            except DataIntegrityError:
                raise
            except Exception as e:
                crash_report("sync_sales_raw", str(e), {"date": date_str}, sys.exc_info())
            current_date += timedelta(days=1)
            time.sleep(0.5)
        print("\nSYNC COMPLETE.")
    except KeyboardInterrupt:
        print("\n\nSYNC INTERRUPTED BY USER")
        sys.exit(0)
    except DataIntegrityError as e:
        append_crash_state("sync_sales_raw", str(e), getattr(e, 'state_of_data', {}))
        sys.exit(1)

if __name__ == "__main__":
    run_sync_engine()
