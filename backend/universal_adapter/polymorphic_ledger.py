"""
Polymorphic Event Ledger - The Universal Storage Engine
========================================================
Stores ALL business data in ONE unified table with AI-generated tags.

CORE PRINCIPLE: We don't create 1,000 tables. We create ONE smart table.

Schema Design:
- event_id: Unique identifier
- tenant_id: Multi-tenant isolation (for SaaS scale)
- timestamp: When the event occurred
- category: AI-classified primary concept
- sub_category: More specific classification
- amount: Standardized monetary value (for cross-analysis)
- rich_data: The full JSON payload
- confidence: AI confidence score
- verified: Human verification status

This enables "360 Analysis" because:
- All data is in one place
- AI tags make it queryable
- Cross-category correlations are possible
"""

import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

from .semantic_brain import (
    BusinessConcept, SubCategory, SemanticClassification,
    classify_data_sync
)


# =============================================================================
# Event Record Schema
# =============================================================================

@dataclass
class UniversalEvent:
    """
    Universal event record that stores any business data.
    """
    event_id: str
    tenant_id: str
    timestamp: str
    source_system: str
    
    # AI Classification
    category: str  # BusinessConcept value
    sub_category: str  # SubCategory value
    confidence_score: float
    ai_reasoning: str
    
    # Standardized Fields (for cross-analysis)
    amount: Optional[float]  # Money involved (if any)
    entity_name: Optional[str]  # Primary entity (customer, vendor, item name)
    reference_id: Optional[str]  # External reference (order_id, invoice_id, etc.)
    
    # The Rich Data
    rich_data: str  # JSON string of full payload
    schema_fingerprint: str  # For pattern matching
    
    # Verification
    verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    original_category: Optional[str] = None  # If human corrected
    
    # Metadata
    created_at: str = None
    raw_log_id: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


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
# Table Initialization
# =============================================================================

def init_universal_ledger():
    """
    Initialize the universal event ledger table.
    This is the ONE table that stores everything.
    """
    client, cfg = _get_bq_client()
    if not client:
        return False
    
    dataset = getattr(cfg, "BQ_DATASET", "cafe_operations")
    table_id = f"{client.project}.{dataset}.universal_ledger"
    
    schema = [
        {"name": "event_id", "field_type": "STRING", "mode": "REQUIRED"},
        {"name": "tenant_id", "field_type": "STRING", "mode": "REQUIRED"},
        {"name": "timestamp", "field_type": "TIMESTAMP", "mode": "REQUIRED"},
        {"name": "source_system", "field_type": "STRING", "mode": "REQUIRED"},

        # AI Classification
        {"name": "category", "field_type": "STRING", "mode": "REQUIRED"},
        {"name": "sub_category", "field_type": "STRING", "mode": "NULLABLE"},
        {"name": "confidence_score", "field_type": "FLOAT", "mode": "REQUIRED"},
        {"name": "ai_reasoning", "field_type": "STRING", "mode": "NULLABLE"},

        # Standardized Fields
        {"name": "amount", "field_type": "FLOAT", "mode": "NULLABLE"},
        {"name": "entity_name", "field_type": "STRING", "mode": "NULLABLE"},
        {"name": "reference_id", "field_type": "STRING", "mode": "NULLABLE"},

        # Rich Data
        {"name": "rich_data", "field_type": "STRING", "mode": "REQUIRED"},  # JSON
        {"name": "schema_fingerprint", "field_type": "STRING", "mode": "NULLABLE"},

        # Verification
        {"name": "verified", "field_type": "BOOLEAN", "mode": "REQUIRED"},
        {"name": "verified_by", "field_type": "STRING", "mode": "NULLABLE"},
        {"name": "verified_at", "field_type": "TIMESTAMP", "mode": "NULLABLE"},
        {"name": "original_category", "field_type": "STRING", "mode": "NULLABLE"},

        # Metadata
        {"name": "created_at", "field_type": "TIMESTAMP", "mode": "REQUIRED"},
        {"name": "raw_log_id", "field_type": "STRING", "mode": "NULLABLE"},
    ]
    
    try:
        from google.cloud import bigquery
        
        table = bigquery.Table(table_id, schema=[
            bigquery.SchemaField(**field) for field in schema
        ])
        
        # Partition by timestamp for efficient queries
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp"
        )
        
        # Cluster by tenant_id and category for multi-tenant queries
        table.clustering_fields = ["tenant_id", "category", "sub_category"]
        
        table = client.create_table(table, exists_ok=True)
        print(f"[OK] Universal Ledger initialized: {table_id}")
        return True
    except Exception as e:
        print(f"[WARN] Failed to init universal ledger: {e}")
        return False


def init_category_registry():
    """
    Initialize the category registry table.
    Tracks all categories (including AI-generated new ones).
    """
    client, cfg = _get_bq_client()
    if not client:
        return False
    
    dataset = getattr(cfg, "BQ_DATASET", "cafe_operations")
    table_id = f"{client.project}.{dataset}.category_registry"
    
    schema = [
        {"name": "category_id", "field_type": "STRING", "mode": "REQUIRED"},
        {"name": "tenant_id", "field_type": "STRING", "mode": "REQUIRED"},
        {"name": "category_name", "field_type": "STRING", "mode": "REQUIRED"},
        {"name": "parent_category", "field_type": "STRING", "mode": "NULLABLE"},
        {"name": "description", "field_type": "STRING", "mode": "NULLABLE"},
        {"name": "is_system", "field_type": "BOOLEAN", "mode": "REQUIRED"},  # Built-in vs AI-generated
        {"name": "is_active", "field_type": "BOOLEAN", "mode": "REQUIRED"},
        {"name": "sample_schema", "field_type": "STRING", "mode": "NULLABLE"},  # JSON schema
        {"name": "event_count", "field_type": "INTEGER", "mode": "NULLABLE"},
        {"name": "created_at", "field_type": "TIMESTAMP", "mode": "REQUIRED"},
        {"name": "created_by", "field_type": "STRING", "mode": "NULLABLE"},
    ]
    
    try:
        from google.cloud import bigquery
        
        table = bigquery.Table(table_id, schema=[
            bigquery.SchemaField(**field) for field in schema
        ])
        
        table = client.create_table(table, exists_ok=True)
        print(f"[OK] Category Registry initialized: {table_id}")
        return True
    except Exception as e:
        print(f"[WARN] Failed to init category registry: {e}")
        return False


def init_schema_patterns():
    """
    Initialize the schema patterns table.
    Caches learned data patterns for cost optimization.
    """
    client, cfg = _get_bq_client()
    if not client:
        return False
    
    dataset = getattr(cfg, "BQ_DATASET", "cafe_operations")
    table_id = f"{client.project}.{dataset}.schema_patterns"
    
    schema = [
        {"name": "pattern_id", "field_type": "STRING", "mode": "REQUIRED"},
        {"name": "fingerprint", "field_type": "STRING", "mode": "REQUIRED"},
        {"name": "tenant_id", "field_type": "STRING", "mode": "NULLABLE"},  # NULL = global pattern
        {"name": "source_system", "field_type": "STRING", "mode": "NULLABLE"},
        {"name": "category", "field_type": "STRING", "mode": "REQUIRED"},
        {"name": "sub_category", "field_type": "STRING", "mode": "NULLABLE"},
        {"name": "confidence_score", "field_type": "FLOAT", "mode": "REQUIRED"},
        {"name": "field_mapping", "field_type": "STRING", "mode": "NULLABLE"},  # JSON
        {"name": "sample_data", "field_type": "STRING", "mode": "NULLABLE"},  # JSON
        {"name": "hit_count", "field_type": "INTEGER", "mode": "REQUIRED"},
        {"name": "last_used", "field_type": "TIMESTAMP", "mode": "REQUIRED"},
        {"name": "created_at", "field_type": "TIMESTAMP", "mode": "REQUIRED"},
    ]
    
    try:
        from google.cloud import bigquery
        
        table = bigquery.Table(table_id, schema=[
            bigquery.SchemaField(**field) for field in schema
        ])
        
        table = client.create_table(table, exists_ok=True)
        print(f"[OK] Schema Patterns initialized: {table_id}")
        return True
    except Exception as e:
        print(f"[WARN] Failed to init schema patterns: {e}")
        return False


def init_all_universal_tables():
    """Initialize all Universal Brain tables"""
    results = {
        "universal_ledger": init_universal_ledger(),
        "category_registry": init_category_registry(),
        "schema_patterns": init_schema_patterns()
    }
    return results


# =============================================================================
# Event Storage
# =============================================================================

def store_universal_event(
    data: Dict[str, Any],
    tenant_id: str,
    source_system: str,
    classification: SemanticClassification,
    raw_log_id: Optional[str] = None
) -> Optional[str]:
    """
    Store data in the universal ledger with AI classification.
    
    Args:
        data: The raw data to store
        tenant_id: Tenant identifier for multi-tenant isolation
        source_system: Source of the data (petpooja, excel, api, etc.)
        classification: SemanticClassification from the AI brain
        raw_log_id: Optional reference to raw_logs entry
    
    Returns:
        event_id if successful, None otherwise
    """
    client, cfg = _get_bq_client()
    if not client:
        return None
    
    dataset = getattr(cfg, "BQ_DATASET", "cafe_operations")
    table_id = f"{client.project}.{dataset}.universal_ledger"
    
    # Generate event ID
    event_id = f"evt_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{uuid.uuid4().hex[:8]}"
    
    # Extract entity name (best guess at primary entity)
    entity_name = None
    for key in ["name", "customer_name", "item_name", "vendor_name", "employee_name", "title"]:
        if key in data and data[key]:
            entity_name = str(data[key])[:200]
            break
    
    # Extract reference ID
    reference_id = None
    for key in ["order_id", "orderID", "invoice_id", "bill_no", "ref", "id", "transaction_id"]:
        if key in data and data[key]:
            reference_id = str(data[key])[:100]
            break
    
    # Build event record
    event = UniversalEvent(
        event_id=event_id,
        tenant_id=tenant_id,
        timestamp=classification.extracted_date or datetime.utcnow().isoformat(),
        source_system=source_system,
        category=classification.primary_concept.value,
        sub_category=classification.sub_category.value,
        confidence_score=classification.confidence_score,
        ai_reasoning=classification.reasoning[:500] if classification.reasoning else None,
        amount=classification.extracted_amount,
        entity_name=entity_name,
        reference_id=reference_id,
        rich_data=json.dumps(data, default=str),
        schema_fingerprint=_compute_fingerprint(data),
        verified=not classification.requires_human_review,
        raw_log_id=raw_log_id
    )
    
    try:
        # Use SQL INSERT for immediate availability
        sql = f"""
        INSERT INTO `{table_id}` (
            event_id, tenant_id, timestamp, source_system,
            category, sub_category, confidence_score, ai_reasoning,
            amount, entity_name, reference_id,
            rich_data, schema_fingerprint,
            verified, verified_by, verified_at, original_category,
            created_at, raw_log_id
        ) VALUES (
            @event_id, @tenant_id, @timestamp, @source_system,
            @category, @sub_category, @confidence_score, @ai_reasoning,
            @amount, @entity_name, @reference_id,
            @rich_data, @schema_fingerprint,
            @verified, @verified_by, @verified_at, @original_category,
            @created_at, @raw_log_id
        )
        """
        
        from google.cloud import bigquery
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("event_id", "STRING", event.event_id),
                bigquery.ScalarQueryParameter("tenant_id", "STRING", event.tenant_id),
                bigquery.ScalarQueryParameter("timestamp", "TIMESTAMP", event.timestamp),
                bigquery.ScalarQueryParameter("source_system", "STRING", event.source_system),
                bigquery.ScalarQueryParameter("category", "STRING", event.category),
                bigquery.ScalarQueryParameter("sub_category", "STRING", event.sub_category),
                bigquery.ScalarQueryParameter("confidence_score", "FLOAT64", event.confidence_score),
                bigquery.ScalarQueryParameter("ai_reasoning", "STRING", event.ai_reasoning),
                bigquery.ScalarQueryParameter("amount", "FLOAT64", event.amount),
                bigquery.ScalarQueryParameter("entity_name", "STRING", event.entity_name),
                bigquery.ScalarQueryParameter("reference_id", "STRING", event.reference_id),
                bigquery.ScalarQueryParameter("rich_data", "STRING", event.rich_data),
                bigquery.ScalarQueryParameter("schema_fingerprint", "STRING", event.schema_fingerprint),
                bigquery.ScalarQueryParameter("verified", "BOOL", event.verified),
                bigquery.ScalarQueryParameter("verified_by", "STRING", event.verified_by),
                bigquery.ScalarQueryParameter("verified_at", "TIMESTAMP", event.verified_at),
                bigquery.ScalarQueryParameter("original_category", "STRING", event.original_category),
                bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", event.created_at),
                bigquery.ScalarQueryParameter("raw_log_id", "STRING", event.raw_log_id),
            ]
        )
        
        client.query(sql, job_config=job_config).result()
        print(f"[OK] Stored universal event: {event_id} [{event.category}/{event.sub_category}]")
        return event_id
        
    except Exception as e:
        print(f"[WARN] Failed to store event: {e}")
        return None


def _compute_fingerprint(data: Dict[str, Any]) -> str:
    """Compute schema fingerprint for pattern matching"""
    import hashlib
    
    structure = {}
    for key, value in data.items():
        if isinstance(value, dict):
            structure[key] = "object"
        elif isinstance(value, list):
            structure[key] = "array"
        elif isinstance(value, (int, float)):
            structure[key] = "number"
        elif isinstance(value, bool):
            structure[key] = "boolean"
        else:
            structure[key] = "string"
    
    structure_str = json.dumps(structure, sort_keys=True)
    return hashlib.md5(structure_str.encode()).hexdigest()[:16]


# =============================================================================
# Event Queries
# =============================================================================

def query_events(
    tenant_id: str,
    category: Optional[str] = None,
    sub_category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    verified_only: bool = False,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Query events from the universal ledger.
    
    Args:
        tenant_id: Tenant identifier (REQUIRED for isolation)
        category: Filter by category
        sub_category: Filter by sub-category
        start_date: Start date filter
        end_date: End date filter
        verified_only: Only return verified events
        limit: Maximum results
    
    Returns:
        List of event records
    """
    client, cfg = _get_bq_client()
    if not client:
        return []
    
    dataset = getattr(cfg, "BQ_DATASET", "cafe_operations")
    table_id = f"{client.project}.{dataset}.universal_ledger"
    
    # Build query with tenant isolation
    conditions = ["tenant_id = @tenant_id"]
    params = [("tenant_id", "STRING", tenant_id)]
    
    if category:
        conditions.append("category = @category")
        params.append(("category", "STRING", category))
    
    if sub_category:
        conditions.append("sub_category = @sub_category")
        params.append(("sub_category", "STRING", sub_category))
    
    if start_date:
        conditions.append("timestamp >= @start_date")
        params.append(("start_date", "TIMESTAMP", start_date))
    
    if end_date:
        conditions.append("timestamp <= @end_date")
        params.append(("end_date", "TIMESTAMP", end_date))
    
    if verified_only:
        conditions.append("verified = TRUE")
    
    sql = f"""
    SELECT *
    FROM `{table_id}`
    WHERE {' AND '.join(conditions)}
    ORDER BY timestamp DESC
    LIMIT {limit}
    """
    
    try:
        from google.cloud import bigquery
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(name, type_, value)
                for name, type_, value in params
            ]
        )
        
        result = client.query(sql, job_config=job_config).result()
        return [dict(row) for row in result]
    except Exception as e:
        print(f"Query error: {e}")
        return []


def get_category_summary(
    tenant_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get summary statistics by category.
    This is the "360 Analysis" foundation.
    """
    client, cfg = _get_bq_client()
    if not client:
        return {}
    
    dataset = getattr(cfg, "BQ_DATASET", "cafe_operations")
    table_id = f"{client.project}.{dataset}.universal_ledger"
    
    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND timestamp BETWEEN '{start_date}' AND '{end_date}'"
    
    sql = f"""
    SELECT 
        category,
        sub_category,
        COUNT(*) as event_count,
        SUM(CASE WHEN amount IS NOT NULL THEN amount ELSE 0 END) as total_amount,
        AVG(confidence_score) as avg_confidence,
        SUM(CASE WHEN verified THEN 1 ELSE 0 END) as verified_count,
        MIN(timestamp) as first_event,
        MAX(timestamp) as last_event
    FROM `{table_id}`
    WHERE tenant_id = @tenant_id {date_filter}
    GROUP BY category, sub_category
    ORDER BY event_count DESC
    """
    
    try:
        from google.cloud import bigquery
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("tenant_id", "STRING", tenant_id)
            ]
        )
        
        result = client.query(sql, job_config=job_config).result()
        
        summary = {"categories": [], "totals": {"events": 0, "amount": 0}}
        for row in result:
            summary["categories"].append(dict(row))
            summary["totals"]["events"] += row.event_count
            summary["totals"]["amount"] += row.total_amount or 0
        
        return summary
    except Exception as e:
        print(f"Summary error: {e}")
        return {}


def cross_category_analysis(
    tenant_id: str,
    category_a: str,
    category_b: str,
    time_window: str = "7d"
) -> Dict[str, Any]:
    """
    Analyze correlation between two categories.
    Example: "Sales" vs "Marketing" spending
    """
    client, cfg = _get_bq_client()
    if not client:
        return {}
    
    dataset = getattr(cfg, "BQ_DATASET", "cafe_operations")
    table_id = f"{client.project}.{dataset}.universal_ledger"
    
    sql = f"""
    WITH daily_a AS (
        SELECT 
            DATE(timestamp) as date,
            SUM(amount) as amount_a,
            COUNT(*) as count_a
        FROM `{table_id}`
        WHERE tenant_id = @tenant_id 
          AND category = @category_a
          AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        GROUP BY DATE(timestamp)
    ),
    daily_b AS (
        SELECT 
            DATE(timestamp) as date,
            SUM(amount) as amount_b,
            COUNT(*) as count_b
        FROM `{table_id}`
        WHERE tenant_id = @tenant_id 
          AND category = @category_b
          AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        GROUP BY DATE(timestamp)
    )
    SELECT 
        COALESCE(a.date, b.date) as date,
        a.amount_a,
        a.count_a,
        b.amount_b,
        b.count_b
    FROM daily_a a
    FULL OUTER JOIN daily_b b ON a.date = b.date
    ORDER BY date
    """
    
    try:
        from google.cloud import bigquery
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("tenant_id", "STRING", tenant_id),
                bigquery.ScalarQueryParameter("category_a", "STRING", category_a),
                bigquery.ScalarQueryParameter("category_b", "STRING", category_b),
            ]
        )
        
        result = client.query(sql, job_config=job_config).result()
        return {
            "category_a": category_a,
            "category_b": category_b,
            "daily_data": [dict(row) for row in result]
        }
    except Exception as e:
        print(f"Cross analysis error: {e}")
        return {}
