"""
Centralized BigQuery client factory.
Handles both local development (service-key.json) and Cloud Run (ADC).
"""
import os


def get_bq_client():
    """
    Get BigQuery client with fallback from service account key to ADC.
    Returns None if BigQuery cannot be initialized.
    """
    try:
        from google.cloud import bigquery
        from pillars.config_vault import EffectiveSettings

        cfg = EffectiveSettings()
        key_file = getattr(cfg, "KEY_FILE", "service-key.json")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
        
        # Try service account key file first (local development)
        if os.path.exists(key_path):
            return bigquery.Client.from_service_account_json(key_path)
        
        # Fall back to Application Default Credentials (Cloud Run)
        project_id = getattr(cfg, "PROJECT_ID", None) or os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if project_id:
            return bigquery.Client(project=project_id)
        
        # Last resort: let BigQuery auto-detect project
        return bigquery.Client()
    except Exception:
        return None
