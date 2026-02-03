"""
Master Config Module - God Mode Control Center
==============================================
Phase 6: Central Manager for Tenant Configs & Global Rules.

This module allows the Master to:
- Enable/disable features per tenant
- Inject global rules into the AI's behavior
- Control system-wide settings without touching core logic
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Windows encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TENANT_CONFIGS_FILE = DATA_DIR / "tenant_configs.json"
GLOBAL_RULES_FILE = DATA_DIR / "global_rules.json"


# =============================================================================
# Default Feature Set
# =============================================================================

DEFAULT_FEATURES = {
    "simulation_mode": True,
    "query_engine": True,
    "payroll": True,
    "inventory": True,
    "sales_analytics": True,
    "hr_module": True,
    "export_excel": True,
    "deep_history": True,
    "ai_suggestions": True,
    "data_ingestion": True,
}


# =============================================================================
# Master Config
# =============================================================================

class MasterConfig:
    """
    God Mode Control Center.
    
    Manages tenant-specific feature flags and global AI rules.
    The Master's commands flow through here to control the entire system.
    """
    
    def __init__(self):
        self._tenant_configs: Dict[str, Dict[str, Any]] = {}
        self._global_rules: List[Dict[str, Any]] = []
        
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load existing configs
        self._load_tenant_configs()
        self._load_global_rules()
        
        print("[MASTER CONFIG] Initialized - God Mode Active")
    
    # =========================================================================
    # Tenant Config Management
    # =========================================================================
    
    def _load_tenant_configs(self):
        """Load tenant configs from file."""
        if TENANT_CONFIGS_FILE.exists():
            try:
                with open(TENANT_CONFIGS_FILE, 'r', encoding='utf-8') as f:
                    self._tenant_configs = json.load(f)
                print(f"[MASTER CONFIG] Loaded configs for {len(self._tenant_configs)} tenants")
            except Exception as e:
                print(f"[MASTER CONFIG] Error loading tenant configs: {e}")
                self._tenant_configs = {}
        else:
            self._tenant_configs = {}
    
    def _save_tenant_configs(self):
        """Save tenant configs to file."""
        try:
            with open(TENANT_CONFIGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._tenant_configs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MASTER CONFIG] Error saving tenant configs: {e}")
    
    def set_tenant_feature(self, tenant_id: str, feature: str, is_enabled: bool) -> Dict[str, Any]:
        """
        Enable or disable a feature for a specific tenant.
        
        Args:
            tenant_id: The tenant identifier
            feature: Feature name (e.g., 'payroll', 'simulation_mode')
            is_enabled: True to enable, False to disable
            
        Returns:
            Updated tenant config
        """
        # Initialize tenant config if not exists
        if tenant_id not in self._tenant_configs:
            self._tenant_configs[tenant_id] = {
                "features": DEFAULT_FEATURES.copy(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        
        # Update feature
        self._tenant_configs[tenant_id]["features"][feature] = is_enabled
        self._tenant_configs[tenant_id]["updated_at"] = datetime.now().isoformat()
        
        # Save
        self._save_tenant_configs()
        
        status = "ENABLED" if is_enabled else "DISABLED"
        print(f"[MASTER CONFIG] Tenant '{tenant_id}': {feature} -> {status}")
        
        return self._tenant_configs[tenant_id]
    
    def get_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get configuration for a tenant.
        
        Args:
            tenant_id: The tenant identifier
            
        Returns:
            Tenant config dict (with defaults if not configured)
        """
        if tenant_id in self._tenant_configs:
            config = self._tenant_configs[tenant_id].copy()
            # Merge with defaults for any missing features
            for feature, default_value in DEFAULT_FEATURES.items():
                if feature not in config.get("features", {}):
                    config.setdefault("features", {})[feature] = default_value
            return config
        
        # Return default config
        return {
            "features": DEFAULT_FEATURES.copy(),
            "created_at": None,
            "updated_at": None,
            "is_default": True
        }
    
    def is_feature_enabled(self, tenant_id: str, feature: str) -> bool:
        """
        Check if a feature is enabled for a tenant.
        
        Args:
            tenant_id: The tenant identifier
            feature: Feature name
            
        Returns:
            True if enabled, False if disabled
        """
        config = self.get_tenant_config(tenant_id)
        return config.get("features", {}).get(feature, True)
    
    def get_disabled_features(self, tenant_id: str) -> List[str]:
        """
        Get list of disabled features for a tenant.
        
        Args:
            tenant_id: The tenant identifier
            
        Returns:
            List of disabled feature names
        """
        config = self.get_tenant_config(tenant_id)
        features = config.get("features", {})
        return [f for f, enabled in features.items() if not enabled]
    
    def list_all_tenants(self) -> List[Dict[str, Any]]:
        """List all configured tenants."""
        tenants = []
        for tenant_id, config in self._tenant_configs.items():
            disabled_count = len(self.get_disabled_features(tenant_id))
            tenants.append({
                "tenant_id": tenant_id,
                "disabled_features": disabled_count,
                "updated_at": config.get("updated_at")
            })
        return tenants
    
    # =========================================================================
    # Global Rules Management
    # =========================================================================
    
    def _load_global_rules(self):
        """Load global rules from file."""
        if GLOBAL_RULES_FILE.exists():
            try:
                with open(GLOBAL_RULES_FILE, 'r', encoding='utf-8') as f:
                    self._global_rules = json.load(f)
                print(f"[MASTER CONFIG] Loaded {len(self._global_rules)} global rules")
            except Exception as e:
                print(f"[MASTER CONFIG] Error loading global rules: {e}")
                self._global_rules = []
        else:
            self._global_rules = []
    
    def _save_global_rules(self):
        """Save global rules to file."""
        try:
            with open(GLOBAL_RULES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._global_rules, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MASTER CONFIG] Error saving global rules: {e}")
    
    def set_global_rule(self, rule_text: str, priority: int = 0, 
                        category: str = "general") -> Dict[str, Any]:
        """
        Add or update a global rule for the AI.
        
        Args:
            rule_text: The rule instruction (e.g., "Be polite and professional")
            priority: Higher priority rules are applied first (default: 0)
            category: Rule category for organization
            
        Returns:
            The created/updated rule
        """
        rule = {
            "id": f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._global_rules)}",
            "text": rule_text,
            "priority": priority,
            "category": category,
            "created_at": datetime.now().isoformat(),
            "active": True
        }
        
        self._global_rules.append(rule)
        self._save_global_rules()
        
        print(f"[MASTER CONFIG] Added global rule: {rule_text[:50]}...")
        
        return rule
    
    def get_global_rules(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get all global rules, sorted by priority.
        
        Args:
            active_only: If True, only return active rules
            
        Returns:
            List of rules sorted by priority (highest first)
        """
        rules = self._global_rules
        if active_only:
            rules = [r for r in rules if r.get("active", True)]
        
        # Sort by priority (highest first)
        return sorted(rules, key=lambda x: x.get("priority", 0), reverse=True)
    
    def get_rules_text(self) -> str:
        """
        Get all active rules as a single text block for injection.
        
        Returns:
            Formatted rules text for prompt injection
        """
        rules = self.get_global_rules(active_only=True)
        if not rules:
            return ""
        
        lines = ["## Master's Global Rules (MUST FOLLOW):"]
        for rule in rules:
            lines.append(f"- {rule['text']}")
        
        return "\n".join(lines)
    
    def deactivate_rule(self, rule_id: str) -> bool:
        """Deactivate a global rule."""
        for rule in self._global_rules:
            if rule["id"] == rule_id:
                rule["active"] = False
                rule["deactivated_at"] = datetime.now().isoformat()
                self._save_global_rules()
                print(f"[MASTER CONFIG] Deactivated rule: {rule_id}")
                return True
        return False
    
    def clear_all_rules(self) -> int:
        """Clear all global rules."""
        count = len(self._global_rules)
        self._global_rules = []
        self._save_global_rules()
        print(f"[MASTER CONFIG] Cleared {count} global rules")
        return count
    
    # =========================================================================
    # Feature-Specific Prompt Injection
    # =========================================================================
    
    def get_feature_restrictions_prompt(self, tenant_id: str) -> str:
        """
        Generate prompt text for disabled features.
        
        This is injected into the AI's context to make it aware
        of what features the tenant cannot access.
        
        Args:
            tenant_id: The tenant identifier
            
        Returns:
            Prompt text describing disabled features
        """
        disabled = self.get_disabled_features(tenant_id)
        if not disabled:
            return ""
        
        # Map feature names to user-friendly descriptions
        feature_descriptions = {
            "simulation_mode": "Simulation/What-if analysis",
            "payroll": "Payroll management",
            "inventory": "Inventory tracking",
            "sales_analytics": "Sales analytics and reports",
            "hr_module": "HR and employee management",
            "export_excel": "Export to Excel",
            "deep_history": "Historical data analysis",
            "ai_suggestions": "AI-powered suggestions",
            "data_ingestion": "Data import/ingestion",
            "query_engine": "Natural language queries"
        }
        
        lines = ["## Feature Restrictions for This User:"]
        lines.append("The following features are DISABLED for this user's plan:")
        
        for feature in disabled:
            desc = feature_descriptions.get(feature, feature.replace("_", " ").title())
            lines.append(f"- {desc} (feature: {feature})")
        
        lines.append("")
        lines.append("IMPORTANT: If the user asks about ANY disabled feature:")
        lines.append("1. Politely inform them this feature is not available on their current plan")
        lines.append("2. Suggest they contact support or upgrade to access this feature")
        lines.append("3. Do NOT attempt to provide the restricted functionality")
        
        return "\n".join(lines)


# =============================================================================
# Global Instance
# =============================================================================

_master_config: Optional[MasterConfig] = None


def get_master_config() -> MasterConfig:
    """Get or create global MasterConfig instance."""
    global _master_config
    if _master_config is None:
        _master_config = MasterConfig()
    return _master_config


# =============================================================================
# Convenience Functions
# =============================================================================

def is_feature_enabled(tenant_id: str, feature: str) -> bool:
    """Check if a feature is enabled for a tenant."""
    return get_master_config().is_feature_enabled(tenant_id, feature)


def set_feature(tenant_id: str, feature: str, enabled: bool) -> Dict[str, Any]:
    """Enable/disable a feature for a tenant."""
    return get_master_config().set_tenant_feature(tenant_id, feature, enabled)


def add_rule(rule_text: str, **kwargs) -> Dict[str, Any]:
    """Add a global rule."""
    return get_master_config().set_global_rule(rule_text, **kwargs)
