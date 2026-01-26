"""
META-COGNITIVE LAYER - Self-Evolution & Knowledge Base
System learns and documents itself
"""
from .knowledge_base import SystemKnowledgeBase, KnowledgeEntry
from .learned_strategies import LearnedStrategiesEngine, Strategy

__all__ = [
    "SystemKnowledgeBase",
    "KnowledgeEntry",
    "LearnedStrategiesEngine",
    "Strategy",
]
