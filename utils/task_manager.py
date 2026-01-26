"""
Task Management System with Follow-up
"""
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import settings

class TaskManager:
    """Manage tasks with follow-up mechanism"""
    
    def __init__(self, client, settings):
        self.client = client
        self.settings = settings
    
    def create_task(self, task_data):
        """Create a new task"""
        try:
            table_id = f"{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.tasks"
            
            # Create table if not exists
            try:
                self.client.get_table(table_id)
            except NotFound:
                schema = [
                    bigquery.SchemaField("task_id", "STRING"),
                    bigquery.SchemaField("task_title", "STRING"),
                    bigquery.SchemaField("task_description", "STRING"),
                    bigquery.SchemaField("priority", "STRING"),
                    bigquery.SchemaField("assigned_date", "DATE"),
                    bigquery.SchemaField("due_date", "DATE"),
                    bigquery.SchemaField("status", "STRING"),
                    bigquery.SchemaField("completed_date", "DATE"),
                    bigquery.SchemaField("created_at", "TIMESTAMP"),
                    bigquery.SchemaField("last_followup", "TIMESTAMP")
                ]
                table = bigquery.Table(table_id, schema=schema)
                self.client.create_table(table)
            
            task_data['created_at'] = datetime.now()
            task_data['last_followup'] = datetime.now()
            
            errors = self.client.insert_rows_json(table_id, [task_data])
            return len(errors) == 0
        except Exception as e:
            print(f"Error creating task: {e}")
            return False
    
    def get_pending_tasks(self, days=1):
        """Get pending tasks"""
        try:
            table_id = f"{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.tasks"
            query = f"""
                SELECT *
                FROM `{table_id}`
                WHERE status != 'Completed'
                AND assigned_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
                ORDER BY priority DESC, assigned_date DESC
            """
            df = self.client.query(query).to_dataframe()
            return df.to_dict('records') if not df.empty else []
        except:
            return []
    
    def mark_task_complete(self, task_id):
        """Mark task as completed"""
        try:
            table_id = f"{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.tasks"
            query = f"""
                UPDATE `{table_id}`
                SET status = 'Completed',
                    completed_date = CURRENT_DATE()
                WHERE task_id = '{task_id}'
            """
            self.client.query(query).result()
            return True
        except:
            return False
    
    def get_tasks_needing_followup(self):
        """Get tasks that need follow-up (assigned yesterday or earlier, not completed)"""
        try:
            table_id = f"{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.tasks"
            query = f"""
                SELECT *
                FROM `{table_id}`
                WHERE status != 'Completed'
                AND assigned_date < CURRENT_DATE()
                ORDER BY assigned_date ASC
            """
            df = self.client.query(query).to_dataframe()
            return df.to_dict('records') if not df.empty else []
        except:
            return []
    
    def update_followup(self, task_id):
        """Update last follow-up timestamp"""
        try:
            table_id = f"{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.tasks"
            query = f"""
                UPDATE `{table_id}`
                SET last_followup = CURRENT_TIMESTAMP()
                WHERE task_id = '{task_id}'
            """
            self.client.query(query).result()
            return True
        except:
            return False
