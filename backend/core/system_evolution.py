"""
System Evolution Module - The Creator Feedback Loop
====================================================
Phase 5: Tracks friction points and suggests features to the Master.

This module:
- Logs friction points (missing features, repeated requests)
- Detects patterns in user behavior
- Uses Gemini to summarize and suggest new features
- Creates an "Evolution Log" for the Master to review
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import Counter

# Windows encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from google import genai
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# Configuration
# =============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
_genai_client = None
if GEMINI_API_KEY:
    _genai_client = genai.Client(api_key=GEMINI_API_KEY)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
EVOLUTION_LOG_FILE = DATA_DIR / "system_evolution_log.json"


# =============================================================================
# Friction Point Types
# =============================================================================

class FrictionType:
    """Types of friction points the system can detect."""
    MISSING_FEATURE = "missing_feature"
    REPEATED_REQUEST = "repeated_request"
    ERROR_PATTERN = "error_pattern"
    UNHANDLED_QUERY = "unhandled_query"
    PERFORMANCE_ISSUE = "performance_issue"
    DATA_GAP = "data_gap"
    USER_CONFUSION = "user_confusion"


# =============================================================================
# System Evolution
# =============================================================================

class SystemEvolution:
    """
    The Creator Feedback Loop.
    
    Tracks friction points and suggests features to the Master.
    This is the AI's way of communicating "Hey, users want X".
    """
    
    def __init__(self):
        self._log: List[Dict[str, Any]] = []
        self._client = _genai_client
        
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load existing log
        self._load_log()
        
        print("[EVOLUTION] System Evolution module initialized")
    
    def _load_log(self):
        """Load evolution log from file."""
        if EVOLUTION_LOG_FILE.exists():
            try:
                with open(EVOLUTION_LOG_FILE, 'r', encoding='utf-8') as f:
                    self._log = json.load(f)
                print(f"[EVOLUTION] Loaded {len(self._log)} friction points")
            except Exception as e:
                print(f"[EVOLUTION] Error loading log: {e}")
                self._log = []
        else:
            self._log = []
    
    def _save_log(self):
        """Save evolution log to file."""
        try:
            with open(EVOLUTION_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[EVOLUTION] Error saving log: {e}")
    
    def log_friction_point(self, event_type: str, details: str, 
                           tenant_id: Optional[str] = None,
                           metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Log a friction point in the system.
        
        Args:
            event_type: Type of friction (see FrictionType)
            details: Human-readable description of the friction
            tenant_id: Optional tenant identifier
            metadata: Optional additional data
            
        Returns:
            The logged friction point entry
        """
        entry = {
            "id": f"friction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._log)}",
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details,
            "tenant_id": tenant_id,
            "metadata": metadata or {},
            "resolved": False,
            "feature_suggested": None
        }
        
        self._log.append(entry)
        self._save_log()
        
        print(f"[EVOLUTION] Logged friction: {event_type} - {details[:50]}...")
        
        # Check for patterns
        self._detect_patterns(event_type, details)
        
        return entry
    
    def _detect_patterns(self, event_type: str, details: str):
        """Detect patterns in friction points."""
        # Count similar events
        similar_count = sum(
            1 for entry in self._log 
            if entry["event_type"] == event_type 
            and self._similarity_score(entry["details"], details) > 0.5
        )
        
        if similar_count >= 5:
            print(f"[EVOLUTION] PATTERN DETECTED: {event_type} occurred {similar_count} times")
    
    def _similarity_score(self, text1: str, text2: str) -> float:
        """Simple word overlap similarity."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        overlap = len(words1 & words2)
        return overlap / max(len(words1), len(words2))
    
    def get_friction_summary(self) -> Dict[str, Any]:
        """Get a summary of all friction points."""
        if not self._log:
            return {
                "total_points": 0,
                "by_type": {},
                "recent": [],
                "patterns": []
            }
        
        # Count by type
        type_counts = Counter(entry["event_type"] for entry in self._log)
        
        # Recent entries (last 10)
        recent = sorted(self._log, key=lambda x: x["timestamp"], reverse=True)[:10]
        
        # Detect patterns (events occurring 3+ times)
        patterns = []
        detail_counts = Counter(entry["details"][:100] for entry in self._log)
        for detail, count in detail_counts.most_common(10):
            if count >= 3:
                patterns.append({
                    "pattern": detail,
                    "count": count,
                    "action_needed": count >= 5
                })
        
        return {
            "total_points": len(self._log),
            "by_type": dict(type_counts),
            "recent": recent,
            "patterns": patterns,
            "unresolved": sum(1 for e in self._log if not e["resolved"])
        }
    
    def suggest_features_to_master(self) -> List[Dict[str, Any]]:
        """
        Analyze friction log and suggest features to the Master.
        
        Uses Gemini to:
        1. Identify common pain points
        2. Suggest specific features to build
        3. Prioritize based on frequency and impact
        
        Returns:
            List of feature suggestions with priority and reasoning
        """
        if not self._log:
            return [{
                "suggestion": "No friction points logged yet",
                "priority": "low",
                "reasoning": "System is running smoothly or needs more data"
            }]
        
        # Prepare summary for AI
        summary = self.get_friction_summary()
        
        prompt = f"""You are the AI Evolution Advisor for TITAN ERP - a business management system.

Analyze these friction points from user interactions and suggest features to build:

## Friction Summary
- Total friction points: {summary['total_points']}
- By type: {json.dumps(summary['by_type'], indent=2)}
- Unresolved: {summary['unresolved']}

## Recent Friction Points
{json.dumps(summary['recent'][:5], indent=2)}

## Detected Patterns
{json.dumps(summary['patterns'], indent=2)}

## Your Task
Based on this data, suggest features the Master should build. Format as JSON array:

[
  {{
    "feature_name": "Short descriptive name",
    "priority": "critical|high|medium|low",
    "user_impact": "How many users affected / How often this occurs",
    "reasoning": "Why this feature should be built",
    "implementation_hint": "Brief technical suggestion"
  }}
]

Focus on:
1. Features that would eliminate multiple friction points at once
2. Missing modules that users keep asking for
3. UI/UX improvements that reduce confusion

Return ONLY the JSON array, no other text."""

        try:
            if not self._client:
                return [{
                    "suggestion": "Gemini client not available",
                    "priority": "high",
                    "reasoning": "Cannot analyze friction points without AI"
                }]
            
            response = self._client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            text = response.text.strip()
            
            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            suggestions = json.loads(text)
            
            print(f"[EVOLUTION] Generated {len(suggestions)} feature suggestions for Master")
            return suggestions
            
        except Exception as e:
            print(f"[EVOLUTION] AI suggestion failed: {e}")
            
            # Fallback: Generate basic suggestions from patterns
            fallback = []
            for pattern in summary.get("patterns", []):
                if pattern["count"] >= 5:
                    fallback.append({
                        "feature_name": f"Address: {pattern['pattern'][:50]}",
                        "priority": "high" if pattern["count"] >= 10 else "medium",
                        "user_impact": f"Occurred {pattern['count']} times",
                        "reasoning": "Repeated friction point detected",
                        "implementation_hint": "Analyze user requests for this pattern"
                    })
            
            return fallback if fallback else [{
                "suggestion": "Manual review needed",
                "priority": "medium",
                "reasoning": f"AI analysis failed: {str(e)}"
            }]
    
    def mark_resolved(self, friction_id: str, feature_built: Optional[str] = None) -> bool:
        """Mark a friction point as resolved."""
        for entry in self._log:
            if entry["id"] == friction_id:
                entry["resolved"] = True
                entry["resolved_at"] = datetime.now().isoformat()
                entry["feature_suggested"] = feature_built
                self._save_log()
                print(f"[EVOLUTION] Marked {friction_id} as resolved")
                return True
        return False
    
    def clear_old_entries(self, days: int = 30) -> int:
        """Clear friction points older than X days."""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        original_count = len(self._log)
        
        self._log = [
            entry for entry in self._log 
            if datetime.fromisoformat(entry["timestamp"]) > cutoff
        ]
        
        removed = original_count - len(self._log)
        if removed > 0:
            self._save_log()
            print(f"[EVOLUTION] Cleared {removed} old friction points")
        
        return removed


# =============================================================================
# Global Instance
# =============================================================================

_evolution: Optional[SystemEvolution] = None


def get_evolution() -> SystemEvolution:
    """Get or create global SystemEvolution instance."""
    global _evolution
    if _evolution is None:
        _evolution = SystemEvolution()
    return _evolution


def log_friction(event_type: str, details: str, **kwargs) -> Dict[str, Any]:
    """Convenience function to log friction points."""
    evolution = get_evolution()
    return evolution.log_friction_point(event_type, details, **kwargs)


def suggest_features() -> List[Dict[str, Any]]:
    """Convenience function to get feature suggestions."""
    evolution = get_evolution()
    return evolution.suggest_features_to_master()
