import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from titan_integrity import DataIntegrityError, crash_report, append_crash_state

import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
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
    return df_raw


def parse_production_master(df):
    clean_rows = []
    current_production_item = None
    start_row = 0
    for i, row in df.iterrows():
        if "Production Name" in str(row.iloc[0]):
            start_row = i + 1
            break
    for i in range(start_row, len(df)):
        row = df.iloc[i]
        col0 = str(row.iloc[0]).strip()
        if col0 and col0.lower() != 'nan':
            current_production_item = col0.title()
            continue
        col1 = str(row.iloc[1]).strip()
        if col1 and col1.lower() not in ('nan', 'raw material'):
            output_qty = 0
            output_unit = ""
            if len(row) > 5:
                val = pd.to_numeric(row.iloc[5], errors='coerce')
                if not pd.isna(val):
                    output_qty = val
                output_unit = str(row.iloc[6]) if len(row) > 6 else ""
            clean_rows.append({
                'production_item': current_production_item,
                'input_ingredient': col1,
                'input_qty': pd.to_numeric(row.iloc[2], errors='coerce') or 0,
                'input_unit': str(row.iloc[3]),
                'yield_qty': output_qty,
                'yield_unit': output_unit,
                'recipe_type': 'PRODUCTION_LINK'
            })
    return pd.DataFrame(clean_rows)


def sync():
    print("📡 Scanning Recipe Drop Folder for Production Files...")
    results = drive_service.files().list(
        q=f"'{settings.FOLDER_ID_RECIPES}' in parents and (name contains 'Conversion' or name contains 'Raw Material') and trashed=false",
        fields="files(id, name)"
    ).execute()
    files = results.get('files', [])

    if not files:
        print("❌ No Production files found.")
        return

    all_production = pd.DataFrame()
    for f in files:
        df = read_drive_file(f['id'], f['name'])
        processed_df = parse_production_master(df)
        all_production = pd.concat([all_production, processed_df])

    if all_production.empty:
        crash_report("sync_production", "Pre-Validation: Production files yielded 0 rows; refusing WRITE_TRUNCATE", {"files": [x["name"] for x in files]}, None)

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", autodetect=True)
    job = bq_client.load_table_from_dataframe(all_production, f"{settings.PROJECT_ID}.{settings.DATASET_ID}.{settings.TABLE_PRODUCTION}", job_config=job_config)
    job.result(timeout=None)
    print("✅ SUCCESS: Production Recipes Synced!")


if __name__ == "__main__":
    try:
        sync()
    except DataIntegrityError as e:
        append_crash_state("sync_production", str(e), getattr(e, 'state_of_data', {}))
        sys.exit(1)
