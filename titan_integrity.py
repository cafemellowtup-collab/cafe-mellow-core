"""
TITAN-INTEGRITY: Data Accuracy above all else.
Raise DataIntegrityError and log State of Data before terminating.
"""
import json
import os
import sys
import traceback
from datetime import datetime


class DataIntegrityError(Exception):
    """Raised when source is incomplete, API/DB fails, or required data is missing. Script must stop."""

    def __init__(self, message, state_of_data=None):
        super().__init__(message)
        self.state_of_data = state_of_data or {}


def _log_path():
    root = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(root, "logs", "titan_system_log.txt")


def _write_crash_block(module, message, state, exc_info, file_path="?", line_number="?"):
    state = state or {}
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    tb_text = ""
    if exc_info and len(exc_info) >= 3:
        tb_text = "".join(traceback.format_exception(*exc_info))
        tb = exc_info[2]
        if tb is not None and hasattr(tb, 'tb_frame') and tb.tb_frame and hasattr(tb.tb_frame.f_code, 'co_filename'):
            file_path = tb.tb_frame.f_code.co_filename or "?"
            line_number = getattr(tb, 'tb_lineno', "?")
    elif sys.exc_info() and sys.exc_info()[0]:
        tb_text = traceback.format_exc()
    try:
        state_json = json.dumps(state, default=str, indent=2)
    except Exception:
        state_json = str(state)
    block = (
        f"[{ts}] [CRASH] [{module}] [{file_path}:{line_number}] DataIntegrityError: {message}\n"
        f"State of Data:\n{state_json}\nTraceback:\n{tb_text}\n---\n"
    )
    try:
        with open(_log_path(), "a", encoding="utf-8", errors="replace") as f:
            f.write(block)
    except Exception:
        try:
            sys.stderr.write(block)
        except Exception:
            pass
    return block


def crash_report(module, message, state_of_data=None, exc_info=None):
    """
    Log exact line of failure and State of Data to logs/titan_system_log.txt, then raise DataIntegrityError.
    state_of_data: dict. exc_info: from sys.exc_info() or None.
    """
    _write_crash_block(module, message, state_of_data or {}, exc_info)
    raise DataIntegrityError(message, state_of_data=state_of_data or {})


def append_crash_state(module, message, state_of_data=None):
    """Append State of Data to log only (e.g. when catching DataIntegrityError that was not from crash_report)."""
    _write_crash_block(module, message, state_of_data or {}, None)
