"""
BigQuery Schema for Universal Ledger
"""
from google.cloud import bigquery


LEDGER_SCHEMA_BQ = [
    bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("org_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("location_id", "STRING", mode="REQUIRED"),
    
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("entry_date", "DATE", mode="REQUIRED"),
    
    bigquery.SchemaField("type", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("amount", "NUMERIC", mode="REQUIRED"),
    
    bigquery.SchemaField("entry_source", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("source_id", "STRING", mode="NULLABLE"),
    
    bigquery.SchemaField("entity_id", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("entity_name", "STRING", mode="NULLABLE"),
    
    bigquery.SchemaField("category", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("subcategory", "STRING", mode="NULLABLE"),
    
    bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
    
    bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
    
    bigquery.SchemaField("is_verified", "BOOLEAN", mode="NULLABLE"),
    bigquery.SchemaField("is_locked", "BOOLEAN", mode="NULLABLE"),
    
    bigquery.SchemaField("created_by", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("verified_by", "STRING", mode="NULLABLE"),
    
    bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
]


def get_create_table_ddl(project_id: str, dataset_id: str) -> str:
    """Generate DDL for creating the ledger table"""
    return f"""
    CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.ledger_universal` (
        id STRING NOT NULL,
        org_id STRING NOT NULL,
        location_id STRING NOT NULL,
        
        timestamp TIMESTAMP NOT NULL,
        entry_date DATE NOT NULL,
        
        type STRING NOT NULL,
        amount NUMERIC NOT NULL,
        
        entry_source STRING NOT NULL,
        source_id STRING,
        
        entity_id STRING,
        entity_name STRING,
        
        category STRING,
        subcategory STRING,
        
        description STRING,
        
        metadata JSON,
        
        is_verified BOOL DEFAULT FALSE,
        is_locked BOOL DEFAULT FALSE,
        
        created_by STRING,
        verified_by STRING,
        
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
    )
    PARTITION BY DATE(entry_date)
    CLUSTER BY org_id, location_id, type;
    """
