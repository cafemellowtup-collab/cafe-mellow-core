"""
TITAN v3 - Self-Evolving Intelligence System
============================================
The next evolution of TITAN AI with:
- Dual-Heart Personality (Predator/Partner modes)
- SQL-GraphRAG (Deep reasoning without GraphDB)
- Phoenix Protocols (Self-Healing Code)
- Active Senses (Weather, Market Data)
- Evolution Core (Continuous Learning)
"""

from .personality_engine import PersonalityEngine, PersonalityMode
from .graph_rag import GraphRAG
from .phoenix_protocols import PhoenixProtocols, auto_heal, HealingStatus
from .active_senses import ActiveSenses, WeatherContext, MarketContext
from .evolution_core import EvolutionCore, LearningType, ConfidenceLevel
from .unified_engine import TitanV3Engine, TitanResponse, get_titan_engine

__version__ = "3.0.0"
__all__ = [
    "PersonalityEngine",
    "PersonalityMode", 
    "GraphRAG",
    "PhoenixProtocols",
    "auto_heal",
    "HealingStatus",
    "ActiveSenses",
    "WeatherContext",
    "MarketContext",
    "EvolutionCore",
    "LearningType",
    "ConfidenceLevel",
    "TitanV3Engine",
    "TitanResponse",
    "get_titan_engine",
]
