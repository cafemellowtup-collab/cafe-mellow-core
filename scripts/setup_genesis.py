#!/usr/bin/env python3
"""
GENESIS PROTOCOL - Setup Script
Creates all BigQuery tables for the Hexagonal Architecture
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from google.cloud import bigquery
from pillars.config_vault import EffectiveSettings


def setup_genesis_tables():
    """Create all Genesis Protocol tables in BigQuery"""
    print("🧬 GENESIS PROTOCOL - Setup Starting...")
    
    cfg = EffectiveSettings()
    client = bigquery.Client.from_service_account_json(cfg.KEY_FILE)
    
    project_id = cfg.PROJECT_ID
    dataset_id = cfg.DATASET_ID
    
    print(f"📊 Target: {project_id}.{dataset_id}")
    
    # Read SQL schema file
    schema_file = Path(__file__).parent.parent / "backend" / "schemas" / "bigquery_schemas.sql"
    
    with open(schema_file, "r", encoding="utf-8") as f:
        sql_script = f.read()
    
    # Replace placeholders
    sql_script = sql_script.replace("{PROJECT_ID}", project_id)
    sql_script = sql_script.replace("{DATASET_ID}", dataset_id)
    
    # Split into individual statements and filter out comments
    lines = sql_script.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove inline comments but keep the SQL
        if '--' in line:
            line = line.split('--')[0]
        cleaned_lines.append(line)
    
    sql_script = '\n'.join(cleaned_lines)
    statements = [s.strip() for s in sql_script.split(";") if s.strip() and len(s.strip()) > 10]
    
    print(f"\n📋 Executing {len(statements)} SQL statements...\n")
    
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements, 1):
        try:
            # Extract table name for logging
            table_name = "unknown"
            if "CREATE TABLE" in statement:
                parts = statement.split("`")
                if len(parts) >= 2:
                    table_name = parts[1].split(".")[-1]
            elif "CREATE OR REPLACE VIEW" in statement:
                parts = statement.split("`")
                if len(parts) >= 2:
                    table_name = parts[1].split(".")[-1]
            
            print(f"[{i}/{len(statements)}] Creating: {table_name}...", end=" ")
            
            client.query(statement).result()
            
            print("✅")
            success_count += 1
        
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")
            error_count += 1
    
    print("\n" + "="*60)
    print(f"✅ Success: {success_count}")
    print(f"❌ Errors: {error_count}")
    print("="*60)
    
    if error_count == 0:
        print("\n🎉 GENESIS PROTOCOL SETUP COMPLETE!")
        print("\n📚 Tables Created:")
        print("  - users (CITADEL)")
        print("  - roles (CITADEL)")
        print("  - entities (CITADEL)")
        print("  - ledger_universal (UNIVERSAL LEDGER)")
        print("  - data_quality_scores (CHAMELEON)")
        print("  - system_knowledge_base (META-COGNITIVE)")
        print("  - learned_strategies (META-COGNITIVE)")
        print("  - user_activity_log (DPDP COMPLIANCE)")
        print("\n🔍 Views Created:")
        print("  - v_daily_revenue")
        print("  - v_daily_expenses")
        print("  - v_profit_summary")
        print("\n🚀 Next Steps:")
        print("  1. Set CRON_SECRET in environment variables")
        print("  2. Configure R2 storage (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, etc.)")
        print("  3. Set up Google Cloud Scheduler for cron jobs")
        print("  4. Run migration to move existing data to Universal Ledger")
    else:
        print("\n⚠️  Some tables failed to create. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    setup_genesis_tables()
