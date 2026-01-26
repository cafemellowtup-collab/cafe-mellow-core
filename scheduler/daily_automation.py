"""
Daily Automation Scheduler
Runs daily reports and task assignments automatically
"""
import schedule
import time
import subprocess
import sys
import os
from datetime import date, datetime, timedelta
from utils.daily_reporter import DailyReporter
from utils.task_manager import TaskManager
from google.cloud import bigquery
import settings
from pillars.config_vault import EffectiveSettings
from utils.ops_brief import generate_and_store as generate_and_store_ops_brief


def _get_bq_client_from_cfg(cfg: EffectiveSettings) -> bigquery.Client:
    key_file = getattr(cfg, "KEY_FILE", "service-key.json")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
    return bigquery.Client.from_service_account_json(key_path)


def _ensure_sales_intel_tables(client: bigquery.Client, cfg: EffectiveSettings):
    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    if not pid or not ds:
        raise RuntimeError("PROJECT_ID/DATASET_ID not configured")

    # Orders (1 row per order)
    client.query(
        f"""
        CREATE TABLE IF NOT EXISTS `{pid}.{ds}.sales_orders_enhanced` (
          bill_date DATE,
          order_id STRING,
          order_status STRING,
          order_total FLOAT64,
          subtotal FLOAT64,
          tax_amount FLOAT64,
          service_charge FLOAT64,
          delivery_charge FLOAT64,
          packing_charge FLOAT64,
          total_discount FLOAT64,
          coupon_codes STRING,
          payment_mode STRING,
          payment_status STRING,
          order_type STRING,
          delivery_partner STRING,
          customer_name STRING,
          customer_phone STRING,
          customer_email STRING,
          outlet_id STRING,
          waiter_name STRING,
          order_time STRING,
          raw_ingested_at TIMESTAMP,
          raw_row_hash STRING,
          raw_json STRING
        )
        PARTITION BY bill_date
        """
    ).result(timeout=None)

    # Items (1 row per item)
    client.query(
        f"""
        CREATE TABLE IF NOT EXISTS `{pid}.{ds}.sales_order_items_enhanced` (
          bill_date DATE,
          order_id STRING,
          item_name STRING,
          item_id STRING,
          category STRING,
          quantity FLOAT64,
          unit_price FLOAT64,
          line_total FLOAT64,
          item_discount FLOAT64,
          tax_rate FLOAT64,
          variant STRING,
          addons STRING,
          special_instructions STRING,
          is_cancelled BOOL,
          cancelled_reason STRING,
          raw_json STRING
        )
        PARTITION BY bill_date
        """
    ).result(timeout=None)

    # Payments (1 row per payment line)
    client.query(
        f"""
        CREATE TABLE IF NOT EXISTS `{pid}.{ds}.sales_order_payments` (
          bill_date DATE,
          order_id STRING,
          payment_method STRING,
          amount FLOAT64,
          status STRING,
          raw_json STRING
        )
        PARTITION BY bill_date
        """
    ).result(timeout=None)

    # Discounts (1 row per discount line)
    client.query(
        f"""
        CREATE TABLE IF NOT EXISTS `{pid}.{ds}.sales_order_discounts` (
          bill_date DATE,
          order_id STRING,
          discount_name STRING,
          discount_type STRING,
          amount FLOAT64,
          reason STRING,
          coupon_code STRING,
          raw_json STRING
        )
        PARTITION BY bill_date
        """
    ).result(timeout=None)


def run_sales_intelligence_etl(days_back: int = 2):
    """Incremental, idempotent ETL from sales_raw_layer -> normalized enhanced tables.

    - Fast: BigQuery-native MERGE, partition-pruned by bill_date.
    - Safe: rerunnable; updates existing rows, inserts missing.
    - Standalone: depends only on sales_raw_layer.
    """
    cfg = EffectiveSettings()
    client = _get_bq_client_from_cfg(cfg)
    _ensure_sales_intel_tables(client, cfg)

    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    end_dt = date.today()
    start_dt = end_dt - timedelta(days=max(0, int(days_back)))

    # Orders: upsert per (bill_date, order_id)
    client.query(
        f"""
        MERGE `{pid}.{ds}.sales_orders_enhanced` T
        USING (
          SELECT
            bill_date,
            CAST(order_id AS STRING) AS order_id,
            ANY_VALUE(
              COALESCE(
                CAST(JSON_VALUE(full_json, '$.Order.status') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.order_status') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.orderStatus') AS STRING)
              )
            ) AS order_status,
            ANY_VALUE(
              COALESCE(
                SAFE_CAST(JSON_VALUE(full_json, '$.Order.order_total') AS FLOAT64),
                SAFE_CAST(JSON_VALUE(full_json, '$.Order.total') AS FLOAT64),
                SAFE_CAST(JSON_VALUE(full_json, '$.Order.grand_total') AS FLOAT64),
                SAFE_CAST(JSON_VALUE(full_json, '$.Order.orderTotal') AS FLOAT64)
              )
            ) AS order_total,
            ANY_VALUE(
              COALESCE(
                SAFE_CAST(JSON_VALUE(full_json, '$.Order.subtotal') AS FLOAT64),
                SAFE_CAST(JSON_VALUE(full_json, '$.Order.sub_total') AS FLOAT64)
              )
            ) AS subtotal,
            ANY_VALUE(
              COALESCE(
                SAFE_CAST(JSON_VALUE(full_json, '$.Order.tax') AS FLOAT64),
                SAFE_CAST(JSON_VALUE(full_json, '$.Order.tax_amount') AS FLOAT64)
              )
            ) AS tax_amount,
            ANY_VALUE(SAFE_CAST(JSON_VALUE(full_json, '$.Order.service_charge') AS FLOAT64)) AS service_charge,
            ANY_VALUE(SAFE_CAST(JSON_VALUE(full_json, '$.Order.delivery_charge') AS FLOAT64)) AS delivery_charge,
            ANY_VALUE(SAFE_CAST(JSON_VALUE(full_json, '$.Order.packing_charge') AS FLOAT64)) AS packing_charge,
            ANY_VALUE(
              COALESCE(
                SAFE_CAST(JSON_VALUE(full_json, '$.Order.total_discount') AS FLOAT64),
                SAFE_CAST(JSON_VALUE(full_json, '$.Order.discount_total') AS FLOAT64)
              )
            ) AS total_discount,
            ANY_VALUE(
              COALESCE(
                CAST(JSON_VALUE(full_json, '$.Order.coupon_code') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.couponCode') AS STRING)
              )
            ) AS coupon_codes,
            ANY_VALUE(
              COALESCE(
                CAST(JSON_VALUE(full_json, '$.Order.payment_mode') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.paymentMode') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.payment_type') AS STRING)
              )
            ) AS payment_mode,
            ANY_VALUE(
              COALESCE(
                CAST(JSON_VALUE(full_json, '$.Order.payment_status') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.paymentStatus') AS STRING)
              )
            ) AS payment_status,
            ANY_VALUE(
              COALESCE(
                CAST(JSON_VALUE(full_json, '$.Order.order_type') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.orderType') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.delivery_type') AS STRING)
              )
            ) AS order_type,
            ANY_VALUE(
              COALESCE(
                CAST(JSON_VALUE(full_json, '$.Order.delivery_partner') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.deliveryPartner') AS STRING)
              )
            ) AS delivery_partner,
            ANY_VALUE(
              COALESCE(
                CAST(JSON_VALUE(full_json, '$.Order.customer_name') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.cust_name') AS STRING)
              )
            ) AS customer_name,
            ANY_VALUE(
              COALESCE(
                CAST(JSON_VALUE(full_json, '$.Order.customer_phone') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.cust_phone') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.phone') AS STRING)
              )
            ) AS customer_phone,
            ANY_VALUE(
              COALESCE(
                CAST(JSON_VALUE(full_json, '$.Order.customer_email') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.cust_email') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.email') AS STRING)
              )
            ) AS customer_email,
            ANY_VALUE(
              COALESCE(
                CAST(JSON_VALUE(full_json, '$.Order.outlet_id') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.outletId') AS STRING)
              )
            ) AS outlet_id,
            ANY_VALUE(
              COALESCE(
                CAST(JSON_VALUE(full_json, '$.Order.waiter_name') AS STRING),
                CAST(JSON_VALUE(full_json, '$.Order.waiterName') AS STRING)
              )
            ) AS waiter_name,
            ANY_VALUE(CAST(JSON_VALUE(full_json, '$.Order.order_time') AS STRING)) AS order_time,
            ANY_VALUE(ingested_at) AS raw_ingested_at,
            ANY_VALUE(row_hash) AS raw_row_hash,
            ANY_VALUE(full_json) AS raw_json
          FROM `{pid}.{ds}.sales_raw_layer`
          WHERE bill_date BETWEEN DATE('{start_dt}') AND DATE('{end_dt}')
          GROUP BY bill_date, CAST(order_id AS STRING)
        ) S
        ON T.bill_date = S.bill_date AND T.order_id = S.order_id
        WHEN MATCHED THEN UPDATE SET
          order_status = S.order_status,
          order_total = S.order_total,
          subtotal = S.subtotal,
          tax_amount = S.tax_amount,
          service_charge = S.service_charge,
          delivery_charge = S.delivery_charge,
          packing_charge = S.packing_charge,
          total_discount = S.total_discount,
          coupon_codes = S.coupon_codes,
          payment_mode = S.payment_mode,
          payment_status = S.payment_status,
          order_type = S.order_type,
          delivery_partner = S.delivery_partner,
          customer_name = S.customer_name,
          customer_phone = S.customer_phone,
          customer_email = S.customer_email,
          outlet_id = S.outlet_id,
          waiter_name = S.waiter_name,
          order_time = S.order_time,
          raw_ingested_at = S.raw_ingested_at,
          raw_row_hash = S.raw_row_hash,
          raw_json = S.raw_json
        WHEN NOT MATCHED THEN INSERT (
          bill_date, order_id, order_status, order_total, subtotal, tax_amount,
          service_charge, delivery_charge, packing_charge, total_discount, coupon_codes,
          payment_mode, payment_status, order_type, delivery_partner,
          customer_name, customer_phone, customer_email, outlet_id, waiter_name,
          order_time, raw_ingested_at, raw_row_hash, raw_json
        ) VALUES (
          S.bill_date, S.order_id, S.order_status, S.order_total, S.subtotal, S.tax_amount,
          S.service_charge, S.delivery_charge, S.packing_charge, S.total_discount, S.coupon_codes,
          S.payment_mode, S.payment_status, S.order_type, S.delivery_partner,
          S.customer_name, S.customer_phone, S.customer_email, S.outlet_id, S.waiter_name,
          S.order_time, S.raw_ingested_at, S.raw_row_hash, S.raw_json
        )
        """
    ).result(timeout=None)

    # Items: rebuild by bill_date window to keep it simple and safe.
    client.query(
        f"""
        DELETE FROM `{pid}.{ds}.sales_order_items_enhanced`
        WHERE bill_date BETWEEN DATE('{start_dt}') AND DATE('{end_dt}')
        """
    ).result(timeout=None)
    client.query(
        f"""
        INSERT INTO `{pid}.{ds}.sales_order_items_enhanced`
        (
          bill_date, order_id, item_name, item_id, category, quantity, unit_price,
          line_total, item_discount, tax_rate, variant, addons, special_instructions,
          is_cancelled, cancelled_reason, raw_json
        )
        SELECT
          r.bill_date,
          CAST(r.order_id AS STRING) AS order_id,
          CAST(JSON_VALUE(i, '$.name') AS STRING) AS item_name,
          COALESCE(CAST(JSON_VALUE(i, '$.item_id') AS STRING), CAST(JSON_VALUE(i, '$.itemId') AS STRING), '') AS item_id,
          COALESCE(CAST(JSON_VALUE(i, '$.category') AS STRING), CAST(JSON_VALUE(i, '$.category_name') AS STRING), '') AS category,
          COALESCE(SAFE_CAST(JSON_VALUE(i, '$.quantity') AS FLOAT64), 1) AS quantity,
          SAFE_CAST(JSON_VALUE(i, '$.price') AS FLOAT64) / NULLIF(COALESCE(SAFE_CAST(JSON_VALUE(i, '$.quantity') AS FLOAT64), 1), 0) AS unit_price,
          COALESCE(SAFE_CAST(JSON_VALUE(i, '$.price') AS FLOAT64), 0) AS line_total,
          SAFE_CAST(JSON_VALUE(i, '$.discount') AS FLOAT64) AS item_discount,
          SAFE_CAST(JSON_VALUE(i, '$.tax_rate') AS FLOAT64) AS tax_rate,
          COALESCE(CAST(JSON_VALUE(i, '$.variant') AS STRING), CAST(JSON_VALUE(i, '$.item_variant') AS STRING), '') AS variant,
          CAST(JSON_QUERY(i, '$.addons') AS STRING) AS addons,
          COALESCE(CAST(JSON_VALUE(i, '$.special_instructions') AS STRING), CAST(JSON_VALUE(i, '$.instructions') AS STRING), '') AS special_instructions,
          COALESCE(SAFE_CAST(JSON_VALUE(i, '$.is_cancelled') AS BOOL), SAFE_CAST(JSON_VALUE(i, '$.isCancelled') AS BOOL), FALSE) AS is_cancelled,
          COALESCE(CAST(JSON_VALUE(i, '$.cancelled_reason') AS STRING), CAST(JSON_VALUE(i, '$.cancelledReason') AS STRING), '') AS cancelled_reason,
          CAST(i AS STRING) AS raw_json
        FROM `{pid}.{ds}.sales_raw_layer` r,
        UNNEST(IFNULL(JSON_QUERY_ARRAY(r.full_json, '$.OrderItem'), [])) AS i
        WHERE r.bill_date BETWEEN DATE('{start_dt}') AND DATE('{end_dt}')
        """
    ).result(timeout=None)

    # Payments: rebuild by date window
    client.query(
        f"""
        DELETE FROM `{pid}.{ds}.sales_order_payments`
        WHERE bill_date BETWEEN DATE('{start_dt}') AND DATE('{end_dt}')
        """
    ).result(timeout=None)
    client.query(
        f"""
        INSERT INTO `{pid}.{ds}.sales_order_payments`
        (bill_date, order_id, payment_method, amount, status, raw_json)
        SELECT
          r.bill_date,
          CAST(r.order_id AS STRING) AS order_id,
          COALESCE(CAST(JSON_VALUE(p, '$.payment_method') AS STRING), CAST(JSON_VALUE(p, '$.method') AS STRING), '') AS payment_method,
          COALESCE(SAFE_CAST(JSON_VALUE(p, '$.amount') AS FLOAT64), SAFE_CAST(JSON_VALUE(p, '$.payment_amount') AS FLOAT64), 0) AS amount,
          COALESCE(CAST(JSON_VALUE(p, '$.status') AS STRING), '') AS status,
          CAST(p AS STRING) AS raw_json
        FROM `{pid}.{ds}.sales_raw_layer` r,
        UNNEST(IFNULL(JSON_QUERY_ARRAY(r.full_json, '$.Payment'), [])) AS p
        WHERE r.bill_date BETWEEN DATE('{start_dt}') AND DATE('{end_dt}')
        """
    ).result(timeout=None)

    # Discounts: rebuild by date window
    client.query(
        f"""
        DELETE FROM `{pid}.{ds}.sales_order_discounts`
        WHERE bill_date BETWEEN DATE('{start_dt}') AND DATE('{end_dt}')
        """
    ).result(timeout=None)
    client.query(
        f"""
        INSERT INTO `{pid}.{ds}.sales_order_discounts`
        (bill_date, order_id, discount_name, discount_type, amount, reason, coupon_code, raw_json)
        SELECT
          r.bill_date,
          CAST(r.order_id AS STRING) AS order_id,
          COALESCE(CAST(JSON_VALUE(d, '$.discount_name') AS STRING), CAST(JSON_VALUE(d, '$.name') AS STRING), '') AS discount_name,
          COALESCE(CAST(JSON_VALUE(d, '$.discount_type') AS STRING), CAST(JSON_VALUE(d, '$.type') AS STRING), '') AS discount_type,
          COALESCE(SAFE_CAST(JSON_VALUE(d, '$.discount_amount') AS FLOAT64), SAFE_CAST(JSON_VALUE(d, '$.amount') AS FLOAT64), 0) AS amount,
          COALESCE(CAST(JSON_VALUE(d, '$.reason') AS STRING), '') AS reason,
          COALESCE(CAST(JSON_VALUE(d, '$.coupon_code') AS STRING), CAST(JSON_VALUE(d, '$.couponCode') AS STRING), CAST(JSON_VALUE(d, '$.code') AS STRING), '') AS coupon_code,
          CAST(d AS STRING) AS raw_json
        FROM `{pid}.{ds}.sales_raw_layer` r,
        UNNEST(IFNULL(JSON_QUERY_ARRAY(r.full_json, '$.Discount'), [])) AS d
        WHERE r.bill_date BETWEEN DATE('{start_dt}') AND DATE('{end_dt}')
        """
    ).result(timeout=None)

    print(f"Sales intelligence ETL complete for {start_dt} -> {end_dt}")

def send_daily_report():
    """Send daily report via email"""
    try:
        client = bigquery.Client.from_service_account_json(settings.KEY_FILE)
        reporter = DailyReporter(client, settings)
        
        report = reporter.generate_daily_report()
        report_text = reporter.format_report_text(report)
        
        # Save report to file
        report_file = f"reports/daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
        os.makedirs("reports", exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"Daily report generated: {report_file}")
        
        # TODO: Send email if configured
        # email.send_report(report_text)
        
    except Exception as e:
        print(f"Error generating daily report: {e}")


def generate_ops_brief():
    """Generate and store the daily ops brief"""
    try:
        cfg = EffectiveSettings()
        key_file = getattr(cfg, "KEY_FILE", "service-key.json")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
        client = bigquery.Client.from_service_account_json(key_path)
        brief = generate_and_store_ops_brief(client, cfg)
        print(f"Ops brief generated for {brief.get('brief_date')}")
    except Exception as e:
        print(f"Error generating ops brief: {e}")

def assign_daily_tasks():
    """Assign tasks from alerts"""
    try:
        client = bigquery.Client.from_service_account_json(settings.KEY_FILE)
        task_manager = TaskManager(client, settings)
        
        # Get alerts from AI Sentinel
        query = f"""
            SELECT task_type, item_involved, description, priority
            FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.ai_task_queue`
            WHERE status = 'Pending'
            AND created_at >= CURRENT_DATE()
            LIMIT 10
        """
        alerts = client.query(query).to_dataframe()
        
        # Convert alerts to tasks
        for _, alert in alerts.iterrows():
            task_data = {
                'task_id': f"task_{datetime.now().strftime('%Y%m%d')}_{alert.name}",
                'task_title': alert['task_type'],
                'task_description': alert['description'],
                'priority': alert['priority'],
                'assigned_date': datetime.now().date().isoformat(),
                'status': 'Pending'
            }
            task_manager.create_task(task_data)
        
        print(f"Assigned {len(alerts)} tasks from alerts")
        
    except Exception as e:
        print(f"Error assigning tasks: {e}")

def followup_tasks():
    """Follow up on pending tasks"""
    try:
        client = bigquery.Client.from_service_account_json(settings.KEY_FILE)
        task_manager = TaskManager(client, settings)
        
        followup_tasks = task_manager.get_tasks_needing_followup()
        
        if followup_tasks:
            print(f"Following up on {len(followup_tasks)} tasks")
            # TODO: Send reminders
        
    except Exception as e:
        print(f"Error in followup: {e}")

def run_sync():
    """Run data sync"""
    try:
        print("Running data sync...")
        subprocess.run([sys.executable, "01_Data_Sync/sync_sales_raw.py"], timeout=600)
        subprocess.run([sys.executable, "01_Data_Sync/titan_sales_parser.py"], timeout=300)
        # Build the normalized, 360-degree sales intelligence tables.
        run_sales_intelligence_etl(days_back=2)
        print("Data sync complete")
    except Exception as e:
        print(f"Error in sync: {e}")

# Schedule tasks
schedule.every().day.at("06:00").do(run_sync)
schedule.every().day.at("06:30").do(generate_ops_brief)
schedule.every().day.at("07:00").do(send_daily_report)
schedule.every().day.at("08:00").do(assign_daily_tasks)
schedule.every().day.at("18:00").do(followup_tasks)

if __name__ == "__main__":
    print("TITAN Daily Automation Scheduler Started")
    print("Schedule:")
    print("- Data Sync: 6:00 AM daily")
    print("- Daily Report: 7:00 AM daily")
    print("- Task Assignment: 8:00 AM daily")
    print("- Task Follow-up: 6:00 PM daily")
    print("\nRunning... Press Ctrl+C to stop")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
