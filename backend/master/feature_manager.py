"""
Feature Manager - Control feature flags and subscription tiers
Handles: Feature toggles, tier management, A/B testing, rollouts
"""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from google.cloud import bigquery

PROJECT_ID = "cafe-mellow-core-2026"
DATASET_ID = "cafe_operations"
bq = bigquery.Client(project=PROJECT_ID)


@dataclass
class Feature:
    """Feature flag definition"""
    feature_id: str
    name: str
    description: str
    default_enabled: bool = False
    tiers: List[str] = field(default_factory=lambda: ["enterprise"])
    category: str = "general"  # general, ai, reporting, integration
    is_beta: bool = False
    rollout_percentage: int = 100  # for gradual rollouts


@dataclass
class TenantFeatureOverride:
    """Override for a specific tenant"""
    tenant_id: str
    feature_id: str
    enabled: bool
    override_reason: str
    updated_by: str
    updated_at: datetime


# Master feature registry
FEATURE_REGISTRY: Dict[str, Feature] = {
    # Core Features
    "chat": Feature(
        feature_id="chat",
        name="AI Chat",
        description="TITAN CFO conversational AI",
        default_enabled=True,
        tiers=["free", "pro", "enterprise"],
        category="ai",
    ),
    "dashboard": Feature(
        feature_id="dashboard",
        name="Dashboard",
        description="KPI dashboard with analytics",
        default_enabled=True,
        tiers=["free", "pro", "enterprise"],
        category="general",
    ),
    "operations": Feature(
        feature_id="operations",
        name="Operations",
        description="Expense and operations management",
        default_enabled=True,
        tiers=["free", "pro", "enterprise"],
        category="general",
    ),
    
    # Reporting Features
    "reports_basic": Feature(
        feature_id="reports_basic",
        name="Basic Reports",
        description="Pre-styled report templates",
        default_enabled=True,
        tiers=["free", "pro", "enterprise"],
        category="reporting",
    ),
    "reports_ai": Feature(
        feature_id="reports_ai",
        name="AI Reports",
        description="AI-generated custom reports",
        default_enabled=False,
        tiers=["pro", "enterprise"],
        category="reporting",
    ),
    "reports_scheduled": Feature(
        feature_id="reports_scheduled",
        name="Scheduled Reports",
        description="Auto-generate and email reports",
        default_enabled=False,
        tiers=["enterprise"],
        category="reporting",
    ),
    
    # Task Management
    "tasks": Feature(
        feature_id="tasks",
        name="Task Management",
        description="AI-generated task assignment",
        default_enabled=False,
        tiers=["pro", "enterprise"],
        category="general",
    ),
    "tasks_automation": Feature(
        feature_id="tasks_automation",
        name="Task Automation",
        description="Automated task workflows",
        default_enabled=False,
        tiers=["enterprise"],
        category="general",
    ),
    
    # Integration Features
    "api_access": Feature(
        feature_id="api_access",
        name="API Access",
        description="Direct API access for integrations",
        default_enabled=False,
        tiers=["pro", "enterprise"],
        category="integration",
    ),
    "webhooks": Feature(
        feature_id="webhooks",
        name="Webhooks",
        description="Outbound webhook notifications",
        default_enabled=False,
        tiers=["pro", "enterprise"],
        category="integration",
    ),
    "pos_integration": Feature(
        feature_id="pos_integration",
        name="POS Integration",
        description="Petpooja and other POS systems",
        default_enabled=False,
        tiers=["pro", "enterprise"],
        category="integration",
    ),
    
    # Advanced Features
    "multi_location": Feature(
        feature_id="multi_location",
        name="Multi-Location",
        description="Manage multiple business locations",
        default_enabled=False,
        tiers=["enterprise"],
        category="general",
    ),
    "custom_branding": Feature(
        feature_id="custom_branding",
        name="Custom Branding",
        description="White-label with custom branding",
        default_enabled=False,
        tiers=["enterprise"],
        category="general",
    ),
    "priority_support": Feature(
        feature_id="priority_support",
        name="Priority Support",
        description="24/7 priority support access",
        default_enabled=False,
        tiers=["pro", "enterprise"],
        category="general",
    ),
    
    # AI Features
    "ai_voice": Feature(
        feature_id="ai_voice",
        name="Voice Commands",
        description="Voice input for AI commands",
        default_enabled=False,
        tiers=["pro", "enterprise"],
        category="ai",
    ),
    "ai_proactive": Feature(
        feature_id="ai_proactive",
        name="Proactive AI Alerts",
        description="AI sends alerts without prompting",
        default_enabled=False,
        tiers=["enterprise"],
        category="ai",
        is_beta=True,
    ),
    "ai_learning": Feature(
        feature_id="ai_learning",
        name="AI Learning Mode",
        description="AI learns from your decisions",
        default_enabled=False,
        tiers=["enterprise"],
        category="ai",
        is_beta=True,
    ),
    
    # Future Features
    "climate_module": Feature(
        feature_id="climate_module",
        name="Climate Module",
        description="Weather-based demand prediction",
        default_enabled=False,
        tiers=["enterprise"],
        category="ai",
        is_beta=True,
        rollout_percentage=0,
    ),
    "internet_data": Feature(
        feature_id="internet_data",
        name="Internet Data",
        description="External market data integration",
        default_enabled=False,
        tiers=["enterprise"],
        category="integration",
        is_beta=True,
        rollout_percentage=0,
    ),
}


class FeatureManager:
    """
    Manage feature flags and subscription tiers
    """
    
    TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.tenant_features"
    
    @classmethod
    def init_table(cls):
        """Initialize the tenant_features table"""
        schema = [
            bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("feature_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("enabled", "BOOL", mode="REQUIRED"),
            bigquery.SchemaField("override_reason", "STRING"),
            bigquery.SchemaField("updated_by", "STRING"),
            bigquery.SchemaField("updated_at", "TIMESTAMP"),
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
    def get_all_features(cls) -> List[Feature]:
        """Get all available features"""
        return list(FEATURE_REGISTRY.values())
    
    @classmethod
    def get_feature(cls, feature_id: str) -> Optional[Feature]:
        """Get a specific feature"""
        return FEATURE_REGISTRY.get(feature_id)
    
    @classmethod
    def get_features_for_tier(cls, tier: str) -> Dict[str, bool]:
        """Get all features available for a tier"""
        features = {}
        for feature_id, feature in FEATURE_REGISTRY.items():
            features[feature_id] = tier in feature.tiers
        return features
    
    @classmethod
    def is_feature_enabled(cls, tenant_id: str, feature_id: str, tenant_tier: str) -> bool:
        """Check if a feature is enabled for a tenant"""
        # Check for override first
        override = cls._get_override(tenant_id, feature_id)
        if override is not None:
            return override
        
        # Check tier access
        feature = FEATURE_REGISTRY.get(feature_id)
        if not feature:
            return False
        
        # Check rollout percentage
        if feature.rollout_percentage < 100:
            # Simple hash-based rollout
            hash_val = hash(f"{tenant_id}_{feature_id}") % 100
            if hash_val >= feature.rollout_percentage:
                return False
        
        return tenant_tier in feature.tiers
    
    @classmethod
    def set_feature_override(
        cls,
        tenant_id: str,
        feature_id: str,
        enabled: bool,
        reason: str,
        admin_id: str,
    ) -> bool:
        """Set a feature override for a tenant"""
        now = datetime.now(timezone.utc).isoformat()
        
        # Delete existing override if any
        delete_query = f"""
            DELETE FROM `{cls.TABLE_ID}`
            WHERE tenant_id = '{tenant_id}' AND feature_id = '{feature_id}'
        """
        bq.query(delete_query).result()
        
        # Insert new override
        row = {
            "tenant_id": tenant_id,
            "feature_id": feature_id,
            "enabled": enabled,
            "override_reason": reason,
            "updated_by": admin_id,
            "updated_at": now,
        }
        
        errors = bq.insert_rows_json(cls.TABLE_ID, [row])
        return len(errors) == 0
    
    @classmethod
    def remove_feature_override(cls, tenant_id: str, feature_id: str) -> bool:
        """Remove a feature override"""
        query = f"""
            DELETE FROM `{cls.TABLE_ID}`
            WHERE tenant_id = '{tenant_id}' AND feature_id = '{feature_id}'
        """
        bq.query(query).result()
        return True
    
    @classmethod
    def get_tenant_features(cls, tenant_id: str, tenant_tier: str) -> Dict[str, Any]:
        """Get all features for a tenant with their status"""
        result = {}
        
        for feature_id, feature in FEATURE_REGISTRY.items():
            enabled = cls.is_feature_enabled(tenant_id, feature_id, tenant_tier)
            override = cls._get_override(tenant_id, feature_id)
            
            result[feature_id] = {
                "name": feature.name,
                "description": feature.description,
                "enabled": enabled,
                "has_override": override is not None,
                "category": feature.category,
                "is_beta": feature.is_beta,
                "tier_required": feature.tiers[0] if feature.tiers else "enterprise",
            }
        
        return result
    
    @classmethod
    def get_all_overrides(cls, tenant_id: Optional[str] = None) -> List[TenantFeatureOverride]:
        """Get all feature overrides"""
        where = f"WHERE tenant_id = '{tenant_id}'" if tenant_id else ""
        
        query = f"""
            SELECT * FROM `{cls.TABLE_ID}`
            {where}
            ORDER BY updated_at DESC
        """
        
        results = bq.query(query).result()
        return [
            TenantFeatureOverride(
                tenant_id=row.tenant_id,
                feature_id=row.feature_id,
                enabled=row.enabled,
                override_reason=row.override_reason,
                updated_by=row.updated_by,
                updated_at=row.updated_at,
            )
            for row in results
        ]
    
    @classmethod
    def get_features_by_category(cls) -> Dict[str, List[Feature]]:
        """Group features by category"""
        categories = {}
        for feature in FEATURE_REGISTRY.values():
            if feature.category not in categories:
                categories[feature.category] = []
            categories[feature.category].append(feature)
        return categories
    
    @classmethod
    def get_beta_features(cls) -> List[Feature]:
        """Get all beta features"""
        return [f for f in FEATURE_REGISTRY.values() if f.is_beta]
    
    @classmethod
    def _get_override(cls, tenant_id: str, feature_id: str) -> Optional[bool]:
        """Get override value if exists"""
        query = f"""
            SELECT enabled FROM `{cls.TABLE_ID}`
            WHERE tenant_id = '{tenant_id}' AND feature_id = '{feature_id}'
            LIMIT 1
        """
        
        results = list(bq.query(query).result())
        if results:
            return results[0].enabled
        return None
