"""
Tenant Registry - Central management for all tenants
Handles: CRUD operations, credentials vault, onboarding, status management
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from enum import Enum
from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError

# Centralized config - NO HARDCODED PROJECT IDs
from pillars.config_vault import get_bq_config

PROJECT_ID, DATASET_ID = get_bq_config()
_bq_init_error: Optional[Exception] = None
try:
    bq = bigquery.Client(project=PROJECT_ID) if PROJECT_ID else None
except DefaultCredentialsError as e:
    bq = None
    _bq_init_error = e
except Exception as e:
    bq = None
    _bq_init_error = e


class TenantPlan(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    SUSPENDED = "suspended"
    TRIAL = "trial"


@dataclass
class TenantCredentials:
    """Encrypted credentials vault for a tenant"""
    gemini_api_key: Optional[str] = None
    petpooja_app_key: Optional[str] = None
    petpooja_app_secret: Optional[str] = None
    petpooja_access_token: Optional[str] = None
    drive_folder_expenses: Optional[str] = None
    drive_folder_purchases: Optional[str] = None
    drive_folder_inventory: Optional[str] = None
    custom_keys: Dict[str, str] = field(default_factory=dict)


@dataclass
class TenantSettings:
    """Tenant-specific settings"""
    timezone: str = "Asia/Kolkata"
    currency: str = "INR"
    date_format: str = "DD/MM/YYYY"
    ai_model: str = "gemini-2.0-flash"
    ai_temperature: float = 0.3
    daily_brief_time: str = "06:00"
    notification_email: bool = True
    notification_sms: bool = False


@dataclass
class Tenant:
    """Complete tenant record"""
    tenant_id: str
    name: str
    email: str
    phone: Optional[str] = None
    plan: TenantPlan = TenantPlan.FREE
    status: TenantStatus = TenantStatus.TRIAL
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: Optional[datetime] = None
    health_score: float = 100.0
    features: Dict[str, bool] = field(default_factory=dict)
    credentials: TenantCredentials = field(default_factory=TenantCredentials)
    settings: TenantSettings = field(default_factory=TenantSettings)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TenantRegistry:
    """
    Central registry for all tenant management operations
    """
    
    def _get_table_id():
        return f"{PROJECT_ID}.{DATASET_ID}.tenant_registry"
    
    @property
    def TABLE_ID(self):
        return self._get_table_id()
    
    # Default features by plan
    PLAN_FEATURES = {
        TenantPlan.FREE: {
            "chat": True,
            "dashboard": True,
            "operations": True,
            "reports_basic": True,
            "reports_ai": False,
            "tasks": False,
            "api_access": False,
            "multi_location": False,
            "custom_branding": False,
            "priority_support": False,
            "ai_limit_daily": 50,
            "storage_gb": 1,
        },
        TenantPlan.PRO: {
            "chat": True,
            "dashboard": True,
            "operations": True,
            "reports_basic": True,
            "reports_ai": True,
            "tasks": True,
            "api_access": True,
            "multi_location": False,
            "custom_branding": False,
            "priority_support": True,
            "ai_limit_daily": 500,
            "storage_gb": 10,
        },
        TenantPlan.ENTERPRISE: {
            "chat": True,
            "dashboard": True,
            "operations": True,
            "reports_basic": True,
            "reports_ai": True,
            "tasks": True,
            "api_access": True,
            "multi_location": True,
            "custom_branding": True,
            "priority_support": True,
            "ai_limit_daily": 5000,
            "storage_gb": 100,
        },
    }
    
    @classmethod
    def init_table(cls):
        """Initialize the tenant_registry table in BigQuery"""
        schema = [
            bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("email", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("phone", "STRING"),
            bigquery.SchemaField("plan", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("last_activity", "TIMESTAMP"),
            bigquery.SchemaField("health_score", "FLOAT64"),
            bigquery.SchemaField("features", "JSON"),
            bigquery.SchemaField("credentials", "JSON"),
            bigquery.SchemaField("settings", "JSON"),
            bigquery.SchemaField("metadata", "JSON"),
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
    def generate_tenant_id(cls, name: str) -> str:
        """Generate unique tenant ID from name"""
        base = name.lower().replace(" ", "_")[:20]
        suffix = hashlib.md5(f"{base}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        return f"{base}_{suffix}"
    
    @classmethod
    def create_tenant(
        cls,
        name: str,
        email: str,
        phone: Optional[str] = None,
        plan: TenantPlan = TenantPlan.FREE,
    ) -> Tenant:
        """Create a new tenant with default settings"""
        tenant_id = cls.generate_tenant_id(name)
        
        # Get default features for plan
        features = cls.PLAN_FEATURES.get(plan, cls.PLAN_FEATURES[TenantPlan.FREE]).copy()
        
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            email=email,
            phone=phone,
            plan=plan,
            status=TenantStatus.TRIAL,
            features=features,
        )
        
        # Save to BigQuery
        row = {
            "tenant_id": tenant.tenant_id,
            "name": tenant.name,
            "email": tenant.email,
            "phone": tenant.phone,
            "plan": tenant.plan.value,
            "status": tenant.status.value,
            "created_at": tenant.created_at.isoformat(),
            "last_activity": None,
            "health_score": tenant.health_score,
            "features": tenant.features,
            "credentials": asdict(tenant.credentials),
            "settings": asdict(tenant.settings),
            "metadata": tenant.metadata,
        }
        
        errors = bq.insert_rows_json(cls.TABLE_ID, [row])
        if errors:
            raise Exception(f"Failed to create tenant: {errors}")
        
        return tenant
    
    @classmethod
    def get_tenant(cls, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        query = f"""
            SELECT * FROM `{cls.TABLE_ID}`
            WHERE tenant_id = @tenant_id
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("tenant_id", "STRING", tenant_id)
            ]
        )
        
        results = list(bq.query(query, job_config=job_config).result())
        if not results:
            return None
        
        row = results[0]
        return cls._row_to_tenant(row)
    
    @classmethod
    def list_tenants(
        cls,
        status: Optional[TenantStatus] = None,
        plan: Optional[TenantPlan] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Tenant]:
        """List all tenants with optional filters"""
        conditions = []
        params = []
        
        if status:
            conditions.append("status = @status")
            params.append(bigquery.ScalarQueryParameter("status", "STRING", status.value))
        
        if plan:
            conditions.append("plan = @plan")
            params.append(bigquery.ScalarQueryParameter("plan", "STRING", plan.value))
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        query = f"""
            SELECT * FROM `{cls.TABLE_ID}`
            {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
        """
        
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        results = bq.query(query, job_config=job_config).result()
        
        return [cls._row_to_tenant(row) for row in results]
    
    @classmethod
    def update_tenant(cls, tenant_id: str, updates: Dict[str, Any]) -> bool:
        """Update tenant fields"""
        allowed_fields = ["name", "email", "phone", "plan", "status", "health_score", 
                         "features", "credentials", "settings", "metadata", "last_activity"]
        
        set_clauses = []
        for field, value in updates.items():
            if field not in allowed_fields:
                continue
            
            if field in ["features", "credentials", "settings", "metadata"]:
                set_clauses.append(f"{field} = PARSE_JSON('{json.dumps(value)}')")
            elif field == "last_activity":
                set_clauses.append(f"{field} = TIMESTAMP('{value}')")
            elif field in ["plan", "status"]:
                set_clauses.append(f"{field} = '{value.value if hasattr(value, 'value') else value}'")
            else:
                set_clauses.append(f"{field} = '{value}'")
        
        if not set_clauses:
            return False
        
        query = f"""
            UPDATE `{cls.TABLE_ID}`
            SET {', '.join(set_clauses)}
            WHERE tenant_id = '{tenant_id}'
        """
        
        bq.query(query).result()
        return True
    
    @classmethod
    def update_credentials(cls, tenant_id: str, credentials: Dict[str, str]) -> bool:
        """Update tenant credentials (encrypted storage)"""
        tenant = cls.get_tenant(tenant_id)
        if not tenant:
            return False
        
        # Merge with existing credentials
        current = asdict(tenant.credentials)
        current.update(credentials)
        
        return cls.update_tenant(tenant_id, {"credentials": current})
    
    @classmethod
    def update_features(cls, tenant_id: str, features: Dict[str, Any]) -> bool:
        """Update tenant feature flags"""
        tenant = cls.get_tenant(tenant_id)
        if not tenant:
            return False
        
        current = tenant.features.copy()
        current.update(features)
        
        return cls.update_tenant(tenant_id, {"features": current})
    
    @classmethod
    def change_plan(cls, tenant_id: str, new_plan: TenantPlan) -> bool:
        """Change tenant subscription plan"""
        tenant = cls.get_tenant(tenant_id)
        if not tenant:
            return False
        
        # Get new plan features but preserve any custom overrides
        new_features = cls.PLAN_FEATURES.get(new_plan, cls.PLAN_FEATURES[TenantPlan.FREE]).copy()
        
        return cls.update_tenant(tenant_id, {
            "plan": new_plan,
            "features": new_features,
        })
    
    @classmethod
    def pause_tenant(cls, tenant_id: str) -> bool:
        """Pause a tenant account"""
        return cls.update_tenant(tenant_id, {"status": TenantStatus.PAUSED})
    
    @classmethod
    def activate_tenant(cls, tenant_id: str) -> bool:
        """Activate a tenant account"""
        return cls.update_tenant(tenant_id, {"status": TenantStatus.ACTIVE})
    
    @classmethod
    def suspend_tenant(cls, tenant_id: str) -> bool:
        """Suspend a tenant account"""
        return cls.update_tenant(tenant_id, {"status": TenantStatus.SUSPENDED})
    
    @classmethod
    def record_activity(cls, tenant_id: str) -> bool:
        """Record tenant activity timestamp"""
        return cls.update_tenant(tenant_id, {
            "last_activity": datetime.now(timezone.utc).isoformat()
        })
    
    @classmethod
    def get_tenant_count(cls, status: Optional[TenantStatus] = None) -> int:
        """Get total tenant count"""
        where = f"WHERE status = '{status.value}'" if status else ""
        query = f"SELECT COUNT(*) as count FROM `{cls.TABLE_ID}` {where}"
        result = list(bq.query(query).result())[0]
        return result.count
    
    @classmethod
    def _row_to_tenant(cls, row) -> Tenant:
        """Convert BigQuery row to Tenant object"""
        creds_data = row.credentials if isinstance(row.credentials, dict) else {}
        settings_data = row.settings if isinstance(row.settings, dict) else {}
        
        return Tenant(
            tenant_id=row.tenant_id,
            name=row.name,
            email=row.email,
            phone=row.phone,
            plan=TenantPlan(row.plan),
            status=TenantStatus(row.status),
            created_at=row.created_at,
            last_activity=row.last_activity,
            health_score=row.health_score or 100.0,
            features=row.features if isinstance(row.features, dict) else {},
            credentials=TenantCredentials(**creds_data),
            settings=TenantSettings(**settings_data),
            metadata=row.metadata if isinstance(row.metadata, dict) else {},
        )
