"""
Usage Tracker - Monitor and track resource usage per tenant
Handles: AI tokens, BigQuery costs, API calls, feature usage
"""

import json
from datetime import datetime, timezone, timedelta, date
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError

PROJECT_ID = "cafe-mellow-core-2026"
DATASET_ID = "cafe_operations"
_bq_init_error: Optional[Exception] = None
try:
    bq = bigquery.Client(project=PROJECT_ID)
except DefaultCredentialsError as e:
    bq = None
    _bq_init_error = e
except Exception as e:
    bq = None
    _bq_init_error = e


@dataclass
class DailyUsage:
    """Daily usage record for a tenant"""
    tenant_id: str
    date: date
    ai_tokens: int = 0
    ai_cost_inr: float = 0.0
    bq_bytes: int = 0
    bq_cost_inr: float = 0.0
    api_calls: int = 0
    chat_messages: int = 0
    reports_generated: int = 0
    tasks_created: int = 0
    logins: int = 0
    active_users: int = 0


@dataclass
class UsageSummary:
    """Aggregated usage summary"""
    tenant_id: str
    period: str  # daily, weekly, monthly
    total_ai_tokens: int = 0
    total_ai_cost: float = 0.0
    total_bq_cost: float = 0.0
    total_api_calls: int = 0
    avg_daily_messages: float = 0.0
    total_reports: int = 0
    total_tasks: int = 0
    cost_trend: float = 0.0  # % change from previous period


class UsageTracker:
    """
    Track and analyze resource usage across all tenants
    """
    
    TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.tenant_usage"
    
    # Cost rates (approximate)
    AI_TOKEN_COST_INR = 0.0001  # per token
    BQ_BYTE_COST_INR = 0.000000005  # per byte scanned
    
    @classmethod
    def init_table(cls):
        """Initialize the tenant_usage table"""
        schema = [
            bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("ai_tokens", "INT64"),
            bigquery.SchemaField("ai_cost_inr", "FLOAT64"),
            bigquery.SchemaField("bq_bytes", "INT64"),
            bigquery.SchemaField("bq_cost_inr", "FLOAT64"),
            bigquery.SchemaField("api_calls", "INT64"),
            bigquery.SchemaField("chat_messages", "INT64"),
            bigquery.SchemaField("reports_generated", "INT64"),
            bigquery.SchemaField("tasks_created", "INT64"),
            bigquery.SchemaField("logins", "INT64"),
            bigquery.SchemaField("active_users", "INT64"),
        ]
        
        table = bigquery.Table(cls.TABLE_ID, schema=schema)
        try:
            bq.create_table(table)
            print(f"Created table {cls.TABLE_ID}")
        except Exception as e:
            if "Already Exists" in str(e):
                print(f"Table {cls.TABLE_ID} already exists")
            else:
                raise e
    
    @classmethod
    def record_ai_usage(cls, tenant_id: str, tokens: int):
        """Record AI token usage"""
        cost = tokens * cls.AI_TOKEN_COST_INR
        cls._increment_usage(tenant_id, {
            "ai_tokens": tokens,
            "ai_cost_inr": cost,
        })
    
    @classmethod
    def record_bq_usage(cls, tenant_id: str, bytes_scanned: int):
        """Record BigQuery usage"""
        cost = bytes_scanned * cls.BQ_BYTE_COST_INR
        cls._increment_usage(tenant_id, {
            "bq_bytes": bytes_scanned,
            "bq_cost_inr": cost,
        })
    
    @classmethod
    def record_api_call(cls, tenant_id: str):
        """Record an API call"""
        cls._increment_usage(tenant_id, {"api_calls": 1})
    
    @classmethod
    def record_chat_message(cls, tenant_id: str):
        """Record a chat message"""
        cls._increment_usage(tenant_id, {"chat_messages": 1})
    
    @classmethod
    def record_report(cls, tenant_id: str):
        """Record a report generation"""
        cls._increment_usage(tenant_id, {"reports_generated": 1})
    
    @classmethod
    def record_task(cls, tenant_id: str):
        """Record a task creation"""
        cls._increment_usage(tenant_id, {"tasks_created": 1})
    
    @classmethod
    def record_login(cls, tenant_id: str):
        """Record a user login"""
        cls._increment_usage(tenant_id, {"logins": 1})
    
    @classmethod
    def _increment_usage(cls, tenant_id: str, increments: Dict[str, Any]):
        """Increment usage counters for today"""
        today = date.today().isoformat()
        
        # Check if row exists for today
        check_query = f"""
            SELECT COUNT(*) as cnt FROM `{cls.TABLE_ID}`
            WHERE tenant_id = '{tenant_id}' AND date = '{today}'
        """
        result = list(bq.query(check_query).result())[0]
        
        if result.cnt == 0:
            # Create new row
            row = {
                "tenant_id": tenant_id,
                "date": today,
                "ai_tokens": increments.get("ai_tokens", 0),
                "ai_cost_inr": increments.get("ai_cost_inr", 0),
                "bq_bytes": increments.get("bq_bytes", 0),
                "bq_cost_inr": increments.get("bq_cost_inr", 0),
                "api_calls": increments.get("api_calls", 0),
                "chat_messages": increments.get("chat_messages", 0),
                "reports_generated": increments.get("reports_generated", 0),
                "tasks_created": increments.get("tasks_created", 0),
                "logins": increments.get("logins", 0),
                "active_users": 1 if increments.get("logins", 0) > 0 else 0,
            }
            errors = bq.insert_rows_json(cls.TABLE_ID, [row])
            if errors:
                print(f"Usage insert error: {errors}")
        else:
            # Update existing row
            set_clauses = []
            for field, value in increments.items():
                set_clauses.append(f"{field} = {field} + {value}")
            
            update_query = f"""
                UPDATE `{cls.TABLE_ID}`
                SET {', '.join(set_clauses)}
                WHERE tenant_id = '{tenant_id}' AND date = '{today}'
            """
            bq.query(update_query).result()
    
    @classmethod
    def get_daily_usage(cls, tenant_id: str, target_date: Optional[date] = None) -> Optional[DailyUsage]:
        """Get usage for a specific day"""
        d = target_date or date.today()
        
        query = f"""
            SELECT * FROM `{cls.TABLE_ID}`
            WHERE tenant_id = '{tenant_id}' AND date = '{d.isoformat()}'
        """
        results = list(bq.query(query).result())
        
        if not results:
            return None
        
        row = results[0]
        return DailyUsage(
            tenant_id=row.tenant_id,
            date=row.date,
            ai_tokens=row.ai_tokens or 0,
            ai_cost_inr=row.ai_cost_inr or 0,
            bq_bytes=row.bq_bytes or 0,
            bq_cost_inr=row.bq_cost_inr or 0,
            api_calls=row.api_calls or 0,
            chat_messages=row.chat_messages or 0,
            reports_generated=row.reports_generated or 0,
            tasks_created=row.tasks_created or 0,
            logins=row.logins or 0,
            active_users=row.active_users or 0,
        )
    
    @classmethod
    def get_usage_summary(
        cls, 
        tenant_id: str, 
        days: int = 30
    ) -> UsageSummary:
        """Get aggregated usage summary for a period"""
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        query = f"""
            SELECT
                SUM(ai_tokens) as total_ai_tokens,
                SUM(ai_cost_inr) as total_ai_cost,
                SUM(bq_cost_inr) as total_bq_cost,
                SUM(api_calls) as total_api_calls,
                AVG(chat_messages) as avg_daily_messages,
                SUM(reports_generated) as total_reports,
                SUM(tasks_created) as total_tasks
            FROM `{cls.TABLE_ID}`
            WHERE tenant_id = '{tenant_id}' AND date >= '{start_date}'
        """
        
        results = list(bq.query(query).result())
        row = results[0] if results else None
        
        period = "daily" if days <= 1 else "weekly" if days <= 7 else "monthly"
        
        return UsageSummary(
            tenant_id=tenant_id,
            period=period,
            total_ai_tokens=int(row.total_ai_tokens or 0) if row else 0,
            total_ai_cost=float(row.total_ai_cost or 0) if row else 0,
            total_bq_cost=float(row.total_bq_cost or 0) if row else 0,
            total_api_calls=int(row.total_api_calls or 0) if row else 0,
            avg_daily_messages=float(row.avg_daily_messages or 0) if row else 0,
            total_reports=int(row.total_reports or 0) if row else 0,
            total_tasks=int(row.total_tasks or 0) if row else 0,
        )
    
    @classmethod
    def get_all_tenants_usage(cls, days: int = 7) -> List[Dict[str, Any]]:
        """Get usage summary for all tenants"""
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        query = f"""
            SELECT
                tenant_id,
                SUM(ai_tokens) as total_ai_tokens,
                SUM(ai_cost_inr + bq_cost_inr) as total_cost,
                SUM(chat_messages) as total_messages,
                SUM(api_calls) as total_api_calls,
                COUNT(DISTINCT date) as active_days
            FROM `{cls.TABLE_ID}`
            WHERE date >= '{start_date}'
            GROUP BY tenant_id
            ORDER BY total_cost DESC
        """
        
        results = bq.query(query).result()
        return [dict(row) for row in results]
    
    @classmethod
    def get_top_users(cls, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top tenants by cost"""
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        query = f"""
            SELECT
                tenant_id,
                SUM(ai_cost_inr + bq_cost_inr) as total_cost,
                SUM(ai_tokens) as total_tokens,
                SUM(chat_messages) as total_messages
            FROM `{cls.TABLE_ID}`
            WHERE date >= '{start_date}'
            GROUP BY tenant_id
            ORDER BY total_cost DESC
            LIMIT {limit}
        """
        
        results = bq.query(query).result()
        return [dict(row) for row in results]
    
    @classmethod
    def get_cost_breakdown(cls, days: int = 30) -> Dict[str, float]:
        """Get overall cost breakdown by category"""
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        query = f"""
            SELECT
                SUM(ai_cost_inr) as ai_cost,
                SUM(bq_cost_inr) as bq_cost
            FROM `{cls.TABLE_ID}`
            WHERE date >= '{start_date}'
        """
        
        results = list(bq.query(query).result())
        row = results[0] if results else None
        
        ai_cost = float(row.ai_cost or 0) if row else 0
        bq_cost = float(row.bq_cost or 0) if row else 0
        total = ai_cost + bq_cost
        
        return {
            "ai_cost": ai_cost,
            "bq_cost": bq_cost,
            "total": total,
            "ai_percentage": (ai_cost / total * 100) if total > 0 else 0,
            "bq_percentage": (bq_cost / total * 100) if total > 0 else 0,
        }
    
    @classmethod
    def check_usage_limits(cls, tenant_id: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """Check if tenant is within usage limits"""
        today_usage = cls.get_daily_usage(tenant_id)
        
        ai_limit = features.get("ai_limit_daily", 50)
        ai_used = today_usage.ai_tokens if today_usage else 0
        
        return {
            "ai_tokens_used": ai_used,
            "ai_tokens_limit": ai_limit,
            "ai_tokens_remaining": max(0, ai_limit - ai_used),
            "ai_limit_exceeded": ai_used >= ai_limit,
            "percentage_used": (ai_used / ai_limit * 100) if ai_limit > 0 else 0,
        }
    
    @classmethod
    def get_inactive_tenants(cls, days: int = 7) -> List[str]:
        """Get tenants with no activity in the last N days"""
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        
        query = f"""
            SELECT DISTINCT tenant_id FROM `{cls.TABLE_ID}`
            WHERE date < '{cutoff}'
            AND tenant_id NOT IN (
                SELECT DISTINCT tenant_id FROM `{cls.TABLE_ID}`
                WHERE date >= '{cutoff}'
            )
        """
        
        results = bq.query(query).result()
        return [row.tenant_id for row in results]
