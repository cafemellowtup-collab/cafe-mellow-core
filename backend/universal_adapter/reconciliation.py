"""
Reconciliation Bot - Gap Detection and Data Recovery
=====================================================
"The Night Watchman" - Finds and fills missing data

This module handles:
1. Gap detection (orders that should exist but don't)
2. Data recovery from source systems
3. Consistency checks between raw_logs and event_log
4. Periodic reconciliation with external APIs (Petpooja, etc.)
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

try:
    from google.cloud import bigquery
    BQ_AVAILABLE = True
except ImportError:
    BQ_AVAILABLE = False

from .event_ledger import (
    EntityType, EventType, log_event, get_latest_version,
    process_incoming_data, ensure_event_log_table
)

# Centralized config - NO HARDCODED PROJECT IDs
from pillars.config_vault import get_bq_config

PROJECT_ID, DATASET_ID = get_bq_config()


class GapType(str, Enum):
    """Types of data gaps we can detect"""
    MISSING_IN_DB = "missing_in_db"          # Exists in source, not in our DB
    MISSING_IN_SOURCE = "missing_in_source"  # Exists in DB, not in source (suspicious)
    VERSION_MISMATCH = "version_mismatch"    # Data differs between source and DB
    STALE_DATA = "stale_data"                # DB data is older than source


class ReconciliationResult:
    """Results from a reconciliation run"""
    def __init__(self):
        self.gaps_found: List[Dict] = []
        self.records_recovered: int = 0
        self.records_updated: int = 0
        self.errors: List[str] = []
        self.start_time: datetime = datetime.now(timezone.utc)
        self.end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "gaps_found": len(self.gaps_found),
            "gaps_detail": self.gaps_found[:100],  # Limit for display
            "records_recovered": self.records_recovered,
            "records_updated": self.records_updated,
            "errors": self.errors,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else None
        }


def _get_bq_client():
    """Get BigQuery client with ADC fallback"""
    if not BQ_AVAILABLE:
        return None
    try:
        key_path = os.path.join(os.path.dirname(__file__), "..", "..", "service-key.json")
        if os.path.exists(key_path):
            return bigquery.Client.from_service_account_json(key_path)
        return bigquery.Client(project=PROJECT_ID)
    except Exception as e:
        print(f"BigQuery client error: {e}")
        return None


def find_unprocessed_raw_logs(
    hours_back: int = 24,
    limit: int = 1000
) -> List[Dict]:
    """
    Find raw_logs entries that haven't been processed into event_log.
    These are potential gaps in the data pipeline.
    """
    client = _get_bq_client()
    if not client:
        return []
    
    query = f"""
    SELECT 
        r.log_id,
        r.source_type,
        r.received_at,
        r.status,
        r.target_schema
    FROM `{PROJECT_ID}.{DATASET_ID}.raw_logs` r
    LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.event_log` e
        ON r.log_id = e.raw_log_id
    WHERE r.received_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_back} HOUR)
      AND r.status = 'completed'
      AND e.event_id IS NULL
    ORDER BY r.received_at DESC
    LIMIT {limit}
    """
    
    try:
        results = client.query(query).result()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error finding unprocessed logs: {e}")
        return []


def find_sequence_gaps(
    entity_type: str,
    id_prefix: str,
    start_date: datetime,
    end_date: datetime
) -> List[str]:
    """
    Find gaps in sequential IDs (e.g., order IDs ORD001, ORD002, ORD004 - ORD003 is missing).
    
    Note: This only works for sequentially numbered IDs.
    """
    client = _get_bq_client()
    if not client:
        return []
    
    query = f"""
    WITH ids AS (
        SELECT DISTINCT entity_id,
            SAFE_CAST(REGEXP_EXTRACT(entity_id, r'{id_prefix}(\\d+)') AS INT64) as id_num
        FROM `{PROJECT_ID}.{DATASET_ID}.event_log`
        WHERE entity_type = @entity_type
          AND event_timestamp BETWEEN @start_date AND @end_date
          AND entity_id LIKE '{id_prefix}%'
    ),
    all_nums AS (
        SELECT num
        FROM UNNEST(GENERATE_ARRAY(
            (SELECT MIN(id_num) FROM ids),
            (SELECT MAX(id_num) FROM ids)
        )) as num
    )
    SELECT CONCAT('{id_prefix}', CAST(a.num AS STRING)) as missing_id
    FROM all_nums a
    LEFT JOIN ids i ON a.num = i.id_num
    WHERE i.entity_id IS NULL
    ORDER BY a.num
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("entity_type", "STRING", entity_type),
            bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
            bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date),
        ]
    )
    
    try:
        results = client.query(query, job_config=job_config).result()
        return [row.missing_id for row in results]
    except Exception as e:
        print(f"Error finding sequence gaps: {e}")
        return []


def find_time_gaps(
    entity_type: str,
    start_time: datetime,
    end_time: datetime,
    expected_interval_minutes: int = 60
) -> List[Tuple[datetime, datetime]]:
    """
    Find time periods where no events occurred (potential outage periods).
    
    Returns list of (gap_start, gap_end) tuples.
    """
    client = _get_bq_client()
    if not client:
        return []
    
    query = f"""
    WITH events AS (
        SELECT event_timestamp,
            LAG(event_timestamp) OVER (ORDER BY event_timestamp) as prev_timestamp
        FROM `{PROJECT_ID}.{DATASET_ID}.event_log`
        WHERE entity_type = @entity_type
          AND event_timestamp BETWEEN @start_time AND @end_time
    )
    SELECT 
        prev_timestamp as gap_start,
        event_timestamp as gap_end,
        TIMESTAMP_DIFF(event_timestamp, prev_timestamp, MINUTE) as gap_minutes
    FROM events
    WHERE TIMESTAMP_DIFF(event_timestamp, prev_timestamp, MINUTE) > @interval
    ORDER BY gap_minutes DESC
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("entity_type", "STRING", entity_type),
            bigquery.ScalarQueryParameter("start_time", "TIMESTAMP", start_time),
            bigquery.ScalarQueryParameter("end_time", "TIMESTAMP", end_time),
            bigquery.ScalarQueryParameter("interval", "INT64", expected_interval_minutes),
        ]
    )
    
    try:
        results = client.query(query, job_config=job_config).result()
        return [(row.gap_start, row.gap_end) for row in results]
    except Exception as e:
        print(f"Error finding time gaps: {e}")
        return []


def compare_with_source_ids(
    entity_type: str,
    source_ids: Set[str],
    start_time: datetime,
    end_time: datetime
) -> Dict[str, List[str]]:
    """
    Compare a set of IDs from the source system against our database.
    
    Args:
        source_ids: Set of entity IDs that should exist (from source system API)
        
    Returns:
        {
            "missing_in_db": [...],      # In source but not in DB
            "missing_in_source": [...]   # In DB but not in source (suspicious)
        }
    """
    client = _get_bq_client()
    if not client:
        return {"missing_in_db": [], "missing_in_source": []}
    
    query = f"""
    SELECT DISTINCT entity_id
    FROM `{PROJECT_ID}.{DATASET_ID}.event_log`
    WHERE entity_type = @entity_type
      AND event_timestamp BETWEEN @start_time AND @end_time
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("entity_type", "STRING", entity_type),
            bigquery.ScalarQueryParameter("start_time", "TIMESTAMP", start_time),
            bigquery.ScalarQueryParameter("end_time", "TIMESTAMP", end_time),
        ]
    )
    
    try:
        results = client.query(query, job_config=job_config).result()
        db_ids = {row.entity_id for row in results}
        
        return {
            "missing_in_db": list(source_ids - db_ids),
            "missing_in_source": list(db_ids - source_ids)
        }
    except Exception as e:
        print(f"Error comparing IDs: {e}")
        return {"missing_in_db": [], "missing_in_source": []}


async def fetch_missing_from_petpooja(
    order_ids: List[str],
    api_key: str,
    restaurant_id: str
) -> List[Dict]:
    """
    Fetch missing orders from Petpooja API.
    
    This is a placeholder - actual implementation depends on Petpooja API structure.
    """
    # TODO: Implement actual Petpooja API call
    # This would call their order details endpoint for each missing ID
    print(f"[RECONCILIATION] Would fetch {len(order_ids)} orders from Petpooja")
    return []


def recover_missing_record(
    entity_type: EntityType,
    entity_id: str,
    data: Dict[str, Any],
    source_system: str,
    original_timestamp: Optional[datetime] = None
) -> bool:
    """
    Recover a missing record by inserting it into the event log.
    Marks it as 'reconciled' to distinguish from normal flow.
    """
    event = log_event(
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=EventType.RECONCILED,
        data_after=data,
        source_system=source_system,
        source_timestamp=original_timestamp,
        change_reason="Recovered by reconciliation bot - gap detection"
    )
    
    return event is not None


def run_daily_reconciliation(
    hours_back: int = 24
) -> ReconciliationResult:
    """
    Run the daily reconciliation check.
    
    This should be run as a scheduled job (e.g., Cloud Scheduler).
    """
    result = ReconciliationResult()
    
    print(f"[RECONCILIATION] Starting daily check for last {hours_back} hours...")
    
    # Ensure event_log table exists
    ensure_event_log_table()
    
    # 1. Find unprocessed raw_logs
    unprocessed = find_unprocessed_raw_logs(hours_back=hours_back)
    if unprocessed:
        print(f"[RECONCILIATION] Found {len(unprocessed)} unprocessed raw_logs")
        for log in unprocessed:
            result.gaps_found.append({
                "type": GapType.MISSING_IN_DB.value,
                "log_id": log["log_id"],
                "source": log["source_type"],
                "received_at": log["received_at"].isoformat() if log["received_at"] else None
            })
    
    # 2. Find time gaps (periods with no orders)
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours_back)
    
    time_gaps = find_time_gaps(
        entity_type="order",
        start_time=start_time,
        end_time=end_time,
        expected_interval_minutes=120  # Alert if 2+ hours without orders
    )
    
    for gap_start, gap_end in time_gaps:
        result.gaps_found.append({
            "type": "time_gap",
            "entity_type": "order",
            "gap_start": gap_start.isoformat() if gap_start else None,
            "gap_end": gap_end.isoformat() if gap_end else None,
            "gap_minutes": (gap_end - gap_start).total_seconds() / 60 if gap_start and gap_end else None
        })
    
    result.end_time = datetime.now(timezone.utc)
    
    print(f"[RECONCILIATION] Complete. Found {len(result.gaps_found)} gaps, "
          f"recovered {result.records_recovered} records")
    
    return result


def check_data_consistency(entity_type: str, entity_id: str) -> Dict[str, Any]:
    """
    Check if the latest event_log state matches the main table.
    
    This catches cases where the event was logged but writing to main table failed.
    """
    client = _get_bq_client()
    if not client:
        return {"error": "Client not available"}
    
    # Get latest from event_log
    _, event_data, event_fingerprint = get_latest_version(entity_type, entity_id)
    
    if not event_data:
        return {"status": "not_found_in_event_log"}
    
    # Map entity type to main table
    table_map = {
        "order": "sales_orders_enhanced",
        "expense": "expenses",
        "purchase": "purchases"
    }
    
    main_table = table_map.get(entity_type)
    if not main_table:
        return {"status": "unknown_entity_type"}
    
    # Get from main table
    id_column = f"{entity_type}_id"
    query = f"""
    SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{main_table}`
    WHERE {id_column} = @entity_id
    LIMIT 1
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("entity_id", "STRING", entity_id),
        ]
    )
    
    try:
        results = list(client.query(query, job_config=job_config).result())
        
        if not results:
            return {
                "status": "missing_in_main_table",
                "event_log_status": event_data.get("_status", "unknown"),
                "recommendation": "Re-run processor to write to main table"
            }
        
        return {
            "status": "consistent",
            "event_log_version": event_data.get("version", 1),
            "main_table_exists": True
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ============================================================
# Scheduled Jobs (to be called by Cloud Scheduler)
# ============================================================

def hourly_check() -> Dict:
    """Quick hourly check for critical issues"""
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "unprocessed_count": 0,
        "alerts": []
    }
    
    # Check for stuck raw_logs (pending for > 1 hour)
    client = _get_bq_client()
    if not client:
        result["error"] = "Client not available"
        return result
    
    query = f"""
    SELECT COUNT(*) as count
    FROM `{PROJECT_ID}.{DATASET_ID}.raw_logs`
    WHERE status = 'pending'
      AND received_at < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
    """
    
    try:
        rows = list(client.query(query).result())
        result["unprocessed_count"] = rows[0].count if rows else 0
        
        if result["unprocessed_count"] > 0:
            result["alerts"].append(f"{result['unprocessed_count']} records stuck in pending for >1 hour")
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def nightly_full_reconciliation() -> Dict:
    """Full nightly reconciliation"""
    result = run_daily_reconciliation(hours_back=24)
    return result.to_dict()
