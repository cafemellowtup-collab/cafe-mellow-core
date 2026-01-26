"""
TITAN Evolution Pillar: Self-Storage & Evolution
Manages dev_evolution_log: ensures table exists, logs logic gaps, and serves Evolution Lab.
"""
from datetime import datetime
import uuid
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
from google.cloud.bigquery import SchemaField

# Table schema: id, timestamp, user_query, logic_gap_detected, suggested_feature_specification, development_status
EVOLUTION_SCHEMA = [
    SchemaField("id", "STRING", mode="NULLABLE"),
    SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("user_query", "STRING", mode="NULLABLE"),
    SchemaField("logic_gap_detected", "STRING", mode="NULLABLE"),
    SchemaField("suggested_feature_specification", "STRING", mode="NULLABLE"),
    SchemaField("development_status", "STRING", mode="NULLABLE"),  # proposed, authorized, in_progress, complete
]


def _table_id(s):
    return f"{s.PROJECT_ID}.{s.DATASET_ID}.{getattr(s, 'TABLE_DEV_EVOLUTION', 'dev_evolution_log')}"


def ensure_dev_evolution_table(client, s=None):
    """
    Verify dev_evolution_log exists in BigQuery. If not, create it.
    Returns: (exists: bool, created: bool)
    """
    s = s or settings
    table_id = _table_id(s)
    try:
        client.get_table(table_id)
        return True, False
    except NotFound:
        table = bigquery.Table(table_id, schema=EVOLUTION_SCHEMA)
        client.create_table(table)
        return True, True
    except Exception as e:
        raise RuntimeError(f"Evolution table check/create failed: {e}") from e


def log_evolution_pillar_suggestion(client, s, user_query: str, suggested_pillar_name: str, description: str = ""):
    """
    Log a suggested new pillar (e.g. "Automated Salary & Advance Reconciliation Pillar") to dev_evolution_log.
    For complex comparisons where the AI identifies that a dedicated tracking pillar would help.
    development_status is set to 'proposed'.
    """
    spec = f"Suggested: {suggested_pillar_name}. {description}".strip()
    return log_logic_gap(client, s, (user_query or "")[:2000], "Suggested new pillar for dedicated tracking.", spec[:8000])


def log_logic_gap(client, s, user_query: str, logic_gap_detected: str, suggested_feature_specification: str):
    """
    Log a detected logic gap / "I cannot answer" to dev_evolution_log.
    development_status is set to 'proposed'. Returns the created row id.
    """
    s = s or settings
    table_id = _table_id(s)
    row_id = str(uuid.uuid4())
    row = {
        "id": row_id,
        "timestamp": datetime.utcnow().isoformat(),
        "user_query": (user_query or "")[:8000],
        "logic_gap_detected": (logic_gap_detected or "")[:8000],
        "suggested_feature_specification": (suggested_feature_specification or "")[:8000],
        "development_status": "proposed",
    }
    errs = client.insert_rows_json(table_id, [row])
    if errs:
        raise RuntimeError(f"Failed to log to dev_evolution_log: {errs}")
    return row_id


def get_evolution_suggestions(client, s, status_filter=None, limit=50):
    """
    Read from dev_evolution_log. status_filter: None (all), 'proposed', 'authorized', etc.
    Returns list of dicts with id, timestamp, user_query, logic_gap_detected, suggested_feature_specification, development_status.
    """
    s = s or settings
    table_id = _table_id(s)
    where = ""
    if status_filter:
        where = f" WHERE development_status = @status "
    q = f"""
        SELECT id, timestamp, user_query, logic_gap_detected, suggested_feature_specification, development_status
        FROM `{table_id}` {where}
        ORDER BY timestamp DESC
        LIMIT {limit}
    """
    job_config = bigquery.QueryJobConfig()
    if status_filter:
        job_config.query_parameters = [bigquery.ScalarQueryParameter("status", "STRING", status_filter)]
    job = client.query(q, job_config=job_config)
    job.result(timeout=None)
    df = job.to_dataframe()
    return df.to_dict("records") if not df.empty else []


def update_development_status(client, s, row_id: str, new_status: str):
    """
    Update development_status for the row with the given id.
    """
    s = s or settings
    table_id = _table_id(s)
    q = f"""
        UPDATE `{table_id}`
        SET development_status = @new_status
        WHERE id = @id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("new_status", "STRING", new_status),
            bigquery.ScalarQueryParameter("id", "STRING", row_id or ""),
        ]
    )
    job = client.query(q, job_config=job_config)
    job.result(timeout=None)
    return True
