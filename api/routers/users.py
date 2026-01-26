"""
User Management Router - Role-Based Access Control
Handles user creation, role assignment, and permissions
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr
import json

from pillars.config_vault import EffectiveSettings

router = APIRouter(prefix="/api/v1/users", tags=["users"])


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: str = "viewer"  # admin, manager, analyst, viewer
    org_id: str
    location_id: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None  # active, inactive


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    permissions: List[str]
    org_id: str
    location_id: str
    created_at: str
    last_login: Optional[str] = None
    status: str


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


def _get_permissions_for_role(role: str) -> List[str]:
    """Get permissions list based on role"""
    permissions_map = {
        "admin": ["all", "settings", "users", "data", "ai", "reports", "operations", "delete"],
        "manager": ["data", "ai", "reports", "operations", "team_view"],
        "analyst": ["ai", "reports", "data_view"],
        "viewer": ["dashboard_view", "reports_view"],
    }
    return permissions_map.get(role, ["dashboard_view"])


def _ensure_users_table(client, cfg) -> str:
    """Ensure users table exists"""
    project_id = getattr(cfg, "PROJECT_ID", "")
    dataset_id = getattr(cfg, "DATASET_ID", "")
    table_id = f"{project_id}.{dataset_id}.system_users"
    
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS `{table_id}` (
        id STRING NOT NULL,
        name STRING NOT NULL,
        email STRING NOT NULL,
        role STRING NOT NULL,
        permissions STRING,
        org_id STRING NOT NULL,
        location_id STRING NOT NULL,
        created_at TIMESTAMP NOT NULL,
        last_login TIMESTAMP,
        status STRING DEFAULT 'active'
    )
    """
    try:
        client.query(create_sql).result()
    except Exception:
        pass
    
    return table_id


@router.get("")
async def list_users(
    org_id: str = Query(...),
    location_id: str = Query(...),
    status: str = Query("active")
) -> Dict[str, Any]:
    """List all users for an organization"""
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected")
    
    try:
        table_id = _ensure_users_table(client, cfg)
        
        query = f"""
        SELECT 
            id, name, email, role, permissions, org_id, location_id,
            CAST(created_at AS STRING) as created_at,
            CAST(last_login AS STRING) as last_login,
            status
        FROM `{table_id}`
        WHERE org_id = '{org_id}'
          AND location_id = '{location_id}'
          AND status = '{status}'
        ORDER BY created_at DESC
        """
        
        result = client.query(query).result()
        users = []
        for row in result:
            permissions = json.loads(row.permissions) if row.permissions else []
            users.append({
                "id": row.id,
                "name": row.name,
                "email": row.email,
                "role": row.role,
                "permissions": permissions,
                "org_id": row.org_id,
                "location_id": row.location_id,
                "created_at": row.created_at,
                "last_login": row.last_login,
                "status": row.status,
            })
        
        return {"ok": True, "users": users, "count": len(users)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_user(user: UserCreate) -> Dict[str, Any]:
    """Create a new user"""
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected")
    
    try:
        table_id = _ensure_users_table(client, cfg)
        
        # Check if user already exists
        check_query = f"""
        SELECT COUNT(*) as cnt
        FROM `{table_id}`
        WHERE email = '{user.email}'
          AND org_id = '{user.org_id}'
        """
        result = list(client.query(check_query).result())
        if result and result[0].cnt > 0:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        user_id = f"user_{int(datetime.now().timestamp() * 1000)}"
        permissions = _get_permissions_for_role(user.role)
        permissions_json = json.dumps(permissions)
        
        insert_sql = f"""
        INSERT INTO `{table_id}`
        (id, name, email, role, permissions, org_id, location_id, created_at, status)
        VALUES (
            '{user_id}',
            '{user.name.replace("'", "''")}',
            '{user.email}',
            '{user.role}',
            '{permissions_json}',
            '{user.org_id}',
            '{user.location_id}',
            CURRENT_TIMESTAMP(),
            'active'
        )
        """
        client.query(insert_sql).result()
        
        return {
            "ok": True,
            "user_id": user_id,
            "message": f"User {user.name} created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{user_id}")
async def update_user(user_id: str, update: UserUpdate) -> Dict[str, Any]:
    """Update a user's role or status"""
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected")
    
    try:
        table_id = _ensure_users_table(client, cfg)
        
        updates = []
        if update.name:
            updates.append(f"name = '{update.name.replace(chr(39), chr(39)+chr(39))}'")
        if update.role:
            permissions = _get_permissions_for_role(update.role)
            permissions_json = json.dumps(permissions)
            updates.append(f"role = '{update.role}'")
            updates.append(f"permissions = '{permissions_json}'")
        if update.status:
            updates.append(f"status = '{update.status}'")
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        update_sql = f"""
        UPDATE `{table_id}`
        SET {', '.join(updates)}
        WHERE id = '{user_id}'
        """
        client.query(update_sql).result()
        
        return {"ok": True, "message": "User updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}")
async def delete_user(user_id: str) -> Dict[str, Any]:
    """Soft delete a user (set status to 'deleted')"""
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected")
    
    try:
        table_id = _ensure_users_table(client, cfg)
        
        update_sql = f"""
        UPDATE `{table_id}`
        SET status = 'deleted'
        WHERE id = '{user_id}'
        """
        client.query(update_sql).result()
        
        return {"ok": True, "message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/permissions")
async def get_user_permissions(user_id: str) -> Dict[str, Any]:
    """Get a user's permissions"""
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected")
    
    try:
        table_id = _ensure_users_table(client, cfg)
        
        query = f"""
        SELECT role, permissions
        FROM `{table_id}`
        WHERE id = '{user_id}'
        """
        result = list(client.query(query).result())
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        
        row = result[0]
        permissions = json.loads(row.permissions) if row.permissions else []
        
        return {
            "ok": True,
            "user_id": user_id,
            "role": row.role,
            "permissions": permissions
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
