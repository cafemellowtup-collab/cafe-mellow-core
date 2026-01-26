"""
GENESIS PROTOCOL - Input Validators
Robust validation for all inputs to prevent crashes
"""
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from typing import Optional, List
from backend.core.exceptions import LedgerValidationError, TenantIsolationError


class TenantValidator:
    """Validates tenant isolation parameters"""
    
    @staticmethod
    def validate_org_id(org_id: str) -> str:
        """Validate org_id format"""
        if not org_id or not org_id.strip():
            raise TenantIsolationError("org_id cannot be empty")
        
        if org_id == "*":
            return org_id  # Wildcard for system events
        
        # Alphanumeric, underscore, hyphen only
        if not re.match(r'^[a-zA-Z0-9_-]+$', org_id):
            raise TenantIsolationError(f"Invalid org_id format: {org_id}")
        
        if len(org_id) > 100:
            raise TenantIsolationError("org_id too long (max 100 chars)")
        
        return org_id.strip()
    
    @staticmethod
    def validate_location_id(location_id: str) -> str:
        """Validate location_id format"""
        if not location_id or not location_id.strip():
            raise TenantIsolationError("location_id cannot be empty")
        
        if location_id == "*":
            return location_id  # Wildcard
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', location_id):
            raise TenantIsolationError(f"Invalid location_id format: {location_id}")
        
        if len(location_id) > 100:
            raise TenantIsolationError("location_id too long (max 100 chars)")
        
        return location_id.strip()


class LedgerValidator:
    """Validates ledger entry inputs"""
    
    @staticmethod
    def validate_amount(amount: float) -> Decimal:
        """Validate and convert amount to Decimal"""
        try:
            decimal_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError) as e:
            raise LedgerValidationError(f"Invalid amount: {amount}")
        
        if decimal_amount < 0:
            raise LedgerValidationError("Amount cannot be negative")
        
        if decimal_amount > Decimal("999999999999.99"):
            raise LedgerValidationError("Amount too large")
        
        # Check decimal places (max 2)
        if decimal_amount.as_tuple().exponent < -2:
            raise LedgerValidationError("Amount can have max 2 decimal places")
        
        return decimal_amount
    
    @staticmethod
    def validate_date(date_str: str) -> date:
        """Validate date string format"""
        try:
            return date.fromisoformat(date_str)
        except (ValueError, AttributeError) as e:
            raise LedgerValidationError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")
    
    @staticmethod
    def validate_timestamp(timestamp_str: str) -> datetime:
        """Validate timestamp string format"""
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            raise LedgerValidationError(f"Invalid timestamp format: {timestamp_str}")
    
    @staticmethod
    def validate_ledger_type(ledger_type: str, allowed_types: List[str]) -> str:
        """Validate ledger type is in allowed list"""
        if ledger_type not in allowed_types:
            raise LedgerValidationError(
                f"Invalid ledger type: {ledger_type}. Allowed: {', '.join(allowed_types)}"
            )
        return ledger_type
    
    @staticmethod
    def validate_source(source: str, allowed_sources: List[str]) -> str:
        """Validate entry source"""
        if source not in allowed_sources:
            raise LedgerValidationError(
                f"Invalid source: {source}. Allowed: {', '.join(allowed_sources)}"
            )
        return source


class QueryValidator:
    """Validates query parameters"""
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> tuple[date, date]:
        """Validate date range"""
        start = LedgerValidator.validate_date(start_date)
        end = LedgerValidator.validate_date(end_date)
        
        if start > end:
            raise LedgerValidationError("start_date cannot be after end_date")
        
        # Prevent overly large ranges (e.g., > 2 years)
        days_diff = (end - start).days
        if days_diff > 730:
            raise LedgerValidationError("Date range too large (max 2 years)")
        
        return start, end
    
    @staticmethod
    def validate_days_param(days: int) -> int:
        """Validate days parameter"""
        if days < 1:
            raise LedgerValidationError("days must be >= 1")
        
        if days > 365:
            raise LedgerValidationError("days cannot exceed 365")
        
        return days
    
    @staticmethod
    def validate_limit(limit: Optional[int], max_limit: int = 1000) -> int:
        """Validate query limit"""
        if limit is None:
            return 100  # Default
        
        if limit < 1:
            raise LedgerValidationError("limit must be >= 1")
        
        if limit > max_limit:
            raise LedgerValidationError(f"limit cannot exceed {max_limit}")
        
        return limit


class EntityValidator:
    """Validates entity (employee/vendor) inputs"""
    
    @staticmethod
    def validate_phone(phone: Optional[str]) -> Optional[str]:
        """Validate phone number"""
        if not phone:
            return None
        
        # Remove spaces and special chars
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Indian phone: 10 digits or +91 followed by 10 digits
        if not re.match(r'^(\+91)?[6-9]\d{9}$', cleaned):
            raise LedgerValidationError(
                "Invalid phone number. Use 10 digits starting with 6-9 or +91XXXXXXXXXX"
            )
        
        return cleaned
    
    @staticmethod
    def validate_email(email: Optional[str]) -> Optional[str]:
        """Validate email format"""
        if not email:
            return None
        
        # Basic email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise LedgerValidationError(f"Invalid email format: {email}")
        
        return email.lower().strip()
    
    @staticmethod
    def validate_entity_type(entity_type: str) -> str:
        """Validate entity type"""
        allowed = ["employee", "vendor", "contractor", "partner"]
        if entity_type.lower() not in allowed:
            raise LedgerValidationError(
                f"Invalid entity_type: {entity_type}. Allowed: {', '.join(allowed)}"
            )
        return entity_type.lower()
