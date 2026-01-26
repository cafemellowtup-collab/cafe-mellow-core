"""
Enhanced Sales Parser - Extracts ALL fields from Petpooja JSON.
TITAN-INTEGRITY: No silent failures. Missing required keys or API/BQ errors raise DataIntegrityError.
"""
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
    except Exception as e:
        return False, None, str(e)

is_valid, bq_client, error = validate_connection()
if not is_valid:
    print(f"ERROR: {error}")
    sys.exit(1)


def extract_all_fields(order_json, order_id, bill_date):
    """Extract ALL possible fields. Raises DataIntegrityError on invalid structure or missing required keys."""
    if order_json is None or (isinstance(order_json, str) and (not order_json or order_json.strip() == '')):
        return []
    if isinstance(order_json, str):
        try:
            order_data = json.loads(order_json)
        except json.JSONDecodeError as e:
            raise DataIntegrityError(f"Invalid JSON: {e}", {"order_id": order_id, "bill_date": str(bill_date)})
    else:
        order_data = order_json

    if order_data is None:
        return []
    if not isinstance(order_data, dict):
        raise DataIntegrityError("Order is not dict", {"order_id": order_id, "type": type(order_data).__name__})

    order_obj = order_data.get('Order') if isinstance(order_data, dict) else {}
    if not order_obj or not isinstance(order_obj, dict):
        return []

    order_info = {
        'order_id': order_id,
        'bill_date': bill_date,
        'order_date': order_obj.get('order_date', bill_date),
        'order_time': order_obj.get('order_time', ''),
        'customer_name': order_obj.get('customer_name', '') or order_obj.get('cust_name', ''),
        'customer_phone': order_obj.get('customer_phone', '') or order_obj.get('cust_phone', '') or order_obj.get('phone', ''),
        'customer_email': order_obj.get('customer_email', '') or order_obj.get('cust_email', '') or order_obj.get('email', ''),
        'table_number': order_obj.get('table_number', '') or order_obj.get('table_no', '') or order_obj.get('table', ''),
        'order_type': order_obj.get('order_type', '') or order_obj.get('orderType', '') or order_obj.get('delivery_type', ''),
        'delivery_partner': order_obj.get('delivery_partner', '') or order_obj.get('deliveryPartner', '') or order_obj.get('partner', ''),
        'order_status': order_obj.get('status', ''),
        'order_total': float(order_obj.get('order_total', 0) or order_obj.get('total', 0) or 0),
        'subtotal': float(order_obj.get('subtotal', 0) or order_obj.get('sub_total', 0) or 0),
        'tax_amount': float(order_obj.get('tax', 0) or order_obj.get('tax_amount', 0) or 0),
        'service_charge': float(order_obj.get('service_charge', 0) or order_obj.get('serviceCharge', 0) or 0),
        'delivery_charge': float(order_obj.get('delivery_charge', 0) or order_obj.get('deliveryCharge', 0) or 0),
        'packing_charge': float(order_obj.get('packing_charge', 0) or order_obj.get('packingCharge', 0) or 0),
        'payment_mode': order_obj.get('payment_mode', '') or order_obj.get('paymentMode', '') or order_obj.get('payment_type', ''),
        'payment_status': order_obj.get('payment_status', '') or order_obj.get('paymentStatus', ''),
        'advance_order': order_obj.get('advance_order', '') or order_obj.get('advanceOrder', '') or order_obj.get('memo_order', ''),
        'advance_order_date': order_obj.get('advance_order_date', '') or order_obj.get('advanceOrderDate', ''),
        'remarks': order_obj.get('remarks', '') or order_obj.get('note', '') or order_obj.get('special_instructions', ''),
        'outlet_id': order_obj.get('outlet_id', '') or order_obj.get('outletId', ''),
        'waiter_name': order_obj.get('waiter_name', '') or order_obj.get('waiterName', ''),
        'created_at': order_obj.get('created_at', '') or order_obj.get('createdAt', ''),
    }
    payments = order_data.get('Payment', []) or order_data.get('payments', []) or []
    if payments:
        order_info['payment_details'] = json.dumps([{"payment_method": p.get('payment_method',''), "payment_amount": float(p.get('amount',0) or 0), "payment_status": p.get('status','')} for p in payments if isinstance(p, dict)])
    discounts = order_data.get('Discount', []) or order_data.get('discounts', []) or []
    discount_total = 0
    discount_details = []
    coupon_codes = []
    for d in discounts:
        if isinstance(d, dict):
            discount_total += float(d.get('discount_amount',0) or d.get('amount',0) or 0)
            discount_details.append({"name": d.get('discount_name',''), "type": d.get('discount_type',''), "amount": float(d.get('discount_amount',0) or d.get('amount',0) or 0), "reason": d.get('reason',''), "coupon_code": d.get('coupon_code','') or d.get('couponCode','') or d.get('code','')})
            if d.get('coupon_code') or d.get('couponCode') or d.get('code'):
                coupon_codes.append(d.get('coupon_code') or d.get('couponCode') or d.get('code'))
    order_info['total_discount'] = discount_total
    order_info['discount_details'] = json.dumps(discount_details)
    order_info['coupon_codes'] = ', '.join(coupon_codes) if coupon_codes else ''

    items = order_data.get('OrderItem', []) or order_data.get('items', []) or []
    parsed_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        iname = item.get('name') or item.get('item_name') or item.get('itemName')
        if iname is None or (isinstance(iname, float) and pd.isna(iname)):
            raise DataIntegrityError("OrderItem missing required 'name' (or item_name/itemId)", {"order_id": order_id, "item_keys": list(item.keys())})
        qty = float(item.get('quantity', 1) or 1)
        line_total = float(item.get('price', 0) or 0)
        unit_price = (line_total / qty) if qty else line_total

        item_row = {**order_info,
            'item_name': str(iname),
            'item_id': str(item.get('item_id', '') or item.get('itemId', '')),
            'category': item.get('category', '') or item.get('category_name', ''),
            'quantity': qty,
            'unit_price': unit_price,
            'total_revenue': line_total,
            'item_discount': float(item.get('discount', 0) or item.get('item_discount', 0) or 0),
            'tax_rate': float(item.get('tax_rate', 0) or item.get('taxRate', 0) or 0),
            'variant': item.get('variant', '') or item.get('item_variant', ''),
            'addons': json.dumps(item.get('addons', [])) if item.get('addons') else '',
            'special_instructions': item.get('special_instructions', '') or item.get('instructions', ''),
            'is_cancelled': item.get('is_cancelled', False) or item.get('isCancelled', False),
            'cancelled_reason': item.get('cancelled_reason', '') or item.get('cancelledReason', ''),
        }
        parsed_items.append(item_row)
    return parsed_items


def parse_enhanced_sales():
    print("ENHANCED SALES PARSER: Extracting Complete Order Intelligence...")
    try:
        query = f"SELECT bill_date, order_id, full_json FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_raw_layer` ORDER BY bill_date DESC LIMIT 100000"
        try:
            job = bq_client.query(query)
            job.result(timeout=None)
            raw_data = job.to_dataframe()
        except NotFound:
            raise DataIntegrityError("sales_raw_layer not found. Run sync_sales_raw.py first.", {})
        except Exception as e:
            raise DataIntegrityError(f"Failed to fetch sales_raw_layer: {e}", {})

        if raw_data.empty:
            crash_report("enhanced_sales_parser", "Pre-Validation: sales_raw_layer is empty; refusing WRITE_TRUNCATE", {}, None)

        all_parsed_items = []
        for idx, row in raw_data.iterrows():
            items = extract_all_fields(row['full_json'], row['order_id'], row['bill_date'])
            all_parsed_items.extend(items)

        if not all_parsed_items:
            crash_report("enhanced_sales_parser", "Pre-Validation: 0 line items extracted; refusing WRITE_TRUNCATE", {"raw_rows": len(raw_data)}, None)

        df = pd.DataFrame(all_parsed_items)
        df = df.drop_duplicates(subset=['order_id', 'item_name', 'quantity', 'unit_price'], keep='first')

        table_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_enhanced"
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", autodetect=True)
        job = bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result(timeout=None)
        print(f"✓ SUCCESS: Saved {len(df)} enhanced line items to 'sales_enhanced'")

        simple_df = df[['bill_date', 'order_id', 'item_name', 'quantity', 'unit_price', 'total_revenue']].copy()
        simple_table_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_items_parsed"
        job2 = bq_client.load_table_from_dataframe(simple_df, simple_table_id, job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"))
        job2.result(timeout=None)
        print("✓ Also updated 'sales_items_parsed' for backward compatibility")

    except KeyboardInterrupt:
        print("\n\nPARSER INTERRUPTED BY USER")
        sys.exit(0)
    except DataIntegrityError:
        raise


if __name__ == "__main__":
    try:
        parse_enhanced_sales()
    except DataIntegrityError as e:
        append_crash_state("enhanced_sales_parser", str(e), getattr(e, 'state_of_data', {}))
        sys.exit(1)
