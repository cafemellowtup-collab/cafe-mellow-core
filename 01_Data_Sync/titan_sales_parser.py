import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from titan_integrity import DataIntegrityError, crash_report, append_crash_state

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import settings
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import pandas as pd
import json

def validate_connection():
    try:
        client = bigquery.Client.from_service_account_json(settings.KEY_FILE)
        client.get_dataset(f"{settings.PROJECT_ID}.{settings.DATASET_ID}")
        return True, client, None
    except NotFound as e:
        return False, None, f"Dataset or project not found: {e}"
    except Exception as e:
        return False, None, str(e)

is_valid, bq_client, error = validate_connection()
if not is_valid:
    print(f"ERROR: {error}")
    sys.exit(1)


def parse_sales_json():
    print("TITAN SALES PARSER: Extracting Item Intelligence...")
    try:
        try:
            table_ref = bq_client.get_table(f"{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_raw_layer")
            all_cols = [f.name for f in table_ref.schema]
        except NotFound:
            raise DataIntegrityError("sales_raw_layer not found. Run sync_sales_raw.py first.", {})
        except Exception as e:
            raise DataIntegrityError(f"Cannot access sales_raw_layer: {e}", {})

        json_col = 'full_json' if 'full_json' in all_cols else ('item_details' if 'item_details' in all_cols else None)
        if not json_col:
            raise DataIntegrityError(f"No JSON column in sales_raw_layer. Columns: {all_cols}", {})

        query = f"SELECT bill_date, order_id, {json_col} FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_raw_layer` LIMIT 1000000"
        qj = bq_client.query(query)
        qj.result(timeout=None)
        raw_data = qj.to_dataframe()

        if raw_data.empty:
            crash_report("titan_sales_parser", "Pre-Validation: sales_raw_layer is empty; refusing to WRITE_TRUNCATE sales_items_parsed", {}, None)

        parsed_rows = []
        for idx, row in raw_data.iterrows():
            raw_json_str = row.get(json_col)
            if not raw_json_str or raw_json_str == "":
                continue
            try:
                raw_blob = json.loads(raw_json_str)
            except json.JSONDecodeError as e:
                raise DataIntegrityError(f"Invalid JSON in sales_raw_layer: {e}", {"order_id": str(row.get('order_id')), "bill_date": str(row.get('bill_date'))})

            items = []
            if isinstance(raw_blob, list):
                items = raw_blob
            elif isinstance(raw_blob, dict):
                items = raw_blob.get('OrderItem', []) or raw_blob.get('items', [])
            if not items:
                continue

            bd = row.get('bill_date')
            oid = row.get('order_id')
            if bd is None or (hasattr(bd, '__len__') and str(bd) == 'NaT'):
                raise DataIntegrityError("Row missing bill_date", {"order_id": str(oid)})
            if oid is None or (pd.notna(oid) is False):
                raise DataIntegrityError("Row missing order_id", {"bill_date": str(bd)})

            for item in items:
                if not isinstance(item, dict):
                    raise DataIntegrityError("OrderItem element is not dict", {"order_id": str(oid)})
                iname = item.get('name') or item.get('item_name') or item.get('itemName')
                if iname is None or (isinstance(iname, float) and pd.isna(iname)):
                    raise DataIntegrityError("OrderItem missing required 'name' (or item_name/itemName)", {"order_id": str(oid), "item_keys": list(item.keys())})
                qty = float(item.get('quantity', 1) or 1)
                line_total = float(item.get('price', 0) or 0)
                unit_price = (line_total / qty) if qty else line_total
                rev = line_total
                parsed_rows.append({
                    "bill_date": bd,
                    "order_id": str(oid),
                    "item_name": str(iname),
                    "quantity": qty,
                    "unit_price": unit_price,
                    "total_revenue": rev
                })

        if not parsed_rows:
            crash_report("titan_sales_parser", "Pre-Validation: 0 parsed rows; refusing WRITE_TRUNCATE", {"raw_rows": len(raw_data)}, None)

        df = pd.DataFrame(parsed_rows)
        df = df.dropna(subset=['bill_date', 'order_id', 'item_name'])
        if df.empty:
            crash_report("titan_sales_parser", "Pre-Validation: 0 rows after dropna; refusing WRITE_TRUNCATE", {"parsed_rows": len(parsed_rows)}, None)

        table_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_items_parsed"
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        job = bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result(timeout=None)
        print(f"[OK] SUCCESS: {len(df)} line-items parsed into 'sales_items_parsed'.")

    except KeyboardInterrupt:
        print("\n\nPARSER INTERRUPTED BY USER")
        sys.exit(0)
    except DataIntegrityError:
        raise


if __name__ == "__main__":
    try:
        parse_sales_json()
    except DataIntegrityError as e:
        append_crash_state("titan_sales_parser", str(e), getattr(e, 'state_of_data', {}))
        sys.exit(1)
