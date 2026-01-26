import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from titan_integrity import DataIntegrityError, crash_report, append_crash_state
from pillars.system_logger import ensure_system_error_log_table, log_error, ensure_system_sync_log_table, log_sync_success

import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
import hashlib
import re
import settings

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

if not os.path.exists(settings.KEY_FILE):
    print("❌ ERROR: Key file missing.")
    sys.exit(1)

bq_client = bigquery.Client.from_service_account_json(settings.KEY_FILE)
creds = service_account.Credentials.from_service_account_file(settings.KEY_FILE, scopes=settings.SCOPE_URL)
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
        col_lower = str(col).lower()
        for kw in keywords:
            if kw.lower() in col_lower:
                return df[col]
    return pd.Series([""] * len(df))


def read_drive_file(file_id, file_name):
    print(f"📥 Processing '{file_name}'...")
    try:
        request = drive_service.files().get_media(fileId=file_id)
        file_content = io.BytesIO(request.execute())
    except Exception as e:
        raise DataIntegrityError(f"Drive get_media failed: {e}", {"file": file_name, "file_id": file_id})

    try:
        if file_name.endswith('.csv'):
            df_raw = pd.read_csv(file_content, header=None)
        else:
            df_raw = pd.read_excel(file_content, header=None)
    except Exception as e:
        raise DataIntegrityError(f"Could not read file as CSV/Excel: {e}", {"file": file_name})

    header_idx = None
    for i, row in df_raw.iterrows():
        if "date" in str(row.values).lower() and "amount" in str(row.values).lower():
            header_idx = i
            break
    if header_idx is None:
        raise DataIntegrityError("Header row (date+amount) not found", {"file": file_name})

    file_content.seek(0)
    if file_name.endswith('.csv'):
        df = pd.read_csv(file_content, header=header_idx)
    else:
        df = pd.read_excel(file_content, header=header_idx)
    df.columns = df.columns.astype(str).str.strip()
    # TITAN-INTEGRITY: require Amount column — crash and log file name if missing
    if not any(str(c).lower().replace(" ", "").startswith("amount") or "amount" in str(c).lower() for c in df.columns):
        raise DataIntegrityError("Missing 'Amount' column", {"file": file_name, "columns": list(df.columns)})
    date_col = next((c for c in df.columns if 'Date' in c), None)
    if date_col:
        df = df.dropna(subset=[date_col])
        df = df[df[date_col].astype(str).str.lower().str.contains('total') == False]
    return df


def sync():
    print("📡 Scanning Expenses Folder...")
    results = drive_service.files().list(
        q=f"'{settings.FOLDER_ID_EXPENSES}' in parents and trashed=false",
        fields="files(id, name)"
    ).execute()
    files = results.get('files', [])

    if not files:
        print("No expense files in folder; nothing to sync.")
        return

    combined_df = pd.DataFrame()
    for f in files:
        df = read_drive_file(f['id'], f['name'])
        combined_df = pd.concat([combined_df, df])

    if combined_df.empty:
        crash_report("sync_expenses", "Files found but no valid rows after read (Pre-Validation)", {"files_count": len(files), "file_names": [x["name"] for x in files]}, None)

    raw_reason = get_col(combined_df, ['Reason', 'Category', 'Expense Head']).astype(str)
    # Dynamic Ledger Parsing: " - " split first; if missing, keyword map (Electric->Electricity, Rent->Rent, etc.); else use raw, main_category=Uncategorized
    def _keyword_to_ledger(s):
        t = str(s or "").strip().lower()
        if not t:
            return "Uncategorized"
        if "electric" in t:
            return "Electricity"
        if re.search(r"\brent\b", t):
            return "Rent"
        if "salar" in t:  # salary, salaries
            return "Salary"
        if "house keeping" in t or "housekeeping" in t:
            return "House Keeping"
        if "repair" in t:
            return "Repairs"
        if "maintenance" in t:
            return "Maintenance"
        return "Uncategorized"

    def _split_ledger(s):
        s = str(s or "").strip()
        if " - " in s:
            parts = s.split(" - ", 1)
            return (parts[0].strip() or "Uncategorized", (parts[1].strip() if len(parts) > 1 else "Uncategorized"))
        mapped = _keyword_to_ledger(s)
        if mapped != "Uncategorized":
            return (mapped, "Uncategorized")
        return (s or "Uncategorized", "Uncategorized")

    _ledger, _main = zip(*raw_reason.apply(_split_ledger))

    clean_df = pd.DataFrame()
    clean_df['expense_date'] = pd.to_datetime(get_col(combined_df, ['Date']), dayfirst=True, errors='coerce').dt.date
    clean_df['category'] = raw_reason
    clean_df['ledger_name'] = list(_ledger)
    clean_df['main_category'] = list(_main)
    clean_df['item_name'] = get_col(combined_df, ['Explanation', 'Description', 'Item Name']).astype(str)
    clean_df['amount'] = pd.to_numeric(get_col(combined_df, ['Amount', 'Amount (₹)']), errors='coerce').fillna(0)
    clean_df['payment_mode'] = get_col(combined_df, ['Paid From', 'Payment Mode']).astype(str)
    _staff = get_col(combined_df, ['Created By', 'Employee', 'Staff', 'Entered By', 'Paid By']).astype(str).str.strip()
    clean_df['staff_name'] = _staff.apply(lambda x: x if (x and str(x).strip()) else "Unknown")
    clean_df['remarks'] = get_col(combined_df, ['Remarks', 'Note']).astype(str)
    clean_df = clean_df.dropna(subset=['expense_date'])

    clean_df['fingerprint'] = clean_df.apply(lambda x: f"{x['expense_date']}_{x['amount']}_{normalize_text(x['item_name'])}", axis=1)
    final_df = clean_df.drop_duplicates(subset=['fingerprint'], keep='last').drop(columns=['fingerprint'])

    if final_df.empty:
        crash_report("sync_expenses", "Pre-Validation: 0 rows after clean/dedup; refusing WRITE_TRUNCATE", {"combined_rows": len(combined_df)}, None)

    final_df['expense_id'] = final_df.apply(lambda x: hashlib.md5(f"{x['expense_date']}{x['item_name']}{x['amount']}".lower().strip().encode()).hexdigest(), axis=1)
    final_df['expense_date'] = pd.to_datetime(final_df['expense_date'])

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = bq_client.load_table_from_dataframe(final_df, f"{settings.PROJECT_ID}.{settings.DATASET_ID}.{settings.TABLE_EXPENSES}", job_config=job_config)
    job.result(timeout=None)
    log_sync_success("expenses", len(final_df), bq_client, settings)
    print(f"✅ SUCCESS: Synced {len(final_df)} validated expenses.")


if __name__ == "__main__":
    try:
        sync()
    except DataIntegrityError as e:
        append_crash_state("sync_expenses", str(e), getattr(e, 'state_of_data', {}))
        ensure_system_error_log_table(bq_client, settings)
        log_error("sync_expenses", str(e), context=json.dumps({"file": getattr(e, "state_of_data", {}).get("file", ""), "state": getattr(e, "state_of_data", {})}), client=bq_client, settings_mod=settings)
        sys.exit(1)
