"""
DPDP Data Export
Users have the right to export their data (India DPDP Act 2023)
"""
import json
from datetime import datetime
from typing import Dict, Any, List


class DPDPDataExporter:
    """
    DPDP Compliance - Data Export
    Allows users to export all their data
    """
    
    def __init__(self, client, settings):
        self.client = client
        self.settings = settings
    
    def export_user_data(self, user_id: str, org_id: str) -> Dict[str, Any]:
        """
        Export all data related to a user
        Returns JSON-serializable dict
        """
        export_data = {
            "export_metadata": {
                "user_id": user_id,
                "org_id": org_id,
                "exported_at": datetime.utcnow().isoformat(),
                "format_version": "1.0"
            },
            "user_profile": self._export_user_profile(user_id),
            "ledger_entries": self._export_ledger_entries(user_id, org_id),
            "activities": self._export_user_activities(user_id, org_id)
        }
        
        return export_data
    
    def _export_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Export user profile data"""
        try:
            query = f"""
            SELECT id, username, email, phone, role_ids, org_id, location_ids, created_at, last_login
            FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.users`
            WHERE id = '{user_id}'
            """
            
            result = self.client.query(query).result()
            
            for row in result:
                return dict(row)
            
            return {}
        except Exception:
            return {}
    
    def _export_ledger_entries(self, user_id: str, org_id: str) -> List[Dict[str, Any]]:
        """Export ledger entries created by user"""
        try:
            query = f"""
            SELECT *
            FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.ledger_universal`
            WHERE created_by = '{user_id}' AND org_id = '{org_id}'
            ORDER BY timestamp DESC
            LIMIT 10000
            """
            
            result = self.client.query(query).result()
            
            return [dict(row) for row in result]
        except Exception:
            return []
    
    def _export_user_activities(self, user_id: str, org_id: str) -> List[Dict[str, Any]]:
        """Export user activity log"""
        try:
            query = f"""
            SELECT *
            FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.user_activity_log`
            WHERE user_id = '{user_id}' AND org_id = '{org_id}'
            ORDER BY timestamp DESC
            LIMIT 5000
            """
            
            result = self.client.query(query).result()
            
            return [dict(row) for row in result]
        except Exception:
            return []
    
    def export_to_json_file(self, user_id: str, org_id: str, output_path: str) -> str:
        """Export user data to JSON file"""
        data = self.export_user_data(user_id, org_id)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        return output_path
