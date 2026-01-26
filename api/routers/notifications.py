"""
Notifications Router - Data Freshness Alerts & System Notifications
Provides real-time alerts for data sync status, anomalies, and system events
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from pillars.config_vault import EffectiveSettings

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: str
    type: str  # critical, warning, info, success
    title: str
    message: str
    timestamp: str
    read: bool
    actionUrl: Optional[str] = None


def _get_bq_client():
    try:
        from google.cloud import bigquery
        import os
        
        cfg = EffectiveSettings()
        key_file = getattr(cfg, "KEY_FILE", "service-key.json")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
        
        if not os.path.exists(key_path):
            return None
        return bigquery.Client.from_service_account_json(key_path)
    except Exception:
        return None


def _check_data_freshness(client, cfg) -> List[Dict[str, Any]]:
    """Check data freshness and generate alerts"""
    alerts = []
    project_id = getattr(cfg, "PROJECT_ID", "")
    dataset_id = getattr(cfg, "DATASET_ID", "")
    
    if not project_id or not dataset_id:
        return alerts
    
    now = datetime.now()
    today = now.date()
    
    # Check sales data freshness
    try:
        query = f"""
        SELECT MAX(bill_date) as last_date
        FROM `{project_id}.{dataset_id}.sales_items_parsed`
        """
        result = list(client.query(query).result())
        if result:
            last_sales = result[0].last_date
            if last_sales:
                days_old = (today - last_sales).days
                if days_old > 1:
                    alerts.append({
                        "id": f"sales_stale_{today}",
                        "type": "warning" if days_old < 3 else "critical",
                        "title": "Sales Data Stale",
                        "message": f"Sales data is {days_old} days old. Last sync: {last_sales}. Consider running a sync.",
                        "timestamp": now.isoformat(),
                        "read": False,
                        "actionUrl": "/settings"
                    })
    except Exception:
        pass
    
    # Check expenses data freshness
    try:
        query = f"""
        SELECT MAX(expense_date) as last_date
        FROM `{project_id}.{dataset_id}.expenses_master`
        """
        result = list(client.query(query).result())
        if result:
            last_expenses = result[0].last_date
            if last_expenses:
                days_old = (today - last_expenses).days
                if days_old > 2:
                    alerts.append({
                        "id": f"expenses_stale_{today}",
                        "type": "warning",
                        "title": "Expenses Data Stale",
                        "message": f"Expense data is {days_old} days old. Last entry: {last_expenses}.",
                        "timestamp": now.isoformat(),
                        "read": False,
                        "actionUrl": "/operations"
                    })
    except Exception:
        pass
    
    # Check for pending tasks
    try:
        query = f"""
        SELECT COUNT(*) as cnt
        FROM `{project_id}.{dataset_id}.ai_task_queue`
        WHERE status = 'Pending'
        """
        result = list(client.query(query).result())
        if result and result[0].cnt > 0:
            count = result[0].cnt
            if count >= 5:
                alerts.append({
                    "id": f"pending_tasks_{today}",
                    "type": "info",
                    "title": f"{count} Pending Tasks",
                    "message": f"You have {count} pending AI-generated tasks awaiting action.",
                    "timestamp": now.isoformat(),
                    "read": False,
                    "actionUrl": "/dashboard"
                })
    except Exception:
        pass
    
    # Check for missing recipes (items sold without recipes)
    try:
        query = f"""
        WITH recent_items AS (
            SELECT DISTINCT item_name
            FROM `{project_id}.{dataset_id}.sales_items_parsed`
            WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
              AND item_name IS NOT NULL
              AND item_name != ''
        ),
        recipe_items AS (
            SELECT DISTINCT item_name
            FROM `{project_id}.{dataset_id}.recipe_master`
            WHERE item_name IS NOT NULL
        )
        SELECT COUNT(*) as missing
        FROM recent_items r
        LEFT JOIN recipe_items rec ON LOWER(TRIM(r.item_name)) = LOWER(TRIM(rec.item_name))
        WHERE rec.item_name IS NULL
        """
        result = list(client.query(query).result())
        if result and result[0].missing > 0:
            count = result[0].missing
            if count >= 3:
                alerts.append({
                    "id": f"missing_recipes_{today}",
                    "type": "warning",
                    "title": f"{count} Items Missing Recipes",
                    "message": f"Found {count} items sold in the last 7 days without recipe data.",
                    "timestamp": now.isoformat(),
                    "read": False,
                    "actionUrl": "/chat"
                })
    except Exception:
        pass
    
    return alerts


def _get_system_notifications(client, cfg) -> List[Dict[str, Any]]:
    """Get system-level notifications"""
    notifications = []
    now = datetime.now()
    
    # Add a success notification if data was synced today
    project_id = getattr(cfg, "PROJECT_ID", "")
    dataset_id = getattr(cfg, "DATASET_ID", "")
    
    if project_id and dataset_id:
        try:
            query = f"""
            SELECT MAX(bill_date) as last_date
            FROM `{project_id}.{dataset_id}.sales_items_parsed`
            """
            result = list(client.query(query).result())
            if result and result[0].last_date:
                last_date = result[0].last_date
                if last_date == now.date() or last_date == (now - timedelta(days=1)).date():
                    notifications.append({
                        "id": f"sync_success_{now.date()}",
                        "type": "success",
                        "title": "Data Sync Active",
                        "message": f"Sales data is up to date. Last sync: {last_date}",
                        "timestamp": (now - timedelta(hours=2)).isoformat(),
                        "read": True,
                        "actionUrl": None
                    })
        except Exception:
            pass
    
    return notifications


@router.get("")
async def get_notifications(
    org_id: str = Query(...),
    location_id: str = Query(...)
) -> Dict[str, Any]:
    """Get all notifications for the current user/organization"""
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    notifications = []
    
    if client:
        # Get data freshness alerts
        freshness_alerts = _check_data_freshness(client, cfg)
        notifications.extend(freshness_alerts)
        
        # Get system notifications
        system_notifications = _get_system_notifications(client, cfg)
        notifications.extend(system_notifications)
    
    # Sort by timestamp (newest first), unread first
    notifications.sort(key=lambda x: (x.get("read", False), x.get("timestamp", "")), reverse=True)
    notifications.sort(key=lambda x: x.get("read", False))
    
    return {
        "ok": True,
        "notifications": notifications,
        "unread_count": len([n for n in notifications if not n.get("read", False)])
    }


@router.post("/{notification_id}/read")
async def mark_notification_read(notification_id: str) -> Dict[str, Any]:
    """Mark a notification as read"""
    # In a full implementation, this would update a database
    # For now, we just return success
    return {"ok": True, "message": "Notification marked as read"}


@router.post("/read-all")
async def mark_all_read(
    org_id: str = Query(...),
    location_id: str = Query(...)
) -> Dict[str, Any]:
    """Mark all notifications as read"""
    return {"ok": True, "message": "All notifications marked as read"}
