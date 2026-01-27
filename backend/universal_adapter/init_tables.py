"""
Initialize BigQuery Tables for Universal Adapter
================================================
Creates all required tables for the Golden Schema if they don't exist.
"""

import os
from datetime import datetime


def _get_bq_client():
    """Get BigQuery client with ADC fallback"""
    try:
        from google.cloud import bigquery
        from pillars.config_vault import EffectiveSettings
        
        cfg = EffectiveSettings()
        key_file = getattr(cfg, "KEY_FILE", "service-key.json")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
        
        if os.path.exists(key_path):
            return bigquery.Client.from_service_account_json(key_path), cfg
        
        project_id = getattr(cfg, "PROJECT_ID", None) or os.environ.get("PROJECT_ID")
        return bigquery.Client(project=project_id) if project_id else bigquery.Client(), cfg
    except Exception as e:
        print(f"BigQuery client error: {e}")
        return None, None


def init_all_tables():
    """Initialize all required tables for Universal Adapter"""
    client, cfg = _get_bq_client()
    if not client:
        print("ERROR: BigQuery client not available")
        return False
    
    project_id = getattr(cfg, "PROJECT_ID", "")
    dataset_id = getattr(cfg, "DATASET_ID", "")
    
    tables = {
        "sales_orders_enhanced": """
            CREATE TABLE IF NOT EXISTS `{project}.{dataset}.sales_orders_enhanced` (
                bill_date DATE NOT NULL,
                order_id STRING NOT NULL,
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
                order_time STRING,
                delivery_partner STRING,
                customer_name STRING,
                customer_phone STRING,
                customer_email STRING,
                outlet_id STRING,
                waiter_name STRING,
                table_number STRING,
                raw_json STRING,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
            )
            PARTITION BY bill_date
            CLUSTER BY order_id
        """,
        
        "sales_order_items_enhanced": """
            CREATE TABLE IF NOT EXISTS `{project}.{dataset}.sales_order_items_enhanced` (
                bill_date DATE NOT NULL,
                order_id STRING NOT NULL,
                item_name STRING NOT NULL,
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
                is_cancelled BOOL DEFAULT FALSE,
                cancelled_reason STRING,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
            )
            PARTITION BY bill_date
            CLUSTER BY order_id
        """,
        
        "sales_order_payments": """
            CREATE TABLE IF NOT EXISTS `{project}.{dataset}.sales_order_payments` (
                bill_date DATE NOT NULL,
                order_id STRING NOT NULL,
                payment_method STRING NOT NULL,
                amount FLOAT64,
                status STRING,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
            )
            PARTITION BY bill_date
        """,
        
        "sales_order_discounts": """
            CREATE TABLE IF NOT EXISTS `{project}.{dataset}.sales_order_discounts` (
                bill_date DATE NOT NULL,
                order_id STRING NOT NULL,
                discount_name STRING,
                discount_type STRING,
                amount FLOAT64,
                reason STRING,
                coupon_code STRING,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
            )
            PARTITION BY bill_date
        """,
        
        "expenses": """
            CREATE TABLE IF NOT EXISTS `{project}.{dataset}.expenses` (
                expense_id STRING NOT NULL,
                expense_date DATE NOT NULL,
                category STRING,
                ledger_name STRING,
                main_category STRING,
                item_name STRING,
                amount FLOAT64,
                payment_mode STRING,
                staff_name STRING,
                remarks STRING,
                source STRING,
                source_file STRING,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
            )
            PARTITION BY expense_date
        """,
        
        "purchases": """
            CREATE TABLE IF NOT EXISTS `{project}.{dataset}.purchases` (
                purchase_id STRING NOT NULL,
                purchase_date DATE NOT NULL,
                vendor_name STRING,
                vendor_id STRING,
                item_name STRING,
                category STRING,
                quantity FLOAT64,
                unit STRING,
                unit_price FLOAT64,
                total_amount FLOAT64,
                payment_mode STRING,
                payment_status STRING,
                remarks STRING,
                source STRING,
                source_file STRING,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
            )
            PARTITION BY purchase_date
        """,
        
        "raw_logs": """
            CREATE TABLE IF NOT EXISTS `{project}.{dataset}.raw_logs` (
                log_id STRING NOT NULL,
                received_at TIMESTAMP NOT NULL,
                source_type STRING NOT NULL,
                source_identifier STRING,
                raw_payload STRING NOT NULL,
                content_type STRING,
                payload_hash STRING,
                status STRING DEFAULT 'pending',
                target_schema STRING,
                processed_at TIMESTAMP,
                error_message STRING,
                retry_count INT64 DEFAULT 0,
                metadata STRING
            )
            PARTITION BY DATE(received_at)
        """,
        
        "quarantine": """
            CREATE TABLE IF NOT EXISTS `{project}.{dataset}.quarantine` (
                quarantine_id STRING NOT NULL,
                raw_log_id STRING NOT NULL,
                quarantined_at TIMESTAMP NOT NULL,
                target_schema STRING NOT NULL,
                validation_errors STRING,
                ai_transformed_data STRING,
                ai_confidence FLOAT64,
                status STRING DEFAULT 'pending',
                reviewed_by STRING,
                reviewed_at TIMESTAMP,
                human_corrected_data STRING,
                correction_notes STRING
            )
            PARTITION BY DATE(quarantined_at)
        """,
        
        "schema_mappings": """
            CREATE TABLE IF NOT EXISTS `{project}.{dataset}.schema_mappings` (
                mapping_id STRING NOT NULL,
                source_identifier STRING NOT NULL,
                target_schema STRING NOT NULL,
                field_mappings STRING NOT NULL,
                transform_rules STRING,
                created_at TIMESTAMP NOT NULL,
                last_used_at TIMESTAMP,
                use_count INT64 DEFAULT 0,
                confidence FLOAT64 DEFAULT 1.0,
                created_by STRING DEFAULT 'ai'
            )
        """
    }
    
    results = {}
    for table_name, create_sql in tables.items():
        sql = create_sql.format(project=project_id, dataset=dataset_id)
        try:
            client.query(sql).result()
            results[table_name] = "OK"
            print(f"[OK] {table_name}")
        except Exception as e:
            error_msg = str(e)
            if "Already Exists" in error_msg:
                results[table_name] = "EXISTS"
                print(f"[EXISTS] {table_name}")
            else:
                results[table_name] = f"ERROR: {error_msg[:100]}"
                print(f"[ERROR] {table_name}: {error_msg[:100]}")
    
    return results


if __name__ == "__main__":
    print("Initializing Universal Adapter Tables...")
    print("=" * 50)
    results = init_all_tables()
    print("=" * 50)
    print("Done!")
