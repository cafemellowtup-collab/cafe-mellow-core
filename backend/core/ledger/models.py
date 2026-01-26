"""
Universal Ledger Models
Single source of truth for all financial events
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal


class LedgerType(str, Enum):
    """Universal Ledger Types"""
    SALE = "SALE"
    EXPENSE = "EXPENSE"
    WASTAGE = "WASTAGE"
    TOPUP = "TOPUP"
    WITHDRAWAL = "WITHDRAWAL"
    LOAN = "LOAN"
    DIVIDEND = "DIVIDEND"
    SALARY_ADVANCE = "SALARY_ADVANCE"
    PURCHASE = "PURCHASE"
    INVENTORY_ADJUSTMENT = "INVENTORY_ADJUSTMENT"


class LedgerSource(str, Enum):
    """Entry Source Systems"""
    POS_PETPOOJA = "pos_petpooja"
    GOOGLE_DRIVE = "google_drive"
    MANUAL_ENTRY = "manual_entry"
    SYSTEM_GENERATED = "system_generated"
    API_INTEGRATION = "api_integration"


class LedgerEntry(BaseModel):
    """
    Universal Ledger Entry
    This is the single source of truth for all financial events
    """
    id: str = Field(description="UUID for this entry")
    
    org_id: str = Field(description="Organization ID (Tenant Isolation)")
    location_id: str = Field(description="Location ID (Multi-location support)")
    
    timestamp: datetime = Field(description="Transaction timestamp")
    entry_date: datetime = Field(description="Accounting date (for period closing)")
    
    type: LedgerType = Field(description="Type of ledger entry")
    amount: Decimal = Field(description="Amount in base currency (INR)")
    
    entry_source: LedgerSource = Field(description="Source system that created this entry")
    source_id: Optional[str] = Field(default=None, description="ID in source system (e.g., order_id, expense_id)")
    
    entity_id: Optional[str] = Field(default=None, description="Related Entity (Employee/Vendor)")
    entity_name: Optional[str] = Field(default=None, description="Entity name for quick reference")
    
    category: Optional[str] = Field(default=None, description="Category/Ledger name")
    subcategory: Optional[str] = Field(default=None, description="Subcategory")
    
    description: Optional[str] = Field(default=None, description="Human-readable description")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Flexible JSON metadata")
    
    is_verified: bool = Field(default=False, description="Has been verified by manager")
    is_locked: bool = Field(default=False, description="Locked for period closing")
    
    created_by: Optional[str] = Field(default=None, description="User ID who created this entry")
    verified_by: Optional[str] = Field(default=None, description="User ID who verified")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat(),
        }


class LedgerQuery(BaseModel):
    """Query parameters for ledger search"""
    org_id: str
    location_id: Optional[str] = None
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    types: Optional[list[LedgerType]] = None
    sources: Optional[list[LedgerSource]] = None
    entity_id: Optional[str] = None
    category: Optional[str] = None
    
    is_verified: Optional[bool] = None
    is_locked: Optional[bool] = None
    
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)
