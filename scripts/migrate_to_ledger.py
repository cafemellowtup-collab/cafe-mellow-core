#!/usr/bin/env python3
"""
STRANGLER FIG PATTERN - Migrate existing data to Universal Ledger
Gradually moves data from legacy tables to the new ledger
"""
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

from google.cloud import bigquery
from pillars.config_vault import EffectiveSettings


def migrate_sales_to_ledger(client, cfg, org_id: str, location_id: str, limit: int = 1000):
    """Migrate sales data to Universal Ledger"""
    print(f"📊 Migrating sales data for org={org_id}, location={location_id}...")
    
    # Query existing sales
    query = f"""
    SELECT 
        order_id,
        bill_date,
        total_revenue,
        timestamp
    FROM `{cfg.PROJECT_ID}.{cfg.DATASET_ID}.sales_items_parsed`
    WHERE org_id = '{org_id}' AND location_id = '{location_id}'
    LIMIT {limit}
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        print("  ⚠️  No sales data found")
        return 0
    
    # Convert to ledger entries
    ledger_rows = []
    for _, row in df.iterrows():
        entry = {
            "id": str(uuid.uuid4()),
            "org_id": org_id,
            "location_id": location_id,
            "timestamp": row.get("timestamp", datetime.utcnow()).isoformat(),
            "entry_date": str(row["bill_date"]),
            "type": "SALE",
            "amount": float(row["total_revenue"]),
            "entry_source": "pos_petpooja",
            "source_id": str(row["order_id"]),
            "entity_id": None,
            "entity_name": None,
            "category": "Sales",
            "subcategory": None,
            "description": f"Sale Order #{row['order_id']}",
            "metadata": {},
            "is_verified": True,
            "is_locked": False,
            "created_by": "migration_script",
            "verified_by": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        ledger_rows.append(entry)
    
    # Insert into ledger
    table_id = f"{cfg.PROJECT_ID}.{cfg.DATASET_ID}.ledger_universal"
    errors = client.insert_rows_json(table_id, ledger_rows)
    
    if errors:
        print(f"  ❌ Errors: {errors[:5]}")
        return 0
    
    print(f"  ✅ Migrated {len(ledger_rows)} sales entries")
    return len(ledger_rows)


def migrate_expenses_to_ledger(client, cfg, org_id: str, location_id: str, limit: int = 1000):
    """Migrate expense data to Universal Ledger"""
    print(f"💰 Migrating expense data for org={org_id}, location={location_id}...")
    
    query = f"""
    SELECT 
        expense_date,
        amount,
        ledger_name,
        category,
        item_name,
        staff_name
    FROM `{cfg.PROJECT_ID}.{cfg.DATASET_ID}.expenses_master`
    WHERE org_id = '{org_id}' AND location_id = '{location_id}'
    LIMIT {limit}
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        print("  ⚠️  No expense data found")
        return 0
    
    ledger_rows = []
    for _, row in df.iterrows():
        entry = {
            "id": str(uuid.uuid4()),
            "org_id": org_id,
            "location_id": location_id,
            "timestamp": datetime.utcnow().isoformat(),
            "entry_date": str(row["expense_date"]),
            "type": "EXPENSE",
            "amount": float(row["amount"]),
            "entry_source": "google_drive",
            "source_id": None,
            "entity_id": None,
            "entity_name": str(row.get("staff_name", "")),
            "category": str(row.get("ledger_name") or row.get("category", "")),
            "subcategory": str(row.get("item_name", "")),
            "description": f"Expense: {row.get('item_name', 'N/A')}",
            "metadata": {},
            "is_verified": True,
            "is_locked": False,
            "created_by": "migration_script",
            "verified_by": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        ledger_rows.append(entry)
    
    table_id = f"{cfg.PROJECT_ID}.{cfg.DATASET_ID}.ledger_universal"
    errors = client.insert_rows_json(table_id, ledger_rows)
    
    if errors:
        print(f"  ❌ Errors: {errors[:5]}")
        return 0
    
    print(f"  ✅ Migrated {len(ledger_rows)} expense entries")
    return len(ledger_rows)


def main():
    """Run migration"""
    print("🔄 STRANGLER FIG PATTERN - Data Migration to Universal Ledger")
    print("="*60)
    
    cfg = EffectiveSettings()
    client = bigquery.Client.from_service_account_json(cfg.KEY_FILE)
    
    # TODO: Update these with actual org/location IDs
    org_id = input("Enter org_id (or press Enter to skip): ").strip()
    if not org_id:
        print("⚠️  Migration skipped. Update this script with your org_id and location_id.")
        return
    
    location_id = input("Enter location_id: ").strip()
    
    total_migrated = 0
    
    # Migrate sales
    total_migrated += migrate_sales_to_ledger(client, cfg, org_id, location_id)
    
    # Migrate expenses
    total_migrated += migrate_expenses_to_ledger(client, cfg, org_id, location_id)
    
    print("\n" + "="*60)
    print(f"✅ Migration Complete: {total_migrated} total entries migrated")
    print("="*60)
    print("\n💡 Next Steps:")
    print("  1. Verify migrated data in BigQuery")
    print("  2. Update sync scripts to write to ledger directly")
    print("  3. Gradually deprecate legacy tables")


if __name__ == "__main__":
    main()
