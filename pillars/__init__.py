# TITAN Modular Pillar Architecture
# All business logic lives here. UI is a window to the logic.

from .evolution import ensure_dev_evolution_table, log_logic_gap, get_evolution_suggestions, update_development_status
from .dashboard import get_revenue_expenses_data, get_sentinel_health, get_ai_observations
from .config_vault import EffectiveSettings, load_config_override, save_config_override
from .system_logger import log_error, ensure_system_error_log_table

__all__ = [
    "ensure_dev_evolution_table",
    "log_logic_gap",
    "get_evolution_suggestions",
    "update_development_status",
    "get_revenue_expenses_data",
    "get_sentinel_health",
    "get_ai_observations",
    "EffectiveSettings",
    "load_config_override",
    "save_config_override",
    "log_error",
    "ensure_system_error_log_table",
]
