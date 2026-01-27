# Master Dashboard Backend Module
# Super Admin Control Center for TITAN ERP

"""
Master Dashboard provides complete control over all tenants:
- Tenant management and onboarding
- Usage analytics and cost tracking
- Feature flags and subscription tiers
- Health monitoring and debugging
- AI watchdog for proactive alerts
- Learning engine for usage patterns
"""

from .tenant_registry import TenantRegistry
from .usage_tracker import UsageTracker
from .feature_manager import FeatureManager
from .health_monitor import HealthMonitor
from .ai_watchdog import AIWatchdog

__all__ = [
    "TenantRegistry",
    "UsageTracker", 
    "FeatureManager",
    "HealthMonitor",
    "AIWatchdog"
]
