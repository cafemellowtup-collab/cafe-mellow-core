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
        if "raw material" in str(row.values).lower() and "quantity" in str(row.values).lower():
            df_raw.columns = df_raw.iloc[i]
            _df = df_raw.iloc[i + 1:].reset_index(drop=True)
            # TITAN-INTEGRITY: require Amount (₹) or amount-like column
            _cols_lower = [str(c).lower() for c in _df.columns]
            if not any("amount" in c or "₹" in c for c in _cols_lower):
                raise DataIntegrityError("Missing 'Amount (₹)' or amount-like column", {"file": file_name, "columns": list(_df.columns)})
            return _df
    raise DataIntegrityError("Header row (Raw Material+Quantity) not found", {"file": file_name})


def clean_money(val):
    if pd.isna(val):
        return 0.0
    s = str(val).replace(',', '').replace('₹', '').strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def sync():
    print("📡 Scanning Wastage Folder...")
    results = drive_service.files().list(q=f"'{settings.FOLDER_ID_WASTAGE}' in parents and trashed=false", fields="files(id, name)").execute()
    files = results.get('files', [])

    if not files:
        print("❌ No Wastage files found.")
        return

    all_wastage = pd.DataFrame()
    for f in files:
        df = read_drive_file(f['id'], f['name'])
        if df.empty:
            continue
        fill_cols = ['Date', 'Total', 'Status', 'Created By', 'Area']
        for col in fill_cols:
            if col in df.columns:
                df[col] = df[col].ffill()
        try:
            clean_df = pd.DataFrame()
            clean_df['wastage_date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            clean_df['ingredient_name'] = df['Raw Material']
            clean_df['menu_item_involved'] = df['Item Name']
            clean_df['qty'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0)
            clean_df['unit'] = df['Unit']
            clean_df['loss_amount'] = df['Amount (₹)'].apply(clean_money)
            clean_df['reason'] = df['Description']
            clean_df['staff_name'] = df['Created By']
            clean_df['source_file'] = f['name']
            clean_df['synced_at'] = datetime.now()
            clean_df = clean_df[clean_df['ingredient_name'].notna()]
            all_wastage = pd.concat([all_wastage, clean_df])
        except (KeyError, TypeError) as e:
            raise DataIntegrityError(f"Column mapping failed: {e}", {"file": f['name'], "columns": list(df.columns)})

    if all_wastage.empty:
        crash_report("sync_wastage", "Pre-Validation: Wastage files yielded 0 rows; refusing WRITE_TRUNCATE", {"files": [x["name"] for x in files]}, None)

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", autodetect=True)
    table_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}.{settings.TABLE_WASTAGE}"
    job = bq_client.load_table_from_dataframe(all_wastage, table_id, job_config=job_config)
    job.result(timeout=None)
    log_sync_success("wastage", len(all_wastage), bq_client, settings)
    print("✅ SUCCESS: Wastage Log Synced!")


if __name__ == "__main__":
    try:
        sync()
    except DataIntegrityError as e:
        append_crash_state("sync_wastage", str(e), getattr(e, 'state_of_data', {}))
        ensure_system_error_log_table(bq_client, settings)
        log_error("sync_wastage", str(e), context=json.dumps({"file": getattr(e, "state_of_data", {}).get("file", ""), "state": getattr(e, "state_of_data", {})}), client=bq_client, settings_mod=settings)
        sys.exit(1)
