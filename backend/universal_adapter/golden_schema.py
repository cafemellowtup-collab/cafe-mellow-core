"""
Golden Schema - The Law of Valid Data
=====================================
Nothing enters the main database unless it matches these signatures.
This is the "Surity" barrier - the single source of truth for data structure.

Based on existing BigQuery tables:
- sales_orders_enhanced
- sales_order_items_enhanced  
- sales_order_payments
- sales_order_discounts
- expenses
- purchases
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import json


# =============================================================================
# ENUMS - Allowed Values
# =============================================================================

class DataSource(str, Enum):
    """Known data sources - extensible"""
    PETPOOJA = "petpooja"
    EXCEL = "excel"
    GOOGLE_DRIVE = "google_drive"
    ZOHO = "zoho"
    MANUAL = "manual"
    WEBHOOK = "webhook"
    UNKNOWN = "unknown"


class PaymentMode(str, Enum):
    """Payment methods"""
    CASH = "cash"
    CARD = "card"
    UPI = "upi"
    ONLINE = "online"
    CREDIT = "credit"
    WALLET = "wallet"
    OTHER = "other"


class OrderType(str, Enum):
    """Order types"""
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"
    DELIVERY = "delivery"
    PICKUP = "pickup"
    OTHER = "other"


# =============================================================================
# GOLDEN SCHEMA: Sales Order
# =============================================================================

class GoldenOrderItem(BaseModel):
    """Single item in an order - The Law for order line items"""
    item_name: str = Field(..., min_length=1, description="Item name (required)")
    item_id: Optional[str] = Field(default=None, description="Item ID from source system")
    category: Optional[str] = Field(default=None, description="Item category")
    quantity: float = Field(default=1.0, ge=0, description="Quantity ordered")
    unit_price: float = Field(default=0.0, ge=0, description="Price per unit")
    line_total: float = Field(default=0.0, ge=0, description="Total for this line")
    item_discount: float = Field(default=0.0, ge=0, description="Discount on this item")
    tax_rate: float = Field(default=0.0, ge=0, description="Tax rate percentage")
    variant: Optional[str] = Field(default=None, description="Item variant")
    addons: Optional[str] = Field(default=None, description="JSON string of addons")
    special_instructions: Optional[str] = Field(default=None)
    is_cancelled: bool = Field(default=False)
    cancelled_reason: Optional[str] = Field(default=None)

    @field_validator('line_total', mode='before')
    @classmethod
    def calculate_line_total(cls, v, info):
        if v is None or v == 0:
            data = info.data
            qty = data.get('quantity', 1) or 1
            price = data.get('unit_price', 0) or 0
            return qty * price
        return v


class GoldenPayment(BaseModel):
    """Payment record - The Law for payment entries"""
    payment_method: str = Field(..., min_length=1)
    amount: float = Field(..., ge=0)
    status: Optional[str] = Field(default="completed")


class GoldenDiscount(BaseModel):
    """Discount record - The Law for discount entries"""
    discount_name: Optional[str] = Field(default=None)
    discount_type: Optional[str] = Field(default=None)
    amount: float = Field(default=0.0, ge=0)
    reason: Optional[str] = Field(default=None)
    coupon_code: Optional[str] = Field(default=None)


class GoldenOrder(BaseModel):
    """
    THE LAW: A Perfect Sales Order
    ==============================
    This is the Golden Schema for orders. All incoming data must be 
    transformed to match this structure before entering the main database.
    """
    # Required fields
    order_id: str = Field(..., min_length=1, description="Unique order identifier")
    bill_date: date = Field(..., description="Date of the order")
    
    # Financial fields
    order_total: float = Field(default=0.0, ge=0, description="Total order amount")
    subtotal: float = Field(default=0.0, ge=0, description="Subtotal before tax/charges")
    tax_amount: float = Field(default=0.0, ge=0, description="Total tax")
    service_charge: float = Field(default=0.0, ge=0)
    delivery_charge: float = Field(default=0.0, ge=0)
    packing_charge: float = Field(default=0.0, ge=0)
    total_discount: float = Field(default=0.0, ge=0)
    
    # Order metadata
    order_status: Optional[str] = Field(default="completed")
    order_type: Optional[str] = Field(default=None)
    order_time: Optional[str] = Field(default=None)
    payment_mode: Optional[str] = Field(default=None)
    payment_status: Optional[str] = Field(default=None)
    
    # Customer info
    customer_name: Optional[str] = Field(default=None)
    customer_phone: Optional[str] = Field(default=None)
    customer_email: Optional[str] = Field(default=None)
    
    # Delivery info
    delivery_partner: Optional[str] = Field(default=None)
    
    # Staff/Location
    outlet_id: Optional[str] = Field(default=None)
    waiter_name: Optional[str] = Field(default=None)
    table_number: Optional[str] = Field(default=None)
    
    # Promo
    coupon_codes: Optional[str] = Field(default=None)
    
    # Nested data
    items: List[GoldenOrderItem] = Field(default_factory=list)
    payments: List[GoldenPayment] = Field(default_factory=list)
    discounts: List[GoldenDiscount] = Field(default_factory=list)
    
    # Metadata
    source: DataSource = Field(default=DataSource.UNKNOWN)
    raw_json: Optional[str] = Field(default=None, description="Original raw JSON for audit")
    
    @field_validator('bill_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, date):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
        raise ValueError(f"Cannot parse date: {v}")

    @model_validator(mode='after')
    def validate_totals(self):
        """Ensure order total makes sense"""
        if self.items and self.order_total == 0:
            self.order_total = sum(item.line_total for item in self.items)
        return self


# =============================================================================
# GOLDEN SCHEMA: Expense
# =============================================================================

class GoldenExpense(BaseModel):
    """
    THE LAW: A Perfect Expense Record
    =================================
    """
    expense_id: str = Field(..., min_length=1)
    expense_date: date = Field(...)
    
    # Categorization
    category: Optional[str] = Field(default=None)
    ledger_name: str = Field(default="Uncategorized")
    main_category: str = Field(default="Uncategorized")
    
    # Details
    item_name: str = Field(default="")
    amount: float = Field(..., description="Expense amount (must be positive)")
    payment_mode: Optional[str] = Field(default=None)
    staff_name: str = Field(default="Unknown")
    remarks: Optional[str] = Field(default=None)
    
    # Metadata
    source: DataSource = Field(default=DataSource.UNKNOWN)
    source_file: Optional[str] = Field(default=None)

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v < 0:
            raise ValueError("Expense amount cannot be negative")
        return v

    @field_validator('expense_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, date):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
        raise ValueError(f"Cannot parse expense date: {v}")


# =============================================================================
# GOLDEN SCHEMA: Purchase
# =============================================================================

class GoldenPurchase(BaseModel):
    """
    THE LAW: A Perfect Purchase Record
    ==================================
    """
    purchase_id: str = Field(..., min_length=1)
    purchase_date: date = Field(...)
    
    # Vendor
    vendor_name: str = Field(default="Unknown")
    vendor_id: Optional[str] = Field(default=None)
    
    # Item details
    item_name: str = Field(...)
    category: Optional[str] = Field(default=None)
    quantity: float = Field(default=1.0, ge=0)
    unit: Optional[str] = Field(default=None)
    unit_price: float = Field(default=0.0, ge=0)
    total_amount: float = Field(default=0.0, ge=0)
    
    # Payment
    payment_mode: Optional[str] = Field(default=None)
    payment_status: Optional[str] = Field(default=None)
    
    # Metadata
    source: DataSource = Field(default=DataSource.UNKNOWN)
    source_file: Optional[str] = Field(default=None)
    remarks: Optional[str] = Field(default=None)

    @field_validator('purchase_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, date):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
        raise ValueError(f"Cannot parse purchase date: {v}")


# =============================================================================
# RAW LOG SCHEMA - For Airlock
# =============================================================================

class RawLogEntry(BaseModel):
    """
    Raw data as received - stored before any transformation.
    This is what the Airlock saves.
    """
    log_id: str = Field(..., description="Unique log entry ID")
    received_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Source identification
    source_type: str = Field(..., description="API, Excel, Webhook, etc.")
    source_identifier: Optional[str] = Field(default=None, description="Filename, API name, etc.")
    
    # Raw payload
    raw_payload: str = Field(..., description="JSON string of original data")
    content_type: Optional[str] = Field(default="application/json")
    
    # Processing status
    status: Literal["pending", "processing", "completed", "failed", "quarantined"] = Field(default="pending")
    target_schema: Optional[str] = Field(default=None, description="order, expense, purchase, etc.")
    
    # Processing metadata
    processed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    retry_count: int = Field(default=0)


# =============================================================================
# QUARANTINE RECORD
# =============================================================================

class QuarantineRecord(BaseModel):
    """
    Records that failed validation go here for human review.
    """
    quarantine_id: str = Field(...)
    raw_log_id: str = Field(..., description="Reference to original raw_log entry")
    quarantined_at: datetime = Field(default_factory=datetime.utcnow)
    
    # What went wrong
    target_schema: str = Field(..., description="What we tried to convert to")
    validation_errors: List[str] = Field(default_factory=list)
    
    # AI's best attempt
    ai_transformed_data: Optional[str] = Field(default=None, description="JSON of AI's attempt")
    ai_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    
    # Human review
    status: Literal["pending", "approved", "rejected", "auto_fixed"] = Field(default="pending")
    reviewed_by: Optional[str] = Field(default=None)
    reviewed_at: Optional[datetime] = Field(default=None)
    human_corrected_data: Optional[str] = Field(default=None)
    
    # Learning
    correction_notes: Optional[str] = Field(default=None, description="Notes for AI to learn from")


# =============================================================================
# SCHEMA MAPPING CACHE
# =============================================================================

class SchemaMapping(BaseModel):
    """
    Cached field mappings learned from AI or human corrections.
    This speeds up future transformations from known sources.
    """
    mapping_id: str = Field(...)
    source_identifier: str = Field(..., description="e.g., 'petpooja_v2', 'expense_sheet_format_a'")
    target_schema: str = Field(..., description="order, expense, purchase")
    
    # The actual mapping
    field_mappings: Dict[str, str] = Field(..., description="source_field -> target_field")
    transform_rules: Optional[Dict[str, Any]] = Field(default=None, description="Special transform logic")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = Field(default=None)
    use_count: int = Field(default=0)
    confidence: float = Field(default=1.0, ge=0, le=1)
    created_by: Literal["ai", "human"] = Field(default="ai")


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_order(data: Dict[str, Any]) -> tuple[bool, Optional[GoldenOrder], List[str]]:
    """
    Validate data against GoldenOrder schema.
    Returns: (is_valid, validated_object_or_none, list_of_errors)
    """
    try:
        order = GoldenOrder(**data)
        return True, order, []
    except Exception as e:
        errors = []
        if hasattr(e, 'errors'):
            for err in e.errors():
                field = '.'.join(str(x) for x in err.get('loc', []))
                msg = err.get('msg', str(e))
                errors.append(f"{field}: {msg}")
        else:
            errors.append(str(e))
        return False, None, errors


def validate_expense(data: Dict[str, Any]) -> tuple[bool, Optional[GoldenExpense], List[str]]:
    """Validate data against GoldenExpense schema."""
    try:
        expense = GoldenExpense(**data)
        return True, expense, []
    except Exception as e:
        errors = []
        if hasattr(e, 'errors'):
            for err in e.errors():
                field = '.'.join(str(x) for x in err.get('loc', []))
                msg = err.get('msg', str(e))
                errors.append(f"{field}: {msg}")
        else:
            errors.append(str(e))
        return False, None, errors


def validate_purchase(data: Dict[str, Any]) -> tuple[bool, Optional[GoldenPurchase], List[str]]:
    """Validate data against GoldenPurchase schema."""
    try:
        purchase = GoldenPurchase(**data)
        return True, purchase, []
    except Exception as e:
        errors = []
        if hasattr(e, 'errors'):
            for err in e.errors():
                field = '.'.join(str(x) for x in err.get('loc', []))
                msg = err.get('msg', str(e))
                errors.append(f"{field}: {msg}")
        else:
            errors.append(str(e))
        return False, None, errors


# Export schemas for external use
GOLDEN_SCHEMAS = {
    "order": GoldenOrder,
    "expense": GoldenExpense,
    "purchase": GoldenPurchase,
}

def get_schema_json(schema_name: str) -> str:
    """Get JSON schema for AI prompts"""
    schema_class = GOLDEN_SCHEMAS.get(schema_name)
    if schema_class:
        return json.dumps(schema_class.model_json_schema(), indent=2)
    return "{}"
