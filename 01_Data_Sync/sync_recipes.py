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
import settings

# Header-agnostic parser for Item/RawMaterial/Qty/Unit regardless of column position
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from header_utils import find_header_row_recipes, build_recipes_rows_agnostic

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
        except Exception as e:
            raise DataIntegrityError(f"Could not read CSV: {e}", {"file": file_name})
    if df_raw is None:
        try:
            file_content.seek(0)
            df_raw = pd.read_excel(file_content, header=None)
        except Exception as e:
            raise DataIntegrityError(f"Could not read Excel: {e}", {"file": file_name})
    if df_raw is None:
        try:
            file_content.seek(0)
            tables = pd.read_html(file_content)
            if tables:
                df_raw = tables[0]
        except Exception as e:
            raise DataIntegrityError(f"Could not read HTML: {e}", {"file": file_name})

    if df_raw is None:
        raise DataIntegrityError("Could not parse file as CSV, Excel, or HTML", {"file": file_name})

    # Header-agnostic: find row with ItemName/Item and (RawMaterial or Ingredient or Qty)
    hdr_idx, _df = find_header_row_recipes(df_raw)
    if hdr_idx is not None and _df is not None:
        return _df
    raise DataIntegrityError("Header row (ItemName/Item + RawMaterial/Ingredient/Qty) not found", {"file": file_name})


def sync():
    print("📡 Scanning Recipe Drop Folder...")
    results = drive_service.files().list(
        q=f"'{settings.FOLDER_ID_RECIPES}' in parents and name contains 'Recipe' and trashed=false",
        fields="files(id, name)"
    ).execute()
    files = results.get('files', [])

    if not files:
        print("❌ No 'Recipe' files found.")
        return

    all_recipes = pd.DataFrame()
    for f in files:
        df = read_drive_file(f['id'], f['name'])
        processed_df = build_recipes_rows_agnostic(df)
        if not processed_df.empty:
            all_recipes = pd.concat([all_recipes, processed_df])

    if all_recipes.empty:
        crash_report("sync_recipes", "Pre-Validation: Recipe files yielded 0 rows; refusing WRITE_TRUNCATE", {"files": [x["name"] for x in files]}, None)

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", autodetect=True)
    job = bq_client.load_table_from_dataframe(all_recipes, f"{settings.PROJECT_ID}.{settings.DATASET_ID}.{settings.TABLE_RECIPES}", job_config=job_config)
    job.result(timeout=None)
    log_sync_success("recipes", len(all_recipes), bq_client, settings)
    print("✅ SUCCESS: Sales Recipes Synced!")


if __name__ == "__main__":
    try:
        sync()
    except DataIntegrityError as e:
        append_crash_state("sync_recipes", str(e), getattr(e, 'state_of_data', {}))
        ensure_system_error_log_table(bq_client, settings)
        log_error("sync_recipes", str(e), context=json.dumps({"file": getattr(e, "state_of_data", {}).get("file", ""), "state": getattr(e, "state_of_data", {})}), client=bq_client, settings_mod=settings)
        sys.exit(1)
