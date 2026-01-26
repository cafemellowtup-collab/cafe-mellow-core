"""
CITADEL Security Models
Pydantic models for Users, Roles, Permissions, Entities
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, field_validator


class PermissionScope(str, Enum):
    """Permission Scopes (Granular Access Control)"""
    READ_DASHBOARD = "read:dashboard"
    READ_SALES = "read:sales"
    READ_EXPENSES = "read:expenses"
    READ_INVENTORY = "read:inventory"
    READ_HR = "read:hr"
    
    WRITE_EXPENSES = "write:expenses"
    WRITE_INVENTORY = "write:inventory"
    WRITE_HR = "write:hr"
    
    MANAGE_USERS = "manage:users"
    MANAGE_CONFIG = "manage:config"
    MANAGE_INTEGRATIONS = "manage:integrations"
    
    EXECUTE_CRON = "execute:cron"
    ADMIN_FULL = "admin:full"


class Permission(BaseModel):
    """Permission Model"""
    id: str
    scope: PermissionScope
    resource: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Role(BaseModel):
    """Role Model with Scoped Permissions"""
    id: str
    name: str
    description: Optional[str] = None
    permissions: List[PermissionScope] = Field(default_factory=list)
    is_system_role: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class User(BaseModel):
    """User Model (System Login)"""
    id: str
    username: str
    email: EmailStr
    phone: Optional[str] = None
    password_hash: str
    pin_hash: Optional[str] = None
    
    role_ids: List[str] = Field(default_factory=list)
    permissions: List[PermissionScope] = Field(default_factory=list)
    
    org_id: str
    location_ids: List[str] = Field(default_factory=list)
    
    is_active: bool = True
    is_verified: bool = False
    last_login: Optional[datetime] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v and len(v) != 10:
            raise ValueError("Phone must be 10 digits")
        return v


class EntityType(str, Enum):
    """Entity Types (HR/Payroll Distinction)"""
    EMPLOYEE = "employee"
    VENDOR = "vendor"
    CONTRACTOR = "contractor"
    PARTNER = "partner"


class Entity(BaseModel):
    """
    Entity Model (Employees/Vendors)
    CRITICAL DISTINCTION: Entities are NOT Users
    Entities are people/orgs that appear in HR/Payroll/Expenses
    """
    id: str
    entity_type: EntityType
    name: str
    
    org_id: str
    location_id: Optional[str] = None
    
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    
    employee_id: Optional[str] = None
    vendor_code: Optional[str] = None
    
    payment_details: Optional[Dict[str, Any]] = None
    tax_details: Optional[Dict[str, Any]] = None
    
    linked_user_id: Optional[str] = None
    
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TenantContext(BaseModel):
    """Tenant Isolation Context"""
    org_id: str
    location_id: Optional[str] = None
    user_id: str
    
    def get_isolation_filter(self) -> Dict[str, Any]:
        """Returns filter for BigQuery WHERE clause"""
        filters = {"org_id": self.org_id}
        if self.location_id:
            filters["location_id"] = self.location_id
        return filters
    
    def to_sql_where(self) -> str:
        """Generate SQL WHERE clause for tenant isolation"""
        conditions = [f"org_id = '{self.org_id}'"]
        if self.location_id:
            conditions.append(f"location_id = '{self.location_id}'")
        return " AND ".join(conditions)
