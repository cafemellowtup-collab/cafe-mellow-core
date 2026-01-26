"""
Domain Event Definitions
"""
from datetime import datetime
from typing import Dict, Any
from .bus import Event


def create_event(event_type: str, org_id: str, location_id: str, payload: Dict[str, Any]) -> Event:
    """Helper to create events"""
    return Event(
        event_type=event_type,
        timestamp=datetime.utcnow(),
        org_id=org_id,
        location_id=location_id,
        payload=payload
    )


class SalesSyncedEvent(Event):
    """Emitted when sales data is synced from POS"""
    event_type: str = "sales.synced"


class ExpenseCreatedEvent(Event):
    """Emitted when a new expense is created"""
    event_type: str = "expense.created"


class DataQualityChangedEvent(Event):
    """Emitted when data quality score changes tier"""
    event_type: str = "data_quality.changed"


class PayrollProcessedEvent(Event):
    """Emitted when payroll is processed"""
    event_type: str = "payroll.processed"
