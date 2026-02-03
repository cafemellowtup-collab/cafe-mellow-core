"""
Universal Mapper - Fuzzy Column Matching & Event Transformation
================================================================
Phase 2E: Transform messy Excel/CSV rows into strict Universal Events.

Problem: Different sources use different column names:
- PetPooja: "Bill Date", "Net Amount", "Item Name"
- Tally: "Date", "Total", "Description"
- Custom: "created_at", "price", "product"

Solution: Fuzzy keyword matching to identify semantic columns.
"""

import re
import json
import uuid
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

import pandas as pd

from .polymorphic_ledger import UniversalEvent


@dataclass
class MappingResult:
    """Result of mapping raw data to Universal Events"""
    valid_events: List[UniversalEvent]
    failed_rows: List[Dict[str, Any]]
    column_mapping: Dict[str, str]
    stats: Dict[str, int]


class UniversalMapper:
    """
    Maps raw tabular data to Universal Events using fuzzy column matching.
    
    Usage:
        mapper = UniversalMapper()
        result = mapper.map_to_events(raw_data, tenant_id="cafe-001")
        print(f"Mapped {len(result.valid_events)} events")
    """
    
    TIMESTAMP_KEYWORDS = [
        "date", "time", "created", "timestamp", "datetime", 
        "bill_date", "order_date", "invoice_date", "trans_date",
        "created_at", "updated_at", "posted", "when"
    ]
    
    AMOUNT_KEYWORDS = [
        "amount", "total", "price", "net", "gross", "value",
        "net_amount", "total_amount", "bill_amount", "invoice_amount",
        "sum", "cost", "revenue", "sales", "payment", "paid"
    ]
    
    ENTITY_KEYWORDS = [
        "item", "product", "desc", "description", "name", "sku",
        "item_name", "product_name", "particulars", "detail",
        "customer", "vendor", "party", "account"
    ]
    
    REFERENCE_KEYWORDS = [
        "id", "order_id", "invoice_id", "bill_no", "invoice_no",
        "reference", "ref", "txn_id", "transaction_id", "order_no",
        "bill_id", "receipt_no", "voucher_no"
    ]
    
    CURRENCY_PATTERN = re.compile(r'[₹$€£¥,\s]')
    CURRENCY_PREFIX_PATTERN = re.compile(r'^(Rs\.?|INR|USD|EUR|GBP)\s*', re.IGNORECASE)
    
    @classmethod
    def map_to_events(
        cls,
        raw_data: List[Dict[str, Any]],
        tenant_id: str,
        source_system: str = "file_upload"
    ) -> Dict[str, Any]:
        """
        Map raw data rows to Universal Events.
        
        Args:
            raw_data: List of dictionaries (rows from DataFrame)
            tenant_id: Tenant identifier for multi-tenant isolation
            source_system: Origin of the data (e.g., "petpooja", "tally")
            
        Returns:
            Dictionary with valid_events, failed_rows, column_mapping, stats
        """
        if not raw_data:
            return {
                "valid_events": [],
                "failed_rows": [],
                "column_mapping": {},
                "stats": {"total": 0, "valid": 0, "failed": 0}
            }
        
        # Step 1: Identify columns
        columns = list(raw_data[0].keys())
        column_mapping = cls._identify_columns(columns)
        
        # Step 2: Process rows
        valid_events = []
        failed_rows = []
        
        for idx, row in enumerate(raw_data):
            try:
                event = cls._process_row(
                    row=row,
                    row_idx=idx,
                    column_mapping=column_mapping,
                    tenant_id=tenant_id,
                    source_system=source_system
                )
                
                if event:
                    valid_events.append(event)
                else:
                    failed_rows.append({
                        "row_idx": idx,
                        "row_data": row,
                        "reason": "Missing required fields (date or amount)"
                    })
                    
            except Exception as e:
                failed_rows.append({
                    "row_idx": idx,
                    "row_data": row,
                    "reason": f"Processing error: {str(e)}"
                })
        
        return {
            "valid_events": valid_events,
            "failed_rows": failed_rows,
            "column_mapping": column_mapping,
            "stats": {
                "total": len(raw_data),
                "valid": len(valid_events),
                "failed": len(failed_rows)
            }
        }
    
    @classmethod
    def _identify_columns(cls, columns: List[str]) -> Dict[str, str]:
        """
        Identify semantic meaning of columns using fuzzy keyword matching.
        
        Returns:
            Dict mapping semantic roles to actual column names
        """
        mapping = {
            "timestamp_col": None,
            "amount_col": None,
            "entity_col": None,
            "reference_col": None
        }
        
        columns_lower = {col: col.lower().replace(" ", "_").replace("-", "_") for col in columns}
        
        # Find timestamp column
        for col, col_normalized in columns_lower.items():
            for keyword in cls.TIMESTAMP_KEYWORDS:
                if keyword in col_normalized or col_normalized in keyword:
                    mapping["timestamp_col"] = col
                    break
            if mapping["timestamp_col"]:
                break
        
        # Find amount column
        for col, col_normalized in columns_lower.items():
            for keyword in cls.AMOUNT_KEYWORDS:
                if keyword in col_normalized or col_normalized in keyword:
                    mapping["amount_col"] = col
                    break
            if mapping["amount_col"]:
                break
        
        # Find entity column
        for col, col_normalized in columns_lower.items():
            if col == mapping["timestamp_col"] or col == mapping["amount_col"]:
                continue
            for keyword in cls.ENTITY_KEYWORDS:
                if keyword in col_normalized or col_normalized in keyword:
                    mapping["entity_col"] = col
                    break
            if mapping["entity_col"]:
                break
        
        # Find reference column
        for col, col_normalized in columns_lower.items():
            if col in [mapping["timestamp_col"], mapping["amount_col"], mapping["entity_col"]]:
                continue
            for keyword in cls.REFERENCE_KEYWORDS:
                if keyword in col_normalized or col_normalized in keyword:
                    mapping["reference_col"] = col
                    break
            if mapping["reference_col"]:
                break
        
        return mapping
    
    @classmethod
    def _process_row(
        cls,
        row: Dict[str, Any],
        row_idx: int,
        column_mapping: Dict[str, str],
        tenant_id: str,
        source_system: str
    ) -> Optional[UniversalEvent]:
        """
        Process a single row into a UniversalEvent.
        """
        # Extract and clean timestamp
        timestamp = None
        timestamp_col = column_mapping.get("timestamp_col")
        if timestamp_col and timestamp_col in row:
            timestamp = cls._clean_timestamp(row[timestamp_col])
        
        # Extract and clean amount
        amount = None
        amount_col = column_mapping.get("amount_col")
        if amount_col and amount_col in row:
            amount = cls._clean_amount(row[amount_col])
        
        # Validation: Need at least timestamp OR amount
        if timestamp is None and amount is None:
            return None
        
        # Use current time if no timestamp found but amount exists
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        
        # Extract entity name
        entity_name = None
        entity_col = column_mapping.get("entity_col")
        if entity_col and entity_col in row:
            entity_name = str(row[entity_col]).strip() if row[entity_col] else None
        
        # Extract reference ID
        reference_id = None
        reference_col = column_mapping.get("reference_col")
        if reference_col and reference_col in row:
            reference_id = str(row[reference_col]).strip() if row[reference_col] else None
        
        # Pack remaining columns into meta_payload
        meta_cols = [c for c in row.keys() if c not in [
            timestamp_col, amount_col, entity_col, reference_col
        ]]
        meta_payload = {col: row[col] for col in meta_cols if row.get(col) is not None}
        
        # Generate event ID and schema fingerprint
        event_id = str(uuid.uuid4())
        schema_fingerprint = cls._generate_fingerprint(list(row.keys()))
        
        # Create UniversalEvent
        event = UniversalEvent(
            event_id=event_id,
            tenant_id=tenant_id,
            timestamp=timestamp,
            source_system=source_system,
            category="UNCATEGORIZED",
            sub_category="PENDING_CLASSIFICATION",
            confidence_score=0.0,
            ai_reasoning="Awaiting AI classification",
            amount=amount,
            entity_name=entity_name,
            reference_id=reference_id,
            rich_data=json.dumps(row, default=str),
            schema_fingerprint=schema_fingerprint,
            verified=False,
            raw_log_id=f"row_{row_idx}"
        )
        
        return event
    
    @classmethod
    def _clean_timestamp(cls, value: Any) -> Optional[str]:
        """
        Clean and normalize timestamp values.
        """
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None
        
        try:
            # Handle pandas Timestamp
            if hasattr(value, 'isoformat'):
                return value.isoformat()
            
            # Try parsing with pandas
            parsed = pd.to_datetime(value, errors='coerce')
            if pd.isna(parsed):
                return None
            return parsed.isoformat()
            
        except Exception:
            return None
    
    @classmethod
    def _clean_amount(cls, value: Any) -> Optional[float]:
        """
        Clean and normalize monetary amounts.
        Removes currency symbols (₹, $, etc.) and commas.
        """
        if value is None:
            return None
        
        try:
            # Already a number
            if isinstance(value, (int, float)):
                if pd.isna(value):
                    return None
                return float(value)
            
            # String processing
            str_value = str(value).strip()
            if not str_value:
                return None
            
            # Remove currency prefixes (Rs, INR, USD, etc.)
            cleaned = cls.CURRENCY_PREFIX_PATTERN.sub('', str_value)
            # Remove currency symbols and commas
            cleaned = cls.CURRENCY_PATTERN.sub('', cleaned)
            cleaned = cleaned.strip()
            
            if not cleaned:
                return None
            
            # Handle negative values in parentheses: (100) -> -100
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]
            
            return float(cleaned)
            
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def _generate_fingerprint(cls, columns: List[str]) -> str:
        """
        Generate a schema fingerprint for pattern matching.
        """
        sorted_cols = sorted([c.lower() for c in columns])
        fingerprint_str = "|".join(sorted_cols)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()[:16]
    
    @classmethod
    def events_to_dicts(cls, events: List[UniversalEvent]) -> List[Dict[str, Any]]:
        """
        Convert UniversalEvent objects to dictionaries for JSON serialization.
        """
        return [asdict(event) for event in events]
