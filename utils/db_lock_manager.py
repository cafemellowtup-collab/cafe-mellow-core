"""
Database Lock Manager: Prevents race conditions during simultaneous syncs
Uses BigQuery table for distributed locking across multiple workers
"""
from datetime import datetime, timedelta
from typing import Optional
from google.cloud import bigquery
import time
import uuid


class DatabaseLockManager:
    """
    Distributed lock manager using BigQuery as lock store.
    Prevents race conditions when multiple sync processes run simultaneously.
    """
    
    def __init__(self, client: bigquery.Client, settings, lock_timeout_seconds: int = 300):
        self.client = client
        self.settings = settings
        self.lock_timeout_seconds = lock_timeout_seconds
        self.project_id = getattr(settings, "PROJECT_ID", "")
        self.dataset_id = getattr(settings, "DATASET_ID", "")
        self.locks_table = f"{self.project_id}.{self.dataset_id}.system_locks"
        self._ensure_locks_table()
    
    def _ensure_locks_table(self):
        """Create locks table if it doesn't exist"""
        try:
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS `{self.locks_table}` (
                lock_name STRING NOT NULL,
                lock_owner STRING NOT NULL,
                acquired_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                metadata JSON
            )
            CLUSTER BY lock_name
            """
            self.client.query(create_sql).result()
        except Exception as e:
            print(f"Error creating locks table: {e}")
    
    def acquire_lock(self, lock_name: str, owner: Optional[str] = None, wait: bool = True, max_wait_seconds: int = 60) -> bool:
        """
        Acquire a distributed lock.
        
        Args:
            lock_name: Name of the lock (e.g., "sync_expenses", "sync_sales")
            owner: Lock owner identifier (defaults to random UUID)
            wait: If True, wait for lock to be released
            max_wait_seconds: Maximum seconds to wait for lock
        
        Returns:
            True if lock acquired, False otherwise
        """
        if owner is None:
            owner = f"worker_{uuid.uuid4().hex[:8]}"
        
        start_time = time.time()
        
        while True:
            # Clean up expired locks first
            self._cleanup_expired_locks()
            
            # Try to acquire lock
            acquired = self._try_acquire_lock(lock_name, owner)
            
            if acquired:
                return True
            
            # If not waiting or timeout exceeded, return False
            if not wait or (time.time() - start_time) > max_wait_seconds:
                return False
            
            # Wait a bit before retrying
            time.sleep(2)
    
    def _try_acquire_lock(self, lock_name: str, owner: str) -> bool:
        """Attempt to acquire lock atomically"""
        try:
            # Check if lock exists and is not expired
            check_sql = f"""
            SELECT COUNT(*) as lock_count
            FROM `{self.locks_table}`
            WHERE lock_name = '{lock_name}'
              AND expires_at > CURRENT_TIMESTAMP()
            """
            
            df = self.client.query(check_sql).to_dataframe()
            lock_exists = int(df['lock_count'].iloc[0]) > 0 if not df.empty else False
            
            if lock_exists:
                return False  # Lock is held by someone else
            
            # Try to insert lock (atomic operation)
            expires_at = datetime.now() + timedelta(seconds=self.lock_timeout_seconds)
            
            insert_sql = f"""
            INSERT INTO `{self.locks_table}`
            (lock_name, lock_owner, acquired_at, expires_at, metadata)
            VALUES (
                '{lock_name}',
                '{owner}',
                CURRENT_TIMESTAMP(),
                TIMESTAMP('{expires_at.isoformat()}'),
                JSON '{{"lock_timeout_seconds": {self.lock_timeout_seconds}}}'
            )
            """
            
            self.client.query(insert_sql).result()
            return True
            
        except Exception as e:
            # If insert fails (e.g., due to race condition), lock was not acquired
            print(f"Lock acquisition failed: {e}")
            return False
    
    def release_lock(self, lock_name: str, owner: Optional[str] = None):
        """
        Release a lock.
        
        Args:
            lock_name: Name of the lock to release
            owner: Lock owner (if specified, only releases if owner matches)
        """
        try:
            if owner:
                delete_sql = f"""
                DELETE FROM `{self.locks_table}`
                WHERE lock_name = '{lock_name}'
                  AND lock_owner = '{owner}'
                """
            else:
                delete_sql = f"""
                DELETE FROM `{self.locks_table}`
                WHERE lock_name = '{lock_name}'
                """
            
            self.client.query(delete_sql).result()
            
        except Exception as e:
            print(f"Error releasing lock: {e}")
    
    def _cleanup_expired_locks(self):
        """Remove expired locks"""
        try:
            cleanup_sql = f"""
            DELETE FROM `{self.locks_table}`
            WHERE expires_at < CURRENT_TIMESTAMP()
            """
            self.client.query(cleanup_sql).result()
        except Exception as e:
            print(f"Error cleaning up expired locks: {e}")
    
    def is_locked(self, lock_name: str) -> bool:
        """Check if a lock is currently held"""
        try:
            check_sql = f"""
            SELECT COUNT(*) as lock_count
            FROM `{self.locks_table}`
            WHERE lock_name = '{lock_name}'
              AND expires_at > CURRENT_TIMESTAMP()
            """
            
            df = self.client.query(check_sql).to_dataframe()
            return int(df['lock_count'].iloc[0]) > 0 if not df.empty else False
            
        except Exception:
            return False
    
    def get_lock_info(self, lock_name: str) -> Optional[dict]:
        """Get information about a lock"""
        try:
            info_sql = f"""
            SELECT lock_owner, acquired_at, expires_at
            FROM `{self.locks_table}`
            WHERE lock_name = '{lock_name}'
              AND expires_at > CURRENT_TIMESTAMP()
            LIMIT 1
            """
            
            df = self.client.query(info_sql).to_dataframe()
            
            if df.empty:
                return None
            
            return {
                "lock_owner": df['lock_owner'].iloc[0],
                "acquired_at": df['acquired_at'].iloc[0].isoformat(),
                "expires_at": df['expires_at'].iloc[0].isoformat()
            }
            
        except Exception:
            return None


class SyncLockContext:
    """
    Context manager for automatic lock acquisition and release.
    
    Usage:
        with SyncLockContext(client, settings, "sync_expenses") as lock:
            if lock.acquired:
                # Perform sync operation
                pass
    """
    
    def __init__(self, client: bigquery.Client, settings, lock_name: str, owner: Optional[str] = None):
        self.lock_manager = DatabaseLockManager(client, settings)
        self.lock_name = lock_name
        self.owner = owner or f"worker_{uuid.uuid4().hex[:8]}"
        self.acquired = False
    
    def __enter__(self):
        self.acquired = self.lock_manager.acquire_lock(self.lock_name, self.owner, wait=True, max_wait_seconds=30)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            self.lock_manager.release_lock(self.lock_name, self.owner)
        return False
