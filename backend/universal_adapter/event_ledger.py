"""
Event Ledger - Immutable Audit Trail System
============================================
"Never Delete, Always Append" - Event Sourcing for Data Integrity

This module implements:
1. Event logging for ALL data changes (create/update/delete/cancel)
2. Version tracking with fingerprints
3. Timestamp-based conflict resolution
4. Soft deletes (data is never truly deleted)

Every change in the system becomes an immutable event that can be:
- Audited (who changed what, when)
- Replayed (reconstruct state at any point in time)
- Analyzed (AI can understand business patterns)
"""

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
import os

# BigQuery client setup
try:
    from google.cloud import bigquery
    from google.api_core.exceptions import NotFound
    BQ_AVAILABLE = True
except ImportError:
    BQ_AVAILABLE = False

PROJECT_ID = "cafe-mellow-core-2026"
DATASET_ID = "cafe_operations"


class EventType(str, Enum):
    """Types of events that can occur on any entity"""
    CREATED = "created"           # New record
    UPDATED = "updated"           # Field(s) changed
    CANCELLED = "cancelled"       # Order/transaction cancelled
    DELETED = "deleted"           # Soft delete (marked as removed)
    RESTORED = "restored"         # Undeleted/reactivated
    AMENDED = "amended"           # Correction (e.g., wrong amount entered)
    VOIDED = "voided"             # Nullified (never happened)
    RECONCILED = "reconciled"     # Added by gap detection


class EntityType(str, Enum):
    """Types of business entities we track"""
    ORDER = "order"
    ORDER_ITEM = "order_item"
    PAYMENT = "payment"
    DISCOUNT = "discount"
    EXPENSE = "expense"
    PURCHASE = "purchase"
    RECIPE = "recipe"
    WASTAGE = "wastage"
    INVENTORY = "inventory"
    SUBSCRIPTION = "subscription"
    # Future entities
    EMPLOYEE = "employee"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"


class EventRecord(BaseModel):
    """Schema for an immutable event record"""
    event_id: str = Field(..., description="Unique event ID")
    entity_type: EntityType = Field(..., description="Type of entity")
    entity_id: str = Field(..., description="Business ID of the entity (e.g., order_id)")
    event_type: EventType = Field(..., description="What happened")
    event_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_timestamp: Optional[datetime] = Field(None, description="Timestamp from source system")
    version: int = Field(1, description="Version number for this entity")
    
    # Data fields
    data_before: Optional[Dict[str, Any]] = Field(None, description="State before change (for updates)")
    data_after: Dict[str, Any] = Field(..., description="State after change / current state")
    data_fingerprint: str = Field(..., description="Hash of data_after for deduplication")
    
    # Metadata
    source_system: str = Field(..., description="Origin system (petpooja, excel, zoho, etc.)")
    raw_log_id: Optional[str] = Field(None, description="Reference to raw_logs entry")
    changed_fields: Optional[List[str]] = Field(None, description="Which fields changed (for updates)")
    change_reason: Optional[str] = Field(None, description="Why the change happened")
    
    # Actor tracking (who made the change)
    actor_type: str = Field("system", description="system/user/api/reconciliation")
    actor_id: Optional[str] = Field(None, description="User ID if applicable")


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


def generate_fingerprint(data: Dict[str, Any]) -> str:
    """Generate a deterministic hash of data for deduplication"""
    # Sort keys for consistent hashing
    normalized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def generate_event_id(entity_type: str, entity_id: str, timestamp: datetime) -> str:
    """Generate unique event ID"""
    ts = timestamp.strftime("%Y%m%d%H%M%S%f")
    return f"evt_{entity_type}_{entity_id}_{ts}"


def detect_changes(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    """
    Compare two data dictionaries and return:
    1. List of changed field names
    2. Dict of {field: {"old": x, "new": y}}
    """
    changed_fields = []
    changes_detail = {}
    
    all_keys = set(old_data.keys()) | set(new_data.keys())
    
    for key in all_keys:
        old_val = old_data.get(key)
        new_val = new_data.get(key)
        
        # Normalize for comparison (handle type differences)
        old_str = json.dumps(old_val, sort_keys=True, default=str) if old_val is not None else None
        new_str = json.dumps(new_val, sort_keys=True, default=str) if new_val is not None else None
        
        if old_str != new_str:
            changed_fields.append(key)
            changes_detail[key] = {"old": old_val, "new": new_val}
    
    return changed_fields, changes_detail


def ensure_event_log_table() -> bool:
    """Create the event_log table if it doesn't exist"""
    client = _get_bq_client()
    if not client:
        return False
    
    table_id = f"{PROJECT_ID}.{DATASET_ID}.event_log"
    
    schema = [
        bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("entity_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("entity_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("event_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("event_timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("source_timestamp", "TIMESTAMP"),
        bigquery.SchemaField("version", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("data_before", "JSON"),
        bigquery.SchemaField("data_after", "JSON", mode="REQUIRED"),
        bigquery.SchemaField("data_fingerprint", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("source_system", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("raw_log_id", "STRING"),
        bigquery.SchemaField("changed_fields", "STRING", mode="REPEATED"),
        bigquery.SchemaField("change_reason", "STRING"),
        bigquery.SchemaField("actor_type", "STRING"),
        bigquery.SchemaField("actor_id", "STRING"),
    ]
    
    try:
        client.get_table(table_id)
        return True
    except NotFound:
        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="event_timestamp"
        )
        table.clustering_fields = ["entity_type", "entity_id"]
        client.create_table(table)
        print(f"[OK] Created event_log table")
        return True
    except Exception as e:
        print(f"[ERROR] Creating event_log: {e}")
        return False


def get_latest_version(entity_type: str, entity_id: str) -> Tuple[int, Optional[Dict], Optional[str]]:
    """
    Get the latest version number, data, and fingerprint for an entity.
    Returns: (version_number, data_after, fingerprint) or (0, None, None) if not found
    """
    client = _get_bq_client()
    if not client:
        return 0, None, None
    
    query = f"""
    SELECT version, data_after, data_fingerprint
    FROM `{PROJECT_ID}.{DATASET_ID}.event_log`
    WHERE entity_type = @entity_type AND entity_id = @entity_id
    ORDER BY version DESC, event_timestamp DESC
    LIMIT 1
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("entity_type", "STRING", entity_type),
            bigquery.ScalarQueryParameter("entity_id", "STRING", entity_id),
        ]
    )
    
    try:
        results = client.query(query, job_config=job_config).result()
        for row in results:
            data = json.loads(row.data_after) if isinstance(row.data_after, str) else row.data_after
            return row.version, data, row.data_fingerprint
        return 0, None, None
    except Exception as e:
        print(f"Error getting latest version: {e}")
        return 0, None, None


def log_event(
    entity_type: EntityType,
    entity_id: str,
    event_type: EventType,
    data_after: Dict[str, Any],
    source_system: str,
    data_before: Optional[Dict[str, Any]] = None,
    source_timestamp: Optional[datetime] = None,
    raw_log_id: Optional[str] = None,
    change_reason: Optional[str] = None,
    actor_type: str = "system",
    actor_id: Optional[str] = None,
    force_version: Optional[int] = None
) -> Optional[EventRecord]:
    """
    Log an event to the immutable ledger.
    
    This is the core function - EVERY data change goes through here.
    
    Returns the created EventRecord or None on failure.
    """
    client = _get_bq_client()
    if not client:
        print("[ERROR] BigQuery client not available for event logging")
        return None
    
    ensure_event_log_table()
    
    now = datetime.now(timezone.utc)
    fingerprint = generate_fingerprint(data_after)
    
    # Get current version and check for duplicates
    current_version, current_data, current_fingerprint = get_latest_version(
        entity_type.value, entity_id
    )
    
    # Duplicate detection: if fingerprint matches, skip
    if current_fingerprint == fingerprint and event_type == EventType.UPDATED:
        print(f"[SKIP] Duplicate data for {entity_type.value}:{entity_id} (same fingerprint)")
        return None
    
    # Calculate version
    if force_version is not None:
        version = force_version
    else:
        version = current_version + 1
    
    # Detect changed fields for updates
    changed_fields = None
    if event_type == EventType.UPDATED and current_data:
        changed_fields, _ = detect_changes(current_data, data_after)
        if not changed_fields:
            print(f"[SKIP] No actual changes for {entity_type.value}:{entity_id}")
            return None
        data_before = current_data
    
    # Generate event ID
    event_id = generate_event_id(entity_type.value, entity_id, now)
    
    # Create event record
    event = EventRecord(
        event_id=event_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        event_timestamp=now,
        source_timestamp=source_timestamp,
        version=version,
        data_before=data_before,
        data_after=data_after,
        data_fingerprint=fingerprint,
        source_system=source_system,
        raw_log_id=raw_log_id,
        changed_fields=changed_fields,
        change_reason=change_reason,
        actor_type=actor_type,
        actor_id=actor_id
    )
    
    # Insert to BigQuery
    table_id = f"{PROJECT_ID}.{DATASET_ID}.event_log"
    
    row = {
        "event_id": event.event_id,
        "entity_type": event.entity_type.value,
        "entity_id": event.entity_id,
        "event_type": event.event_type.value,
        "event_timestamp": event.event_timestamp.isoformat(),
        "source_timestamp": event.source_timestamp.isoformat() if event.source_timestamp else None,
        "version": event.version,
        "data_before": event.data_before,  # Pass dict directly for JSON type
        "data_after": event.data_after,    # Pass dict directly for JSON type
        "data_fingerprint": event.data_fingerprint,
        "source_system": event.source_system,
        "raw_log_id": event.raw_log_id,
        "changed_fields": event.changed_fields or [],
        "change_reason": event.change_reason,
        "actor_type": event.actor_type,
        "actor_id": event.actor_id
    }
    
    try:
        errors = client.insert_rows_json(table_id, [row])
        if errors:
            print(f"[ERROR] Inserting event: {errors}")
            return None
        print(f"[EVENT] {event_type.value} {entity_type.value}:{entity_id} v{version}")
        return event
    except Exception as e:
        print(f"[ERROR] Event logging failed: {e}")
        return None


def process_incoming_data(
    entity_type: EntityType,
    entity_id: str,
    incoming_data: Dict[str, Any],
    source_system: str,
    source_timestamp: Optional[datetime] = None,
    raw_log_id: Optional[str] = None,
    is_cancellation: bool = False,
    is_deletion: bool = False
) -> Tuple[EventType, Optional[EventRecord]]:
    """
    Smart processor that determines if incoming data is:
    - A new record (CREATED)
    - An update to existing (UPDATED)
    - A cancellation (CANCELLED)
    - A deletion (DELETED)
    
    Returns: (determined_event_type, event_record)
    """
    # Check if entity exists
    current_version, current_data, _ = get_latest_version(entity_type.value, entity_id)
    
    # Determine event type
    if is_cancellation:
        event_type = EventType.CANCELLED
        # Add cancellation marker to data
        incoming_data["_status"] = "cancelled"
        incoming_data["_cancelled_at"] = datetime.now(timezone.utc).isoformat()
    elif is_deletion:
        event_type = EventType.DELETED
        incoming_data["_status"] = "deleted"
        incoming_data["_deleted_at"] = datetime.now(timezone.utc).isoformat()
    elif current_version == 0:
        event_type = EventType.CREATED
        incoming_data["_status"] = "active"
    else:
        event_type = EventType.UPDATED
        # Check source timestamp for conflict resolution
        if source_timestamp and current_data:
            current_source_ts = current_data.get("_source_timestamp")
            if current_source_ts:
                current_ts = datetime.fromisoformat(current_source_ts.replace("Z", "+00:00"))
                if source_timestamp <= current_ts:
                    print(f"[SKIP] Stale update for {entity_type.value}:{entity_id} "
                          f"(incoming: {source_timestamp}, current: {current_ts})")
                    return event_type, None
    
    # Add source timestamp to data for future comparisons
    if source_timestamp:
        incoming_data["_source_timestamp"] = source_timestamp.isoformat()
    
    # Log the event
    event = log_event(
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        data_after=incoming_data,
        source_system=source_system,
        source_timestamp=source_timestamp,
        raw_log_id=raw_log_id
    )
    
    return event_type, event


def get_entity_history(entity_type: str, entity_id: str, limit: int = 100) -> List[Dict]:
    """Get the full history of an entity (all versions)"""
    client = _get_bq_client()
    if not client:
        return []
    
    query = f"""
    SELECT *
    FROM `{PROJECT_ID}.{DATASET_ID}.event_log`
    WHERE entity_type = @entity_type AND entity_id = @entity_id
    ORDER BY version DESC, event_timestamp DESC
    LIMIT {limit}
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("entity_type", "STRING", entity_type),
            bigquery.ScalarQueryParameter("entity_id", "STRING", entity_id),
        ]
    )
    
    try:
        results = client.query(query, job_config=job_config).result()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting entity history: {e}")
        return []


def get_latest_state(entity_type: str, entity_id: str) -> Optional[Dict]:
    """Get the current/latest state of an entity"""
    _, data, _ = get_latest_version(entity_type, entity_id)
    return data


def get_state_at_time(entity_type: str, entity_id: str, at_time: datetime) -> Optional[Dict]:
    """Get the state of an entity at a specific point in time"""
    client = _get_bq_client()
    if not client:
        return None
    
    query = f"""
    SELECT data_after
    FROM `{PROJECT_ID}.{DATASET_ID}.event_log`
    WHERE entity_type = @entity_type 
      AND entity_id = @entity_id
      AND event_timestamp <= @at_time
    ORDER BY version DESC, event_timestamp DESC
    LIMIT 1
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("entity_type", "STRING", entity_type),
            bigquery.ScalarQueryParameter("entity_id", "STRING", entity_id),
            bigquery.ScalarQueryParameter("at_time", "TIMESTAMP", at_time),
        ]
    )
    
    try:
        results = client.query(query, job_config=job_config).result()
        for row in results:
            return json.loads(row.data_after) if isinstance(row.data_after, str) else row.data_after
        return None
    except Exception as e:
        print(f"Error getting state at time: {e}")
        return None


# ============================================================
# BigQuery Views for "Latest State" Queries
# ============================================================

def create_latest_state_views() -> bool:
    """
    Create views that automatically show only the LATEST version of each entity.
    These are what the dashboard/reports should query.
    """
    client = _get_bq_client()
    if not client:
        return False
    
    views = {
        # Latest orders (excluding cancelled/deleted)
        "v_orders_latest": f"""
            CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET_ID}.v_orders_latest` AS
            WITH ranked AS (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY entity_id 
                        ORDER BY version DESC, event_timestamp DESC
                    ) as rn
                FROM `{PROJECT_ID}.{DATASET_ID}.event_log`
                WHERE entity_type = 'order'
            )
            SELECT 
                entity_id as order_id,
                event_type as last_event,
                version,
                event_timestamp as last_updated,
                JSON_VALUE(data_after, '$._status') as status,
                CAST(JSON_VALUE(data_after, '$.order_total') AS FLOAT64) as order_total,
                CAST(JSON_VALUE(data_after, '$.subtotal') AS FLOAT64) as subtotal,
                CAST(JSON_VALUE(data_after, '$.tax_amount') AS FLOAT64) as tax_amount,
                JSON_VALUE(data_after, '$.order_date') as order_date,
                JSON_VALUE(data_after, '$.customer_name') as customer_name,
                JSON_VALUE(data_after, '$.payment_status') as payment_status,
                source_system,
                data_after as full_data
            FROM ranked
            WHERE rn = 1
              AND JSON_VALUE(data_after, '$._status') NOT IN ('deleted', 'voided')
        """,
        
        # Latest expenses (excluding deleted)
        "v_expenses_latest": f"""
            CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET_ID}.v_expenses_latest` AS
            WITH ranked AS (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY entity_id 
                        ORDER BY version DESC, event_timestamp DESC
                    ) as rn
                FROM `{PROJECT_ID}.{DATASET_ID}.event_log`
                WHERE entity_type = 'expense'
            )
            SELECT 
                entity_id as expense_id,
                event_type as last_event,
                version,
                event_timestamp as last_updated,
                JSON_VALUE(data_after, '$._status') as status,
                CAST(JSON_VALUE(data_after, '$.amount') AS FLOAT64) as amount,
                JSON_VALUE(data_after, '$.category') as category,
                JSON_VALUE(data_after, '$.expense_date') as expense_date,
                JSON_VALUE(data_after, '$.description') as description,
                JSON_VALUE(data_after, '$.payment_mode') as payment_mode,
                source_system,
                data_after as full_data
            FROM ranked
            WHERE rn = 1
              AND JSON_VALUE(data_after, '$._status') != 'deleted'
        """,
        
        # Latest purchases (excluding deleted)
        "v_purchases_latest": f"""
            CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET_ID}.v_purchases_latest` AS
            WITH ranked AS (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY entity_id 
                        ORDER BY version DESC, event_timestamp DESC
                    ) as rn
                FROM `{PROJECT_ID}.{DATASET_ID}.event_log`
                WHERE entity_type = 'purchase'
            )
            SELECT 
                entity_id as purchase_id,
                event_type as last_event,
                version,
                event_timestamp as last_updated,
                JSON_VALUE(data_after, '$._status') as status,
                CAST(JSON_VALUE(data_after, '$.total_amount') AS FLOAT64) as total_amount,
                JSON_VALUE(data_after, '$.vendor_name') as vendor_name,
                JSON_VALUE(data_after, '$.purchase_date') as purchase_date,
                JSON_VALUE(data_after, '$.category') as category,
                source_system,
                data_after as full_data
            FROM ranked
            WHERE rn = 1
              AND JSON_VALUE(data_after, '$._status') != 'deleted'
        """,
        
        # All changes in last 24 hours (for monitoring)
        "v_recent_changes": f"""
            CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET_ID}.v_recent_changes` AS
            SELECT 
                event_id,
                entity_type,
                entity_id,
                event_type,
                event_timestamp,
                version,
                changed_fields,
                change_reason,
                source_system,
                actor_type,
                actor_id
            FROM `{PROJECT_ID}.{DATASET_ID}.event_log`
            WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
            ORDER BY event_timestamp DESC
        """,
        
        # Cancelled orders (for reporting)
        "v_orders_cancelled": f"""
            CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET_ID}.v_orders_cancelled` AS
            SELECT 
                entity_id as order_id,
                event_timestamp as cancelled_at,
                CAST(JSON_VALUE(data_after, '$.order_total') AS FLOAT64) as order_total,
                JSON_VALUE(data_after, '$.order_date') as order_date,
                change_reason as cancellation_reason,
                source_system
            FROM `{PROJECT_ID}.{DATASET_ID}.event_log`
            WHERE entity_type = 'order'
              AND event_type = 'cancelled'
            ORDER BY event_timestamp DESC
        """
    }
    
    try:
        for view_name, view_sql in views.items():
            client.query(view_sql).result()
            print(f"[OK] Created view: {view_name}")
        return True
    except Exception as e:
        print(f"[ERROR] Creating views: {e}")
        return False


# ============================================================
# Summary Statistics for AI Analysis
# ============================================================

def get_change_summary(
    entity_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get summary statistics of changes for AI to understand business patterns.
    """
    client = _get_bq_client()
    if not client:
        return {}
    
    where_clauses = ["1=1"]
    params = []
    
    if entity_type:
        where_clauses.append("entity_type = @entity_type")
        params.append(bigquery.ScalarQueryParameter("entity_type", "STRING", entity_type))
    
    if start_time:
        where_clauses.append("event_timestamp >= @start_time")
        params.append(bigquery.ScalarQueryParameter("start_time", "TIMESTAMP", start_time))
    
    if end_time:
        where_clauses.append("event_timestamp <= @end_time")
        params.append(bigquery.ScalarQueryParameter("end_time", "TIMESTAMP", end_time))
    
    where_sql = " AND ".join(where_clauses)
    
    query = f"""
    SELECT 
        entity_type,
        event_type,
        COUNT(*) as event_count,
        COUNT(DISTINCT entity_id) as unique_entities,
        MIN(event_timestamp) as first_event,
        MAX(event_timestamp) as last_event
    FROM `{PROJECT_ID}.{DATASET_ID}.event_log`
    WHERE {where_sql}
    GROUP BY entity_type, event_type
    ORDER BY entity_type, event_count DESC
    """
    
    job_config = bigquery.QueryJobConfig(query_parameters=params) if params else None
    
    try:
        results = client.query(query, job_config=job_config).result()
        
        summary = {
            "by_entity": {},
            "totals": {"events": 0, "unique_entities": 0}
        }
        
        for row in results:
            entity = row.entity_type
            if entity not in summary["by_entity"]:
                summary["by_entity"][entity] = {"events": {}, "total": 0}
            
            summary["by_entity"][entity]["events"][row.event_type] = row.event_count
            summary["by_entity"][entity]["total"] += row.event_count
            summary["totals"]["events"] += row.event_count
        
        return summary
    except Exception as e:
        print(f"Error getting change summary: {e}")
        return {}
