"""
Guard - The Validation & Quarantine System
==========================================
Phase 4 of the Universal Adapter.

CORE PRINCIPLE: Only perfect data enters the main database.
Failed records go to quarantine for human review.

Process:
1. Fetch processed data from refinery
2. Final validation against Golden Schema
3. PASS → Write to main BigQuery tables
4. FAIL → Write to quarantine table with errors
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from .golden_schema import (
    GoldenOrder, GoldenExpense, GoldenPurchase,
    validate_order, validate_expense, validate_purchase
)
from .refinery import TransformResult


# =============================================================================
# BigQuery Client
# =============================================================================

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


# =============================================================================
# Quarantine Operations
# =============================================================================

def quarantine_record(
    raw_log_id: str,
    target_schema: str,
    validation_errors: List[str],
    ai_transformed_data: Optional[Dict[str, Any]] = None,
    ai_confidence: Optional[float] = None
) -> Optional[str]:
    """
    Send a failed record to quarantine for human review.
    Returns quarantine_id if successful.
    """
    client, cfg = _get_bq_client()
    if not client:
        print("WARNING: Cannot quarantine - BigQuery not available")
        return None
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        table_id = f"{project_id}.{dataset_id}.quarantine"
        
        quarantine_id = f"quar_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(raw_log_id.encode()).hexdigest()[:8]}"
        errors_json = json.dumps(validation_errors).replace("'", "''")
        ai_data_json = json.dumps(ai_transformed_data, default=str).replace("'", "''") if ai_transformed_data else ""
        
        insert_sql = f"""
        INSERT INTO `{table_id}`
        (quarantine_id, raw_log_id, quarantined_at, target_schema, validation_errors, 
         ai_transformed_data, ai_confidence, status)
        VALUES (
            '{quarantine_id}',
            '{raw_log_id}',
            CURRENT_TIMESTAMP(),
            '{target_schema}',
            '{errors_json}',
            '{ai_data_json}',
            {ai_confidence if ai_confidence else 'NULL'},
            'pending'
        )
        """
        client.query(insert_sql).result()
        
        # Update raw_log status
        raw_logs_table = f"{project_id}.{dataset_id}.raw_logs"
        update_sql = f"""
        UPDATE `{raw_logs_table}`
        SET status = 'quarantined', error_message = '{errors_json[:500]}'
        WHERE log_id = '{raw_log_id}'
        """
        client.query(update_sql).result()
        
        return quarantine_id
    except Exception as e:
        print(f"Quarantine error: {e}")
        return None


def get_quarantined_records(status: str = "pending", limit: int = 50) -> List[Dict[str, Any]]:
    """Get quarantined records for review"""
    client, cfg = _get_bq_client()
    if not client:
        return []
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        table_id = f"{project_id}.{dataset_id}.quarantine"
        raw_logs_table = f"{project_id}.{dataset_id}.raw_logs"
        
        query = f"""
        SELECT 
            q.quarantine_id,
            q.raw_log_id,
            CAST(q.quarantined_at AS STRING) as quarantined_at,
            q.target_schema,
            q.validation_errors,
            q.ai_transformed_data,
            q.ai_confidence,
            q.status,
            r.source_type,
            r.source_identifier,
            r.raw_payload
        FROM `{table_id}` q
        LEFT JOIN `{raw_logs_table}` r ON q.raw_log_id = r.log_id
        WHERE q.status = '{status}'
        ORDER BY q.quarantined_at DESC
        LIMIT {limit}
        """
        result = list(client.query(query).result())
        
        return [
            {
                "quarantine_id": row.quarantine_id,
                "raw_log_id": row.raw_log_id,
                "quarantined_at": row.quarantined_at,
                "target_schema": row.target_schema,
                "validation_errors": json.loads(row.validation_errors) if row.validation_errors else [],
                "ai_transformed_data": json.loads(row.ai_transformed_data) if row.ai_transformed_data else None,
                "ai_confidence": row.ai_confidence,
                "status": row.status,
                "source_type": row.source_type,
                "source_identifier": row.source_identifier,
                "raw_payload": json.loads(row.raw_payload) if row.raw_payload else None
            }
            for row in result
        ]
    except Exception as e:
        print(f"Get quarantined error: {e}")
        return []


def approve_quarantined_record(
    quarantine_id: str,
    corrected_data: Dict[str, Any],
    reviewed_by: str = "human",
    correction_notes: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Approve a quarantined record with human corrections.
    This triggers re-validation and insertion into main DB.
    """
    client, cfg = _get_bq_client()
    if not client:
        return False, "BigQuery not available"
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        quarantine_table = f"{project_id}.{dataset_id}.quarantine"
        
        # Get the quarantine record
        query = f"""
        SELECT target_schema, raw_log_id
        FROM `{quarantine_table}`
        WHERE quarantine_id = '{quarantine_id}'
        """
        result = list(client.query(query).result())
        if not result:
            return False, "Quarantine record not found"
        
        target_schema = result[0].target_schema
        raw_log_id = result[0].raw_log_id
        
        # Validate the corrected data
        if target_schema == "order":
            is_valid, validated, errors = validate_order(corrected_data)
        elif target_schema == "expense":
            is_valid, validated, errors = validate_expense(corrected_data)
        elif target_schema == "purchase":
            is_valid, validated, errors = validate_purchase(corrected_data)
        else:
            return False, f"Unknown schema: {target_schema}"
        
        if not is_valid:
            return False, f"Corrected data still invalid: {errors}"
        
        # Write to main database
        success, write_error = write_to_main_db(validated, target_schema)
        if not success:
            return False, write_error
        
        # Update quarantine status
        corrected_json = json.dumps(corrected_data, default=str).replace("'", "''")
        notes_safe = (correction_notes or "").replace("'", "''")
        
        update_sql = f"""
        UPDATE `{quarantine_table}`
        SET status = 'approved',
            reviewed_by = '{reviewed_by}',
            reviewed_at = CURRENT_TIMESTAMP(),
            human_corrected_data = '{corrected_json}',
            correction_notes = '{notes_safe}'
        WHERE quarantine_id = '{quarantine_id}'
        """
        client.query(update_sql).result()
        
        # Update raw_log status
        raw_logs_table = f"{project_id}.{dataset_id}.raw_logs"
        update_raw_sql = f"""
        UPDATE `{raw_logs_table}`
        SET status = 'completed', processed_at = CURRENT_TIMESTAMP()
        WHERE log_id = '{raw_log_id}'
        """
        client.query(update_raw_sql).result()
        
        # Learn from the correction - save mapping
        _learn_from_correction(client, cfg, quarantine_id, corrected_data, target_schema)
        
        return True, None
    except Exception as e:
        return False, str(e)


def reject_quarantined_record(quarantine_id: str, reviewed_by: str = "human", reason: str = "") -> bool:
    """Reject a quarantined record (won't be processed)"""
    client, cfg = _get_bq_client()
    if not client:
        return False
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        quarantine_table = f"{project_id}.{dataset_id}.quarantine"
        
        reason_safe = reason.replace("'", "''")
        update_sql = f"""
        UPDATE `{quarantine_table}`
        SET status = 'rejected',
            reviewed_by = '{reviewed_by}',
            reviewed_at = CURRENT_TIMESTAMP(),
            correction_notes = '{reason_safe}'
        WHERE quarantine_id = '{quarantine_id}'
        """
        client.query(update_sql).result()
        return True
    except Exception as e:
        print(f"Reject error: {e}")
        return False


def _learn_from_correction(client, cfg, quarantine_id: str, corrected_data: Dict[str, Any], target_schema: str):
    """Learn from human correction to improve future mappings"""
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        quarantine_table = f"{project_id}.{dataset_id}.quarantine"
        raw_logs_table = f"{project_id}.{dataset_id}.raw_logs"
        mappings_table = f"{project_id}.{dataset_id}.schema_mappings"
        
        # Get original raw data
        query = f"""
        SELECT r.raw_payload, r.source_identifier
        FROM `{quarantine_table}` q
        JOIN `{raw_logs_table}` r ON q.raw_log_id = r.log_id
        WHERE q.quarantine_id = '{quarantine_id}'
        """
        result = list(client.query(query).result())
        if not result:
            return
        
        raw_payload = json.loads(result[0].raw_payload)
        source_identifier = result[0].source_identifier or "human_corrected"
        
        # Build field mappings from the correction
        field_mappings = {}
        for corrected_key, corrected_value in corrected_data.items():
            if corrected_value is None:
                continue
            # Find matching source field
            for raw_key, raw_value in raw_payload.items():
                if str(raw_value) == str(corrected_value):
                    field_mappings[corrected_key] = raw_key
                    break
        
        if not field_mappings:
            return
        
        # Save the learned mapping
        mapping_id = f"map_learned_{hashlib.md5(f'{source_identifier}_{target_schema}'.encode()).hexdigest()[:12]}"
        mappings_json = json.dumps(field_mappings).replace("'", "''")
        
        # Check if mapping exists
        check_query = f"""
        SELECT mapping_id FROM `{mappings_table}`
        WHERE source_identifier = '{source_identifier}' AND target_schema = '{target_schema}'
        """
        existing = list(client.query(check_query).result())
        
        if existing:
            # Update existing
            update_sql = f"""
            UPDATE `{mappings_table}`
            SET field_mappings = '{mappings_json}',
                last_used_at = CURRENT_TIMESTAMP(),
                confidence = 1.0,
                created_by = 'human'
            WHERE source_identifier = '{source_identifier}' AND target_schema = '{target_schema}'
            """
            client.query(update_sql).result()
        else:
            # Insert new
            insert_sql = f"""
            INSERT INTO `{mappings_table}`
            (mapping_id, source_identifier, target_schema, field_mappings, created_at, confidence, created_by)
            VALUES (
                '{mapping_id}',
                '{source_identifier}',
                '{target_schema}',
                '{mappings_json}',
                CURRENT_TIMESTAMP(),
                1.0,
                'human'
            )
            """
            client.query(insert_sql).result()
        
        print(f"✅ Learned mapping from human correction: {source_identifier} -> {target_schema}")
    except Exception as e:
        print(f"Learn from correction error: {e}")


# =============================================================================
# Write to Main Database
# =============================================================================

def write_to_main_db(validated_data, target_schema: str) -> Tuple[bool, Optional[str]]:
    """
    Write validated data to the main production tables.
    This is the final step - only perfect data reaches here.
    """
    client, cfg = _get_bq_client()
    if not client:
        return False, "BigQuery not available"
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        
        if target_schema == "order":
            return _write_order_to_db(client, project_id, dataset_id, validated_data)
        elif target_schema == "expense":
            return _write_expense_to_db(client, project_id, dataset_id, validated_data)
        elif target_schema == "purchase":
            return _write_purchase_to_db(client, project_id, dataset_id, validated_data)
        else:
            return False, f"Unknown schema: {target_schema}"
    except Exception as e:
        return False, str(e)


def _write_order_to_db(client, project_id: str, dataset_id: str, order: GoldenOrder) -> Tuple[bool, Optional[str]]:
    """Write order to sales_orders_enhanced table"""
    try:
        table_id = f"{project_id}.{dataset_id}.sales_orders_enhanced"
        
        # Escape strings
        def safe(val):
            if val is None:
                return "NULL"
            return f"'{str(val).replace(chr(39), chr(39)+chr(39))}'"
        
        # Delete existing (upsert pattern)
        delete_sql = f"""
        DELETE FROM `{table_id}`
        WHERE order_id = '{order.order_id}' AND bill_date = '{order.bill_date}'
        """
        client.query(delete_sql).result()
        
        # Insert order
        insert_sql = f"""
        INSERT INTO `{table_id}`
        (bill_date, order_id, order_status, order_total, subtotal, tax_amount,
         service_charge, delivery_charge, packing_charge, total_discount,
         coupon_codes, payment_mode, payment_status, order_type, delivery_partner,
         customer_name, customer_phone, customer_email, outlet_id, waiter_name,
         order_time, raw_json)
        VALUES (
            '{order.bill_date}',
            '{order.order_id}',
            {safe(order.order_status)},
            {order.order_total},
            {order.subtotal},
            {order.tax_amount},
            {order.service_charge},
            {order.delivery_charge},
            {order.packing_charge},
            {order.total_discount},
            {safe(order.coupon_codes)},
            {safe(order.payment_mode)},
            {safe(order.payment_status)},
            {safe(order.order_type)},
            {safe(order.delivery_partner)},
            {safe(order.customer_name)},
            {safe(order.customer_phone)},
            {safe(order.customer_email)},
            {safe(order.outlet_id)},
            {safe(order.waiter_name)},
            {safe(order.order_time)},
            {safe(order.raw_json)}
        )
        """
        client.query(insert_sql).result()
        
        # Write order items
        if order.items:
            items_table = f"{project_id}.{dataset_id}.sales_order_items_enhanced"
            
            # Delete existing items
            delete_items_sql = f"""
            DELETE FROM `{items_table}`
            WHERE order_id = '{order.order_id}' AND bill_date = '{order.bill_date}'
            """
            client.query(delete_items_sql).result()
            
            # Insert items
            for item in order.items:
                item_sql = f"""
                INSERT INTO `{items_table}`
                (bill_date, order_id, item_name, item_id, category, quantity,
                 unit_price, line_total, item_discount, tax_rate, variant,
                 addons, special_instructions, is_cancelled, cancelled_reason)
                VALUES (
                    '{order.bill_date}',
                    '{order.order_id}',
                    {safe(item.item_name)},
                    {safe(item.item_id)},
                    {safe(item.category)},
                    {item.quantity},
                    {item.unit_price},
                    {item.line_total},
                    {item.item_discount},
                    {item.tax_rate},
                    {safe(item.variant)},
                    {safe(item.addons)},
                    {safe(item.special_instructions)},
                    {item.is_cancelled},
                    {safe(item.cancelled_reason)}
                )
                """
                client.query(item_sql).result()
        
        return True, None
    except Exception as e:
        return False, str(e)


def _write_expense_to_db(client, project_id: str, dataset_id: str, expense: GoldenExpense) -> Tuple[bool, Optional[str]]:
    """Write expense to expenses table"""
    try:
        table_id = f"{project_id}.{dataset_id}.expenses"
        
        def safe(val):
            if val is None:
                return "NULL"
            return f"'{str(val).replace(chr(39), chr(39)+chr(39))}'"
        
        # Upsert pattern
        delete_sql = f"""
        DELETE FROM `{table_id}`
        WHERE expense_id = '{expense.expense_id}'
        """
        client.query(delete_sql).result()
        
        insert_sql = f"""
        INSERT INTO `{table_id}`
        (expense_id, expense_date, category, ledger_name, main_category,
         item_name, amount, payment_mode, staff_name, remarks)
        VALUES (
            '{expense.expense_id}',
            '{expense.expense_date}',
            {safe(expense.category)},
            {safe(expense.ledger_name)},
            {safe(expense.main_category)},
            {safe(expense.item_name)},
            {expense.amount},
            {safe(expense.payment_mode)},
            {safe(expense.staff_name)},
            {safe(expense.remarks)}
        )
        """
        client.query(insert_sql).result()
        return True, None
    except Exception as e:
        return False, str(e)


def _write_purchase_to_db(client, project_id: str, dataset_id: str, purchase: GoldenPurchase) -> Tuple[bool, Optional[str]]:
    """Write purchase to purchases table"""
    try:
        table_id = f"{project_id}.{dataset_id}.purchases"
        
        def safe(val):
            if val is None:
                return "NULL"
            return f"'{str(val).replace(chr(39), chr(39)+chr(39))}'"
        
        # Upsert pattern
        delete_sql = f"""
        DELETE FROM `{table_id}`
        WHERE purchase_id = '{purchase.purchase_id}'
        """
        client.query(delete_sql).result()
        
        insert_sql = f"""
        INSERT INTO `{table_id}`
        (purchase_id, purchase_date, vendor_name, vendor_id, item_name,
         category, quantity, unit, unit_price, total_amount,
         payment_mode, payment_status, remarks)
        VALUES (
            '{purchase.purchase_id}',
            '{purchase.purchase_date}',
            {safe(purchase.vendor_name)},
            {safe(purchase.vendor_id)},
            {safe(purchase.item_name)},
            {safe(purchase.category)},
            {purchase.quantity},
            {safe(purchase.unit)},
            {purchase.unit_price},
            {purchase.total_amount},
            {safe(purchase.payment_mode)},
            {safe(purchase.payment_status)},
            {safe(purchase.remarks)}
        )
        """
        client.query(insert_sql).result()
        return True, None
    except Exception as e:
        return False, str(e)


# =============================================================================
# Quarantine Stats
# =============================================================================

def get_quarantine_stats() -> Dict[str, Any]:
    """Get quarantine statistics"""
    client, cfg = _get_bq_client()
    if not client:
        return {"ok": False, "error": "Database not available"}
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        table_id = f"{project_id}.{dataset_id}.quarantine"
        
        query = f"""
        SELECT 
            status,
            target_schema,
            COUNT(*) as count
        FROM `{table_id}`
        GROUP BY status, target_schema
        """
        result = list(client.query(query).result())
        
        stats = {
            "by_status": {},
            "by_schema": {},
            "total": 0
        }
        
        for row in result:
            stats["by_status"][row.status] = stats["by_status"].get(row.status, 0) + row.count
            stats["by_schema"][row.target_schema] = stats["by_schema"].get(row.target_schema, 0) + row.count
            stats["total"] += row.count
        
        return {"ok": True, "stats": stats}
    except Exception as e:
        return {"ok": False, "error": str(e)}
