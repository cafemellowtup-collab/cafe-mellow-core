"""
Ledger Writer - Dual Mode Storage Engine with Traffic Cop
============================================================
Phase 3A + 3C: Writes UniversalEvent objects to persistent storage.

Dual Mode Operation:
1. BIGQUERY Mode: Writes to BigQuery universal_ledger table (production)
2. LOCAL_FILE Mode: Writes to local JSONL files (fallback/development)

Traffic Cop Logic (Phase 3C):
- Events with confidence >= 0.85 OR verified=True -> universal_ledger (trusted)
- Events with confidence < 0.85 AND verified=False -> quarantine_queue (review)

The writer automatically detects available credentials and selects the
appropriate mode. If BigQuery fails mid-operation, it automatically
falls back to local file storage to prevent data loss.

Usage:
    writer = LedgerWriter()
    result = writer.write_batch(events, tenant_id="cafe_mellow")
    # Returns: {"status": "persisted_to_bigquery", "trusted": 5, "quarantined": 1}
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from .polymorphic_ledger import UniversalEvent


class LedgerWriter:
    """
    Dual-mode storage engine for UniversalEvent objects.
    
    Automatically selects between BigQuery and local file storage
    based on available credentials. Includes automatic fallback
    to local storage if BigQuery operations fail.
    
    Traffic Cop: Routes events based on confidence score.
    - High confidence (>= 0.85) or verified -> Main Ledger
    - Low confidence (< 0.85) and unverified -> Quarantine Queue
    """
    
    # Storage modes
    MODE_BIGQUERY = "BIGQUERY"
    MODE_LOCAL_FILE = "LOCAL_FILE"
    
    # Traffic Cop threshold (configurable)
    CONFIDENCE_THRESHOLD = 0.85
    
    def __init__(self):
        """
        Initialize the LedgerWriter with automatic mode detection.
        
        Checks for BigQuery credentials in this order:
        1. GOOGLE_APPLICATION_CREDENTIALS environment variable
        2. service-account.json in project root
        3. service-key.json in project root (legacy)
        
        If none found, falls back to LOCAL_FILE mode.
        """
        self.mode = self.MODE_LOCAL_FILE
        self.client = None
        self.project_id = None
        self.dataset_id = None
        self.table_id = None
        
        # Determine project root (two levels up from this file)
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data" / "ledger"
        
        # Try to initialize BigQuery
        self._init_bigquery()
    
    def _init_bigquery(self):
        """
        Attempt to initialize BigQuery client.
        Sets mode to BIGQUERY if successful, LOCAL_FILE otherwise.
        """
        try:
            # Check if google-cloud-bigquery is installed
            from google.cloud import bigquery
        except ImportError:
            print("[LEDGER] google-cloud-bigquery not installed. Using Local Fallback.")
            return
        
        # Check for credentials
        creds_path = None
        
        # Option 1: GOOGLE_APPLICATION_CREDENTIALS env var
        env_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if env_creds and os.path.exists(env_creds):
            creds_path = env_creds
        
        # Option 2: service-account.json in project root
        if not creds_path:
            sa_path = self.project_root / "service-account.json"
            if sa_path.exists():
                creds_path = str(sa_path)
        
        # Option 3: service-key.json (legacy naming)
        if not creds_path:
            sk_path = self.project_root / "service-key.json"
            if sk_path.exists():
                creds_path = str(sk_path)
        
        if not creds_path:
            print("[LEDGER] Cloud credentials missing. Using Local Fallback.")
            return
        
        try:
            # Initialize BigQuery client
            self.client = bigquery.Client.from_service_account_json(creds_path)
            
            # Get project/dataset config (returns tuple)
            from pillars.config_vault import get_bq_config
            self.project_id, self.dataset_id = get_bq_config()
            self.table_id = f"{self.project_id}.{self.dataset_id}.universal_ledger"
            self.quarantine_table_id = f"{self.project_id}.{self.dataset_id}.quarantine_queue"
            
            self.mode = self.MODE_BIGQUERY
            print(f"[LEDGER] BigQuery mode enabled. Table: {self.table_id}")
            print(f"[LEDGER] Quarantine table: {self.quarantine_table_id}")
            
        except Exception as e:
            print(f"[LEDGER] BigQuery init failed: {e}. Using Local Fallback.")
            self.client = None
    
    def write_batch(
        self, 
        events: List[UniversalEvent], 
        tenant_id: str,
        data_type: str = None
    ) -> Dict[str, Any]:
        """
        Write a batch of UniversalEvent objects to storage.
        
        TRAFFIC COP LOGIC:
        - Events with confidence >= 0.85 OR verified=True -> universal_ledger
        - Events with confidence < 0.85 AND verified=False -> quarantine_queue
        
        PHASE 8 GHOST LOGIC:
        - For STREAM (Sales) data: Auto-create provisional menu items for unknown items
        - For STATE (Menu) data: Upsert items, convert provisional to official
        
        Args:
            events: List of UniversalEvent objects to persist
            tenant_id: Tenant identifier for file naming and validation
            data_type: "STREAM" (Sales) or "STATE" (Menu) for Ghost Logic
            
        Returns:
            dict with keys:
                - status: "persisted" | "saved_locally" | "error"
                - trusted_count: Number of trusted events written to ledger
                - quarantined_count: Number of events sent to quarantine
                - ghost_items_created: Number of provisional items created
                - details: Breakdown of write operations
        """
        if not events:
            return {
                "status": "no_events",
                "count": 0,
                "trusted_count": 0,
                "quarantined_count": 0,
                "ghost_items_created": 0,
                "message": "No events to write"
            }
        
        # === TRAFFIC COP: Separate events by confidence ===
        trusted_list = []
        quarantine_list = []
        
        for event in events:
            confidence = getattr(event, 'confidence_score', 0.0) or 0.0
            verified = getattr(event, 'verified', False) or False
            
            if confidence >= self.CONFIDENCE_THRESHOLD or verified:
                trusted_list.append(event)
            else:
                quarantine_list.append(event)
        
        print(f"[TRAFFIC COP] {len(trusted_list)} trusted, {len(quarantine_list)} quarantined (threshold: {self.CONFIDENCE_THRESHOLD})")
        
        # =====================================================================
        # PHASE 8: GHOST LOGIC - Handle provisional items
        # =====================================================================
        ghost_items_created = 0
        
        if data_type == "STREAM":
            # For STREAM (Sales) data: Check for unknown items and create provisional entries
            ghost_items_created = self._handle_ghost_items(trusted_list, tenant_id)
        elif data_type == "STATE":
            # For STATE (Menu) data: Upsert items, convert provisional to official
            self._handle_state_upsert(trusted_list, tenant_id)
        
        # === Write to appropriate destinations ===
        if self.mode == self.MODE_BIGQUERY:
            result = self._write_with_quarantine_bq(trusted_list, quarantine_list, tenant_id)
        else:
            result = self._write_with_quarantine_local(trusted_list, quarantine_list, tenant_id)
        
        # Add ghost items count to result
        result["ghost_items_created"] = ghost_items_created
        return result
    
    def _write_to_bigquery(
        self, 
        events: List[UniversalEvent], 
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Write events to BigQuery universal_ledger table.
        Falls back to local storage on failure.
        """
        try:
            # Convert events to dicts for BigQuery
            rows = []
            for event in events:
                row = asdict(event)
                # Ensure timestamp format is correct for BigQuery
                if row.get("timestamp"):
                    row["timestamp"] = self._normalize_timestamp(row["timestamp"])
                if row.get("created_at"):
                    row["created_at"] = self._normalize_timestamp(row["created_at"])
                if row.get("verified_at") and row["verified_at"]:
                    row["verified_at"] = self._normalize_timestamp(row["verified_at"])
                rows.append(row)
            
            # Insert rows to BigQuery
            errors = self.client.insert_rows_json(self.table_id, rows)
            
            if errors:
                # Partial failure - some rows failed
                error_msgs = [str(e) for e in errors[:5]]  # First 5 errors
                print(f"[LEDGER] BigQuery partial failure: {len(errors)} rows failed")
                
                # Fall back to local for ALL events to ensure data safety
                local_result = self._write_to_local(events, tenant_id)
                return {
                    "status": "fallback_to_local",
                    "count": len(events),
                    "bigquery_errors": error_msgs,
                    "file": local_result.get("file"),
                    "message": f"BigQuery failed, saved locally instead"
                }
            
            print(f"[LEDGER] Persisted {len(events)} events to BigQuery")
            return {
                "status": "persisted_to_bigquery",
                "count": len(events),
                "table": self.table_id
            }
            
        except Exception as e:
            print(f"[LEDGER] BigQuery write failed: {e}. Falling back to local.")
            
            # Automatic fallback to local storage
            local_result = self._write_to_local(events, tenant_id)
            return {
                "status": "fallback_to_local",
                "count": len(events),
                "bigquery_error": str(e),
                "file": local_result.get("file"),
                "message": f"BigQuery failed, saved locally instead"
            }
    
    def _write_to_local(
        self, 
        events: List[UniversalEvent], 
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Write events to local JSONL file.
        File path: data/ledger/{tenant_id}_ledger.jsonl
        """
        try:
            # Ensure directory exists
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            # Construct file path
            safe_tenant = tenant_id.replace("/", "_").replace("\\", "_")
            file_path = self.data_dir / f"{safe_tenant}_ledger.jsonl"
            
            # Append events as JSON lines
            with open(file_path, "a", encoding="utf-8") as f:
                for event in events:
                    row = asdict(event)
                    # Add write metadata
                    row["_written_at"] = datetime.utcnow().isoformat()
                    row["_writer_mode"] = "local_fallback"
                    f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            
            print(f"[LEDGER] Saved {len(events)} events locally to {file_path}")
            return {
                "status": "saved_locally",
                "count": len(events),
                "file": str(file_path)
            }
            
        except Exception as e:
            print(f"[LEDGER] Local write failed: {e}")
            return {
                "status": "error",
                "count": 0,
                "error": str(e)
            }
    
    def _normalize_timestamp(self, ts: str) -> str:
        """
        Normalize timestamp string for BigQuery compatibility.
        BigQuery expects ISO format: YYYY-MM-DDTHH:MM:SS.ffffff
        """
        if not ts:
            return datetime.utcnow().isoformat()
        
        # If already in good format, return as-is
        if "T" in ts:
            return ts
        
        # Try to parse and reformat
        try:
            # Handle various date formats
            for fmt in [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%d/%m/%Y",
                "%m/%d/%Y",
            ]:
                try:
                    dt = datetime.strptime(ts, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            
            # If all else fails, return as-is
            return ts
        except Exception:
            return ts
    
    def _write_with_quarantine_bq(
        self,
        trusted_list: List[UniversalEvent],
        quarantine_list: List[UniversalEvent],
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Write trusted events to universal_ledger and quarantined to quarantine_queue.
        BigQuery mode with fallback.
        """
        result = {
            "status": "persisted",
            "count": len(trusted_list) + len(quarantine_list),
            "trusted_count": 0,
            "quarantined_count": 0,
            "details": {}
        }
        
        # Write trusted events to main ledger
        if trusted_list:
            try:
                rows = [self._event_to_row(e) for e in trusted_list]
                errors = self.client.insert_rows_json(self.table_id, rows)
                if errors:
                    print(f"[LEDGER] Trusted write partial fail: {len(errors)} errors")
                    # Fallback to local
                    local_res = self._write_to_local(trusted_list, tenant_id)
                    result["details"]["trusted"] = {"fallback": True, "file": local_res.get("file")}
                else:
                    result["trusted_count"] = len(trusted_list)
                    result["details"]["trusted"] = {"table": self.table_id}
                    print(f"[LEDGER] {len(trusted_list)} trusted events -> {self.table_id}")
            except Exception as e:
                print(f"[LEDGER] Trusted write failed: {e}")
                local_res = self._write_to_local(trusted_list, tenant_id)
                result["details"]["trusted"] = {"fallback": True, "error": str(e)}
        
        # Write quarantined events to quarantine_queue
        if quarantine_list:
            try:
                rows = [self._event_to_row(e, quarantine=True) for e in quarantine_list]
                errors = self.client.insert_rows_json(self.quarantine_table_id, rows)
                if errors:
                    print(f"[QUARANTINE] Write partial fail: {len(errors)} errors")
                    # Fallback to local quarantine file
                    local_res = self._write_quarantine_local(quarantine_list, tenant_id)
                    result["details"]["quarantine"] = {"fallback": True, "file": local_res.get("file")}
                else:
                    result["quarantined_count"] = len(quarantine_list)
                    result["details"]["quarantine"] = {"table": self.quarantine_table_id}
                    print(f"[QUARANTINE] {len(quarantine_list)} events -> {self.quarantine_table_id}")
            except Exception as e:
                print(f"[QUARANTINE] Write failed: {e}. Using local fallback.")
                local_res = self._write_quarantine_local(quarantine_list, tenant_id)
                result["quarantined_count"] = len(quarantine_list)
                result["details"]["quarantine"] = {"fallback": True, "file": local_res.get("file")}
        
        return result
    
    def _write_with_quarantine_local(
        self,
        trusted_list: List[UniversalEvent],
        quarantine_list: List[UniversalEvent],
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Write trusted to ledger file and quarantined to quarantine file.
        Local file mode.
        """
        result = {
            "status": "saved_locally",
            "count": len(trusted_list) + len(quarantine_list),
            "trusted_count": 0,
            "quarantined_count": 0,
            "details": {}
        }
        
        # Write trusted events
        if trusted_list:
            local_res = self._write_to_local(trusted_list, tenant_id)
            result["trusted_count"] = len(trusted_list)
            result["details"]["trusted"] = {"file": local_res.get("file")}
        
        # Write quarantined events
        if quarantine_list:
            local_res = self._write_quarantine_local(quarantine_list, tenant_id)
            result["quarantined_count"] = len(quarantine_list)
            result["details"]["quarantine"] = {"file": local_res.get("file")}
        
        return result
    
    def _write_quarantine_local(
        self,
        events: List[UniversalEvent],
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Write quarantined events to local quarantine file.
        File path: data/ledger/{tenant_id}_quarantine.jsonl
        """
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            safe_tenant = tenant_id.replace("/", "_").replace("\\", "_")
            file_path = self.data_dir / f"{safe_tenant}_quarantine.jsonl"
            
            with open(file_path, "a", encoding="utf-8") as f:
                for event in events:
                    row = asdict(event)
                    row["_written_at"] = datetime.utcnow().isoformat()
                    row["_quarantine_reason"] = f"Low confidence: {row.get('confidence_score', 0.0)}"
                    row["_status"] = "pending_review"
                    f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            
            print(f"[QUARANTINE] Saved {len(events)} events locally to {file_path}")
            return {"status": "saved", "count": len(events), "file": str(file_path)}
        except Exception as e:
            print(f"[QUARANTINE] Local write failed: {e}")
            return {"status": "error", "count": 0, "error": str(e)}

    # =========================================================================
    # PHASE 8: GHOST LOGIC - Provisional Items
    # =========================================================================

    def _get_registry_file(self, tenant_id: str) -> Path:
        """Get path to local category registry file."""
        registry_dir = self.project_root / "data" / "registry"
        registry_dir.mkdir(parents=True, exist_ok=True)
        safe_tenant = tenant_id.replace("/", "_").replace("\\", "_")
        return registry_dir / f"{safe_tenant}_category_registry.jsonl"

    def _load_known_items(self, tenant_id: str) -> Dict[str, Dict[str, Any]]:
        """Load known items from local category registry (latest entry wins)."""
        registry_file = self._get_registry_file(tenant_id)
        known_items: Dict[str, Dict[str, Any]] = {}

        if registry_file.exists():
            try:
                with open(registry_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        entry = json.loads(line)
                        name = entry.get("name") or entry.get("category_name")
                        if name:
                            known_items[name.lower().strip()] = entry
            except Exception as e:
                print(f"[GHOST] Failed to load registry: {e}")

        return known_items

    def _handle_ghost_items(self, events: List[UniversalEvent], tenant_id: str) -> int:
        """
        Auto-create provisional menu items for unknown items in STREAM (Sales) data.
        """
        known_items = self._load_known_items(tenant_id)
        new_items: Dict[str, str] = {}

        for event in events:
            entity_name = getattr(event, "entity_name", None)
            if not entity_name:
                continue
            key = entity_name.lower().strip()
            if key and key not in known_items and key not in new_items:
                new_items[key] = entity_name.strip()

        if not new_items:
            return 0

        registry_file = self._get_registry_file(tenant_id)
        created_at = datetime.utcnow().isoformat()

        with open(registry_file, "a", encoding="utf-8") as f:
            for item_name in new_items.values():
                entry = {
                    "category_id": f"cat_{uuid.uuid4().hex[:8]}",
                    "tenant_id": tenant_id,
                    "name": item_name,
                    "category_name": item_name,
                    "is_provisional": True,
                    "is_official": False,
                    "is_active": True,
                    "source": "ghost_logic",
                    "created_at": created_at,
                    "updated_at": created_at,
                    "status": "provisional"
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                print(f"[GHOST] Auto-created provisional item: {item_name}")

        print(f"[GHOST] Created {len(new_items)} provisional items for tenant {tenant_id}")
        return len(new_items)

    def _handle_state_upsert(self, events: List[UniversalEvent], tenant_id: str) -> None:
        """
        Upsert menu items for STATE data and convert provisional to official.
        """
        known_items = self._load_known_items(tenant_id)
        updates: Dict[str, str] = {}

        for event in events:
            entity_name = getattr(event, "entity_name", None)
            if not entity_name:
                continue
            key = entity_name.lower().strip()
            if not key:
                continue
            existing = known_items.get(key)
            if existing and not existing.get("is_provisional", False):
                continue
            updates[key] = entity_name.strip()

        if not updates:
            return

        registry_file = self._get_registry_file(tenant_id)
        updated_at = datetime.utcnow().isoformat()

        with open(registry_file, "a", encoding="utf-8") as f:
            for key, item_name in updates.items():
                was_provisional = known_items.get(key, {}).get("is_provisional", False)
                entry = {
                    "category_id": f"cat_{uuid.uuid4().hex[:8]}",
                    "tenant_id": tenant_id,
                    "name": item_name,
                    "category_name": item_name,
                    "is_provisional": False,
                    "is_official": True,
                    "is_active": True,
                    "source": "state_upsert",
                    "created_at": known_items.get(key, {}).get("created_at", updated_at),
                    "updated_at": updated_at,
                    "status": "official",
                    "converted_from": "provisional" if was_provisional else "new_state"
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

                if was_provisional:
                    print(f"[STATE] Converted provisional to official: {item_name}")
                else:
                    print(f"[STATE] Added official menu item: {item_name}")
    
    def _event_to_row(self, event: UniversalEvent, quarantine: bool = False) -> Dict[str, Any]:
        """Convert UniversalEvent to BigQuery row dict."""
        row = asdict(event)
        if row.get("timestamp"):
            row["timestamp"] = self._normalize_timestamp(row["timestamp"])
        if row.get("created_at"):
            row["created_at"] = self._normalize_timestamp(row["created_at"])
        if row.get("verified_at") and row["verified_at"]:
            row["verified_at"] = self._normalize_timestamp(row["verified_at"])
        if quarantine:
            row["_quarantine_reason"] = f"Low confidence: {row.get('confidence_score', 0.0)}"
            row["_status"] = "pending_review"
        return row
    
    def get_mode(self) -> str:
        """Return current storage mode."""
        return self.mode
    
    def get_status(self) -> Dict[str, Any]:
        """Return current writer status for diagnostics."""
        return {
            "mode": self.mode,
            "bigquery_available": self.client is not None,
            "table_id": self.table_id,
            "local_data_dir": str(self.data_dir)
        }
