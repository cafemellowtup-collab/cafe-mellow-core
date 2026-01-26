"""
TITAN System Logger: Automatic error logging to file and BigQuery.
Read titan_system_log.txt to quickly identify exact error and place.
"""
import os
import sys
import traceback
import uuid
from datetime import datetime
from google.cloud.bigquery import SchemaField

LOG_DIR = "logs"
LOG_FILE = "logs/titan_system_log.txt"
SCHEMA = [
    SchemaField("id", "STRING", mode="NULLABLE"),
    SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("module", "STRING", mode="NULLABLE"),
    SchemaField("file_path", "STRING", mode="NULLABLE"),
    SchemaField("line_number", "INT64", mode="NULLABLE"),
    SchemaField("error_message", "STRING", mode="NULLABLE"),
    SchemaField("traceback_text", "STRING", mode="NULLABLE"),
    SchemaField("context", "STRING", mode="NULLABLE"),
]


def _ensure_log_dir():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(root, LOG_DIR)
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(root, LOG_FILE)


def _table_id(s=None):
    if s is None:
        import settings as _s
        s = _s
    return f"{s.PROJECT_ID}.{s.DATASET_ID}.{getattr(s, 'TABLE_SYSTEM_ERROR_LOG', 'system_error_log')}"


SYNC_LOG_SCHEMA = [
    SchemaField("sync_type", "STRING", mode="REQUIRED"),
    SchemaField("last_sync_ts", "TIMESTAMP", mode="REQUIRED"),
    SchemaField("rows_synced", "INT64", mode="NULLABLE"),
    SchemaField("status", "STRING", mode="NULLABLE"),
    SchemaField("triggered_by", "STRING", mode="NULLABLE"),
]


def _sync_log_table_id(s=None):
    if s is None:
        import settings as _s
        s = _s
    return f"{s.PROJECT_ID}.{s.DATASET_ID}.{getattr(s, 'TABLE_SYSTEM_SYNC_LOG', 'system_sync_log')}"


def ensure_system_sync_log_table(client, s=None):
    """Create system_sync_log in BigQuery if it does not exist."""
    from google.cloud.exceptions import NotFound
    if s is None:
        import settings as _s
        s = _s
    tid = _sync_log_table_id(s)
    try:
        client.get_table(tid)
        return True, False
    except NotFound:
        from google.cloud import bigquery
        t = bigquery.Table(tid, schema=SYNC_LOG_SCHEMA)
        client.create_table(t)
        return True, True


def log_sync_success(sync_type, rows_synced, client, s=None, triggered_by=None):
    """Append a successful sync record to system_sync_log. triggered_by from SYNC_TRIGGERED_BY env or 'cli'."""
    if s is None:
        import settings as _s
        s = _s
    ensure_system_sync_log_table(client, s)
    tid = _sync_log_table_id(s)
    tb = triggered_by if triggered_by is not None else os.environ.get("SYNC_TRIGGERED_BY", "cli")
    row = {
        "sync_type": str(sync_type)[:64],
        "last_sync_ts": datetime.utcnow().isoformat(),
        "rows_synced": int(rows_synced) if rows_synced is not None else None,
        "status": "success",
        "triggered_by": str(tb)[:64] if tb else None,
    }
    try:
        errs = client.insert_rows_json(tid, [row])
        if errs:
            try:
                with open(_ensure_log_dir(), "a", encoding="utf-8", errors="replace") as f:
                    f.write(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] [system_logger] system_sync_log insert failed: {errs}\n---\n")
            except Exception:
                pass
    except Exception:
        pass


def ensure_system_error_log_table(client, s=None):
    """Create system_error_log in BigQuery if it does not exist."""
    from google.cloud.exceptions import NotFound
    if s is None:
        import settings as _s
        s = _s
    tid = _table_id(s)
    try:
        client.get_table(tid)
        return True, False
    except NotFound:
        from google.cloud import bigquery
        t = bigquery.Table(tid, schema=SCHEMA)
        client.create_table(t)
        return True, True


def log_error(module, message, exc_info=None, file_path=None, line_number=None, context=None, client=None, settings_mod=None):
    """
    Append error to logs/titan_system_log.txt. If client and settings given, also insert into BigQuery system_error_log.
    module: e.g. "titan_app", "pillars.dashboard"
    message: short error message
    exc_info: from sys.exc_info() or None
    file_path, line_number: optional location
    context: optional JSON or string
    """
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    tb_text = ""
    if exc_info:
        tb_text = "".join(traceback.format_exception(*exc_info))
    elif exc_info is None and sys.exc_info() and sys.exc_info()[0]:
        tb_text = traceback.format_exc()

    loc = f"{file_path or '?'}:{line_number or '?'}"
    block = f"[{ts}] [{module}] [{loc}] ERROR: {message}\n{tb_text}\n---\n"

    # File
    try:
        logpath = _ensure_log_dir()
        with open(logpath, "a", encoding="utf-8", errors="replace") as f:
            f.write(block)
    except Exception as e:
        # TITAN-INTEGRITY: only allowed silent catch — prevents log recursion
        try:
            sys.stderr.write(f"TITAN LOG WRITE FAILED: {e}\n{block}")
        except Exception:
            pass

    # BigQuery
    if client and settings_mod:
        try:
            tid = _table_id(settings_mod)
            row = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "module": (module or "")[:500],
                "file_path": (file_path or "")[:500],
                "line_number": int(line_number) if line_number is not None else None,
                "error_message": (message or "")[:8000],
                "traceback_text": (tb_text or "")[:8000],
                "context": (str(context) if context is not None else "")[:4000],
            }
            errs = client.insert_rows_json(tid, [row])
            if errs:
                with open(_ensure_log_dir(), "a", encoding="utf-8", errors="replace") as f:
                    f.write(f"[{ts}] [system_logger] BQ insert failed: {errs}\n---\n")
        except Exception:
            pass  # TITAN-INTEGRITY: logger-only; do not mask caller's error
    return block
