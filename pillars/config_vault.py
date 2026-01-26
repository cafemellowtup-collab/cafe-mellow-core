"""
TITAN Config Vault: UI-editable settings (API keys, BQ project) without touching code.
Uses config_override.json. EffectiveSettings merges settings + overrides.
"""
import json
import os
import types

CONFIG_OVERRIDE_PATH = "config_override.json"
OVERRIDABLE_KEYS = [
    "PROJECT_ID", "DATASET_ID", "GEMINI_API_KEY", "KEY_FILE",
    "PP_APP_KEY", "PP_APP_SECRET", "PP_ACCESS_TOKEN", "PP_MAPPING_CODE",
    "FOLDER_ID_EXPENSES", "FOLDER_ID_PURCHASES", "FOLDER_ID_INVENTORY",
    "FOLDER_ID_RECIPES", "FOLDER_ID_WASTAGE",
]


def _project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config_override():
    path = os.path.join(_project_root(), CONFIG_OVERRIDE_PATH)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config_override(overrides: dict, merge: bool = True):
    """
    Save config overrides. If merge=True, preserves existing keys not in overrides.
    This fixes the credential overwrite bug.
    """
    path = os.path.join(_project_root(), CONFIG_OVERRIDE_PATH)
    
    # Load existing config if merge mode
    existing = {}
    if merge and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}
    
    # Merge new overrides with existing
    merged = {**existing} if merge else {}
    for k in OVERRIDABLE_KEYS:
        if k in overrides and overrides[k] is not None:
            merged[k] = overrides[k]
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)
    return merged


class EffectiveSettings:
    """
    Merged settings: config_override overrides settings.py.
    Use as: cfg = EffectiveSettings(); cfg.PROJECT_ID, cfg.GEMINI_API_KEY, etc.
    """

    def __init__(self):
        import settings as _s
        self._settings = _s
        self._overrides = load_config_override()

    def __getattr__(self, key):
        if key in self._overrides:
            return self._overrides[key]
        return getattr(self._settings, key)

    def get_override(self, key):
        return self._overrides.get(key)

    def all_overridable(self):
        return {k: getattr(self, k) for k in OVERRIDABLE_KEYS}
