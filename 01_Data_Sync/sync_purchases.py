import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from titan_integrity import DataIntegrityError, crash_report, append_crash_state
from pillars.system_logger import ensure_system_error_log_table, log_error, log_sync_success

import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
from datetime import datetime
import settings

# Header-agnostic parser for Item/Qty/Price regardless of column position
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from header_utils import find_header_row_purchases, build_purchases_row_agnostic

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

if not os.path.exists(settings.KEY_FILE):
    print("❌ ERROR: Key file missing.")
    sys.exit(1)

bq_client = bigquery.Client.from_service_account_json(settings.KEY_FILE)
creds = service_account.Credentials.from_service_account_file(settings.KEY_FILE, scopes=settings.SCOPE_URL)
drive_service = build('drive', 'v3', credentials=creds)


def read_drive_file(file_id, file_name):
    print(f"📥 Processing '{file_name}'...")
    try:
        content_bytes = drive_service.files().get_media(fileId=file_id).execute()
        file_content = io.BytesIO(content_bytes)
    except Exception as e:
        raise DataIntegrityError(f"Drive get_media failed: {e}", {"file": file_name})

    df_raw = None
    if file_name.lower().endswith('.csv'):
        try:
            df_raw = pd.read_csv(file_content, header=None)
        except Exception:
            file_content.seek(0)
    if df_raw is None:
        try:
            df_raw = pd.read_excel(file_content, header=None)
        except Exception:
            file_content.seek(0)
    if df_raw is None:
        try:
            tables = pd.read_html(file_content)
            if tables:
                df_raw = tables[0]
        except Exception:
            pass
    if df_raw is None:
        raise DataIntegrityError("Could not parse as CSV, Excel, or HTML", {"file": file_name})

    for i, row in df_raw.iterrows():
        if "supplier" in str(row.values).lower() and "invoice" in str(row.values).lower():
            df_raw.columns = df_raw.iloc[i]
            _df = df_raw.iloc[i + 1:].reset_index(drop=True)
            # TITAN-INTEGRITY: need enough columns for net_amount (index 10) and an amount-like column
            if len(_df.columns) < 11:
                raise DataIntegrityError("Not enough columns (need ≥11 for net_amount)", {"file": file_name, "columns": len(_df.columns)})
            _cols_lower = [str(c).lower() for c in _df.columns]
            if not any(any(k in c for k in ("amount", "net", "total", "subtotal")) for c in _cols_lower):
                raise DataIntegrityError("Missing amount-like column (Amount/net/total/subtotal)", {"file": file_name, "columns": list(_df.columns)})
            return _df
    raise DataIntegrityError("Header row (Supplier+Invoice) not found", {"file": file_name})


def clean_money(val):
    if pd.isna(val):
        return 0.0
    s = str(val).replace(',', '').replace('₹', '').strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def sync():
    print("📡 Scanning Purchases Folder...")
    results = drive_service.files().list(q=f"'{settings.FOLDER_ID_PURCHASES}' in parents and trashed=false", fields="files(id, name)").execute()
    files = results.get('files', [])

    if not files:
        print("❌ No Purchase files found.")
        return

    all_purchases = pd.DataFrame()
    for f in files:
        df = read_drive_file(f['id'], f['name'])
        if df.empty:
            continue
        try:
            clean_df = build_purchases_row_agnostic(df, clean_money)
            if clean_df.empty:
                continue
            clean_df['source_file'] = f['name']
            clean_df['last_synced'] = datetime.now()
            all_purchases = pd.concat([all_purchases, clean_df])
        except (IndexError, KeyError) as e:
            raise DataIntegrityError(f"Column mapping failed: {e}", {"file": f['name'], "columns": len(df.columns)})

    if all_purchases.empty:
        crash_report("sync_purchases", "Pre-Validation: Purchase files yielded 0 rows; refusing WRITE_TRUNCATE", {"files": [x["name"] for x in files]}, None)

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", autodetect=True)
    table_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}.{settings.TABLE_PURCHASES}"
    job = bq_client.load_table_from_dataframe(all_purchases, table_id, job_config=job_config)
    job.result(timeout=None)
    log_sync_success("purchases", len(all_purchases), bq_client, settings)
    print("✅ SUCCESS: All Purchase files merged and synced!")


if __name__ == "__main__":
    try:
        sync()
    except DataIntegrityError as e:
        append_crash_state("sync_purchases", str(e), getattr(e, 'state_of_data', {}))
        ensure_system_error_log_table(bq_client, settings)
        log_error("sync_purchases", str(e), context=json.dumps({"file": getattr(e, "state_of_data", {}).get("file", ""), "state": getattr(e, "state_of_data", {})}), client=bq_client, settings_mod=settings)
        sys.exit(1)
