# -*- coding: utf-8 -*-
"""Create missing BigQuery tables for new features"""
from google.cloud import bigquery
import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__) + "/../")
sys.path.insert(0, project_root)

try:
    from pillars.config_vault import get_bq_config
    project_id, dataset_id = get_bq_config()
    import settings
    key_file = getattr(settings, "KEY_FILE", "service-key.json")
except:
    # Fallback to environment variables if config not available
    project_id = os.environ.get("PROJECT_ID", "")
    dataset_id = os.environ.get("DATASET_ID", "cafe_operations")
    key_file = "service-key.json"

key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
client = bigquery.Client.from_service_account_json(key_path)

print(f"Creating missing tables in {project_id}.{dataset_id}...\n")

# 1. system_knowledge_base (Metacognitive Learning)
create_knowledge_base = f"""
CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.system_knowledge_base` (
    id STRING,
    org_id STRING,
    location_id STRING,
    rule_type STRING,
    description STRING,
    created_by STRING,
    created_at TIMESTAMP,
    confidence_score FLOAT64,
    usage_count INT64,
    last_used_at TIMESTAMP,
    status STRING
)
"""

# 2. vision_analysis_log (Oracle Vision)
create_vision_log = f"""
CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.vision_analysis_log` (
    id STRING,
    org_id STRING,
    location_id STRING,
    analysis_type STRING,
    analysis_result STRING,
    created_at TIMESTAMP
)
"""

# 3. system_error_log (Error tracking)
create_error_log = f"""
CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.system_error_log` (
    id STRING,
    error_message STRING,
    error_stack STRING,
    component_stack STRING,
    timestamp TIMESTAMP,
    user_agent STRING
)
"""

tables_to_create = [
    ("system_knowledge_base", create_knowledge_base),
    ("vision_analysis_log", create_vision_log),
    ("system_error_log", create_error_log),
]

for table_name, sql in tables_to_create:
    try:
        print(f"Creating {table_name}...", end=" ")
        client.query(sql).result()
        print("OK")
    except Exception as e:
        if "Already Exists" in str(e):
            print("OK (already exists)")
        else:
            print(f"FAIL: {e}")

print("\nDone! Tables created successfully.")
