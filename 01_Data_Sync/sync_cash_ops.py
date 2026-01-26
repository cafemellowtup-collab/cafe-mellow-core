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
import hashlib
import re
from datetime import datetime

import settings

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KEY_FILE = getattr(settings, "KEY_FILE", "service-key.json")
KEY_PATH = KEY_FILE if os.path.isabs(KEY_FILE) else os.path.join(_ROOT, KEY_FILE)
PROJECT_ID = getattr(settings, "PROJECT_ID", "cafe-mellow-core-2026")
DATASET_ID = getattr(settings, "DATASET_ID", "cafe_operations")
TABLE_ID = getattr(settings, "TABLE_CASH", "cash_flow_master")
DRIVE_FOLDER_ID = getattr(settings, "FOLDER_ID_CASH_OPS", "1WsoWDQtkyBcmchEkJ2CgETb64JUvvroS")

if not os.path.exists(KEY_PATH):
    print("❌ ERROR: Key file missing.")
    sys.exit(1)

bq_client = bigquery.Client.from_service_account_json(KEY_PATH)
creds = service_account.Credentials.from_service_account_file(KEY_PATH, scopes=getattr(settings, "SCOPE_URL", ["https://www.googleapis.com/auth/drive.readonly"]))
drive_service = build('drive', 'v3', credentials=creds)


def normalize_text(text):
    if not isinstance(text, str):
        return str(text)
    return re.sub(r'[^a-z0-9]', '', text.lower())


def get_col(df, keywords):
    for col in df.columns:
        if str(col).strip() in keywords:
            return df[col]
    for col in df.columns:
        for kw in keywords:
            if kw.lower() in str(col).lower():
                return df[col]
    return pd.Series([""] * len(df))


def read_drive_file(file_id, file_name):
    print(f"📥 Processing '{file_name}'...")
    file_name_clean = file_name.lower().replace(" ", "_")
    if "withdrawal" in file_name_clean:
        row_type = "WITHDRAWAL"
    elif "top" in file_name_clean:
        row_type = "TOPUP"
    else:
        return None

    try:
        file_content = io.BytesIO(drive_service.files().get_media(fileId=file_id).execute())
    except Exception as e:
        raise DataIntegrityError(f"Drive get_media failed: {e}", {"file": file_name})

    try:
        df_raw = pd.read_csv(file_content, header=None) if file_name.endswith('.csv') else pd.read_excel(file_content, header=None)
    except Exception as e:
        raise DataIntegrityError(f"Could not read file: {e}", {"file": file_name})

    header_idx = None
    for i, row in df_raw.iterrows():
        if "date" in str(row.values).lower() and "amount" in str(row.values).lower():
            header_idx = i
            break
    if header_idx is None:
        raise DataIntegrityError("Header row (date+amount) not found", {"file": file_name})

    file_content.seek(0)
    df = pd.read_csv(file_content, header=header_idx) if file_name.endswith('.csv') else pd.read_excel(file_content, header=header_idx)
    df.columns = df.columns.astype(str).str.strip()
    date_col = next((c for c in df.columns if 'Date' in c), None)
    if date_col:
        df = df.dropna(subset=[date_col])
        df = df[df[date_col].astype(str).str.lower().str.contains('total') == False]
    df['txn_type'] = row_type
    return df


def sync():
    print("📡 Scanning Cash Ops Folder...")
    results = drive_service.files().list(q=f"'{DRIVE_FOLDER_ID}' in parents and trashed=false").execute()
    files = results.get('files', [])

    if not files:
        print("No files; nothing to sync.")
        return

    combined_df = pd.DataFrame()
    for f in files:
        d = read_drive_file(f['id'], f['name'])
        if d is not None:
            combined_df = pd.concat([combined_df, d])

    if combined_df.empty:
        crash_report("sync_cash_ops", "Files found but no valid rows (Pre-Validation)", {"files": [x["name"] for x in files]}, None)

    clean_df = pd.DataFrame()
    clean_df['entry_date'] = pd.to_datetime(get_col(combined_df, ['Date']), dayfirst=True, errors='coerce').dt.date
    clean_df['txn_type'] = combined_df['txn_type']
    clean_df['category'] = get_col(combined_df, ['Reason', 'Category']).astype(str)
    clean_df['description'] = get_col(combined_df, ['Explanation', 'Note', 'Description']).astype(str)
    clean_df['amount'] = pd.to_numeric(get_col(combined_df, ['Amount', 'Amount (₹)']), errors='coerce').fillna(0)
    clean_df = clean_df.dropna(subset=['entry_date'])

    clean_df['fingerprint'] = clean_df.apply(lambda x: f"{x['entry_date']}_{x['txn_type']}_{x['amount']}_{normalize_text(x['description'])}", axis=1)
    final_df = clean_df.drop_duplicates(subset=['fingerprint'], keep='last').drop(columns=['fingerprint'])

    if final_df.empty:
        crash_report("sync_cash_ops", "Pre-Validation: 0 rows after clean; refusing WRITE_TRUNCATE", {"combined_rows": len(combined_df)}, None)

    final_df['txn_id'] = final_df.apply(lambda x: hashlib.md5(f"{x['entry_date']}{x['txn_type']}{x['description']}{x['amount']}".lower().strip().encode()).hexdigest(), axis=1)
    final_df['entry_date'] = pd.to_datetime(final_df['entry_date'])
    final_df['last_updated'] = datetime.now()

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = bq_client.load_table_from_dataframe(final_df, f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}", job_config=job_config)
    job.result(timeout=None)
    log_sync_success("cash_ops", len(final_df), bq_client, settings)
    print(f"✅ SUCCESS: Synced {len(final_df)} cash movements.")


if __name__ == "__main__":
    try:
        sync()
    except DataIntegrityError as e:
        append_crash_state("sync_cash_ops", str(e), getattr(e, 'state_of_data', {}))
        ensure_system_error_log_table(bq_client, settings)
        log_error("sync_cash_ops", str(e), context=json.dumps({"file": getattr(e, "state_of_data", {}).get("file", ""), "state": getattr(e, "state_of_data", {})}), client=bq_client, settings_mod=settings)
        sys.exit(1)
