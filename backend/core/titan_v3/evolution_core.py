"""
TITAN v3 Evolution Core
=======================
Continuous learning and self-improvement engine.

Features:
1. Pattern Learning - Extract patterns from successful interactions
2. Strategy Evolution - Evolve response strategies based on feedback
3. Knowledge Synthesis - Combine learnings into actionable insights
4. Performance Tracking - Monitor and optimize AI quality
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import os
from google.auth.exceptions import DefaultCredentialsError

from google.cloud import bigquery

try:
    from google import genai
    _GENAI_AVAILABLE = True
except ImportError:
    genai = None
    _GENAI_AVAILABLE = False

# Centralized config - NO HARDCODED PROJECT IDs
from pillars.config_vault import get_bq_config


def _get_bq_client(project_id: str) -> Tuple[Optional[bigquery.Client], Optional[Exception]]:
    try:
        key_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "service-key.json")
        )
        if os.path.exists(key_path):
            return bigquery.Client.from_service_account_json(key_path), None
        return bigquery.Client(project=project_id), None
    except DefaultCredentialsError as e:
        return None, e
    except Exception as e:
        return None, e


class LearningType(str, Enum):
    PATTERN = "pattern"           # Data patterns discovered
    STRATEGY = "strategy"         # Successful response strategies
    CORRECTION = "correction"     # User corrections learned
    OPTIMIZATION = "optimization" # Performance optimizations
    INSIGHT = "insight"          # Business insights generated


class ConfidenceLevel(str, Enum):
    HYPOTHESIS = "hypothesis"    # 0-30% - needs validation
    EMERGING = "emerging"        # 30-60% - some evidence
    CONFIDENT = "confident"      # 60-85% - strong evidence
    PROVEN = "proven"           # 85%+ - consistently validated


@dataclass
class Learning:
    """A learned piece of knowledge"""
    learning_id: str
    learning_type: LearningType
    content: str
    context: Dict[str, Any]
    confidence: float
    confidence_level: ConfidenceLevel
    times_validated: int = 0
    times_contradicted: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    source_interactions: List[str] = field(default_factory=list)


@dataclass
class EvolutionMetrics:
    """Metrics tracking TITAN's evolution"""
    total_learnings: int
    proven_learnings: int
    active_hypotheses: int
    avg_confidence: float
    learning_velocity: float  # learnings per day
    accuracy_trend: str  # improving, stable, declining
    top_learning_areas: List[str]


class EvolutionCore:
    """
    TITAN's Self-Evolution Engine
    
    Enables continuous learning, pattern extraction, and
    strategy optimization based on interactions and feedback.
    """
    
    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
        # Use centralized config
        self.PROJECT_ID, self.DATASET_ID = get_bq_config()
        self.bq_client, self._bq_init_error = _get_bq_client(self.PROJECT_ID) if self.PROJECT_ID else (None, None)
        
        api_key = os.getenv("GEMINI_API_KEY")
        self.genai_client = None
        self.model_name = "gemini-2.0-flash"
        
        if api_key and _GENAI_AVAILABLE:
            try:
                self.genai_client = genai.Client(api_key=api_key)
            except Exception:
                self.genai_client = None
        
        if self.bq_client:
            self._ensure_tables_exist()
        self._learning_cache: Dict[str, Learning] = {}
    
    def _ensure_tables_exist(self):
        """Create evolution tables"""
        if not self.bq_client:
            return
        # Learnings table
        learnings_schema = [
            bigquery.SchemaField("learning_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("tenant_id", "STRING"),
            bigquery.SchemaField("learning_type", "STRING"),
            bigquery.SchemaField("content", "STRING"),
            bigquery.SchemaField("context", "JSON"),
            bigquery.SchemaField("confidence", "FLOAT64"),
            bigquery.SchemaField("confidence_level", "STRING"),
            bigquery.SchemaField("times_validated", "INT64"),
            bigquery.SchemaField("times_contradicted", "INT64"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("last_used", "TIMESTAMP"),
            bigquery.SchemaField("source_interactions", "STRING", mode="REPEATED"),
        ]
        
        # Interactions table for learning source
        interactions_schema = [
            bigquery.SchemaField("interaction_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("tenant_id", "STRING"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("user_query", "STRING"),
            bigquery.SchemaField("ai_response", "STRING"),
            bigquery.SchemaField("response_rating", "INT64"),  # 1-5
            bigquery.SchemaField("personality_mode", "STRING"),
            bigquery.SchemaField("query_type", "STRING"),
            bigquery.SchemaField("response_time_ms", "INT64"),
            bigquery.SchemaField("feedback", "STRING"),
            bigquery.SchemaField("extracted_patterns", "JSON"),
        ]
        
        tables = {
            "titan_learnings": learnings_schema,
            "titan_interactions": interactions_schema,
        }
        
        for table_name, schema in tables.items():
            table_ref = f"{self.PROJECT_ID}.{self.DATASET_ID}.{table_name}"
            try:
                self.bq_client.get_table(table_ref)
            except Exception:
                table = bigquery.Table(table_ref, schema=schema)
                self.bq_client.create_table(table)
    
    def record_interaction(
        self,
        user_query: str,
        ai_response: str,
        personality_mode: str = "hybrid",
        query_type: str = "general",
        response_time_ms: int = 0,
        rating: Optional[int] = None,
        feedback: Optional[str] = None
    ) -> str:
        """Record an interaction for learning"""
        if not self.bq_client:
            return ""
        interaction_id = hashlib.md5(
            f"{self.tenant_id}:{datetime.now().isoformat()}:{user_query[:50]}".encode()
        ).hexdigest()[:16]
        
        # Extract patterns from interaction
        patterns = self._extract_patterns(user_query, ai_response)
        
        row = {
            "interaction_id": interaction_id,
            "tenant_id": self.tenant_id,
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query[:2000],
            "ai_response": ai_response[:5000],
            "response_rating": rating,
            "personality_mode": personality_mode,
            "query_type": query_type,
            "response_time_ms": response_time_ms,
            "feedback": feedback,
            "extracted_patterns": patterns,
        }
        
        table_ref = f"{self.PROJECT_ID}.{self.DATASET_ID}.titan_interactions"
        try:
            self.bq_client.insert_rows_json(table_ref, [row])
        except Exception:
            pass
        
        # Trigger learning if rating is available
        if rating and rating >= 4:
            self._learn_from_success(user_query, ai_response, patterns, interaction_id)
        elif rating and rating <= 2:
            self._learn_from_failure(user_query, ai_response, feedback, interaction_id)
        
        return interaction_id
    
    def _extract_patterns(self, query: str, response: str) -> Dict[str, Any]:
        """Extract learnable patterns from interaction"""
        patterns = {
            "query_length": len(query),
            "response_length": len(response),
            "has_numbers": any(c.isdigit() for c in query),
            "has_question": "?" in query,
            "keywords": [],
            "intent_signals": [],
        }
        
        # Extract keywords
        keywords = [
            "revenue", "profit", "expense", "cost", "sales", "orders",
            "staff", "inventory", "forecast", "trend", "compare", "why",
            "how", "what", "when", "should", "recommend"
        ]
        
        query_lower = query.lower()
        patterns["keywords"] = [k for k in keywords if k in query_lower]
        
        # Detect intent signals
        if any(w in query_lower for w in ["worried", "concerned", "help"]):
            patterns["intent_signals"].append("emotional_support")
        if any(w in query_lower for w in ["show", "display", "chart", "graph"]):
            patterns["intent_signals"].append("visual_data")
        if any(w in query_lower for w in ["why", "reason", "cause"]):
            patterns["intent_signals"].append("explanation")
        if any(w in query_lower for w in ["should", "recommend", "suggest"]):
            patterns["intent_signals"].append("recommendation")
        
        return patterns
    
    def _learn_from_success(
        self,
        query: str,
        response: str,
        patterns: Dict,
        interaction_id: str
    ):
        """Extract learning from successful interaction"""
        if not self.genai_client:
            return
        
        # Use AI to extract the winning strategy
        prompt = f"""Analyze this successful AI interaction and extract the key strategy that made it work.

USER QUERY: {query}

AI RESPONSE (rated highly): {response[:1500]}

DETECTED PATTERNS: {json.dumps(patterns)}

Extract:
1. STRATEGY: What approach made this response successful? (1-2 sentences)
2. TRIGGER: What in the query should trigger this strategy? (specific patterns)
3. APPLICABILITY: What types of queries would benefit from this strategy?

Format as JSON:
{{"strategy": "...", "trigger": "...", "applicability": "..."}}
"""
        
        try:
            result = self.genai_client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            response_text = result.text
            
            # Parse JSON from response
            if "{" in response_text:
                json_str = response_text[response_text.find("{"):response_text.rfind("}")+1]
                learning_data = json.loads(json_str)
                
                self._store_learning(
                    learning_type=LearningType.STRATEGY,
                    content=learning_data.get("strategy", ""),
                    context={
                        "trigger": learning_data.get("trigger", ""),
                        "applicability": learning_data.get("applicability", ""),
                        "source_query": query[:200],
                    },
                    confidence=0.6,
                    source_interaction=interaction_id
                )
        except Exception:
            pass
    
    def _learn_from_failure(
        self,
        query: str,
        response: str,
        feedback: Optional[str],
        interaction_id: str
    ):
        """Learn from failed interaction"""
        if not self.genai_client:
            return
        
        prompt = f"""Analyze this failed AI interaction and identify what went wrong.

USER QUERY: {query}

AI RESPONSE (rated poorly): {response[:1500]}

USER FEEDBACK: {feedback or "No feedback provided"}

Identify:
1. ISSUE: What was wrong with the response?
2. CORRECTION: How should similar queries be handled?
3. AVOID: What patterns to avoid in future?

Format as JSON:
{{"issue": "...", "correction": "...", "avoid": "..."}}
"""
        
        try:
            result = self.genai_client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            response_text = result.text
            
            if "{" in response_text:
                json_str = response_text[response_text.find("{"):response_text.rfind("}")+1]
                learning_data = json.loads(json_str)
                
                self._store_learning(
                    learning_type=LearningType.CORRECTION,
                    content=learning_data.get("correction", ""),
                    context={
                        "issue": learning_data.get("issue", ""),
                        "avoid": learning_data.get("avoid", ""),
                        "source_query": query[:200],
                    },
                    confidence=0.5,
                    source_interaction=interaction_id
                )
        except Exception:
            pass
    
    def _store_learning(
        self,
        learning_type: LearningType,
        content: str,
        context: Dict,
        confidence: float,
        source_interaction: str
    ):
        """Store a learning in the database"""
        if not self.bq_client:
            return
        
        learning_id = hashlib.md5(
            f"{learning_type.value}:{content[:100]}".encode()
        ).hexdigest()[:16]
        
        confidence_level = self._get_confidence_level(confidence)
        
        row = {
            "learning_id": learning_id,
            "tenant_id": self.tenant_id,
            "learning_type": learning_type.value,
            "content": content[:2000],
            "context": context,
            "confidence": confidence,
            "confidence_level": confidence_level.value,
            "times_validated": 0,
            "times_contradicted": 0,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "source_interactions": [source_interaction],
        }
        
        table_ref = f"{self.PROJECT_ID}.{self.DATASET_ID}.titan_learnings"
        try:
            self.bq_client.insert_rows_json(table_ref, [row])
        except Exception:
            pass
    
    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Map confidence score to level"""
        if confidence < 0.3:
            return ConfidenceLevel.HYPOTHESIS
        elif confidence < 0.6:
            return ConfidenceLevel.EMERGING
        elif confidence < 0.85:
            return ConfidenceLevel.CONFIDENT
        else:
            return ConfidenceLevel.PROVEN
    
    def get_relevant_learnings(
        self,
        query: str,
        learning_types: Optional[List[LearningType]] = None,
        min_confidence: float = 0.5,
        limit: int = 5
    ) -> List[Learning]:
        """Get learnings relevant to a query"""
        if not self.bq_client:
            return []
        type_filter = ""
        if learning_types:
            types = ", ".join([f"'{lt.value}'" for lt in learning_types])
            type_filter = f"AND learning_type IN ({types})"
        
        # Extract keywords from query for matching
        keywords = self._extract_patterns(query, "")["keywords"]
        
        # Build keyword search condition
        keyword_conditions = []
        for kw in keywords[:5]:
            keyword_conditions.append(f"LOWER(content) LIKE '%{kw}%'")
        
        keyword_filter = ""
        if keyword_conditions:
            keyword_filter = f"AND ({' OR '.join(keyword_conditions)})"
        
        sql = f"""
        SELECT *
        FROM `{self.PROJECT_ID}.{self.DATASET_ID}.titan_learnings`
        WHERE tenant_id = '{self.tenant_id}'
            AND confidence >= {min_confidence}
            {type_filter}
            {keyword_filter}
        ORDER BY confidence DESC, times_validated DESC
        LIMIT {limit}
        """
        
        try:
            results = self.bq_client.query(sql).result()
            learnings = []
            
            for row in results:
                learning = Learning(
                    learning_id=row["learning_id"],
                    learning_type=LearningType(row["learning_type"]),
                    content=row["content"],
                    context=row["context"] or {},
                    confidence=row["confidence"],
                    confidence_level=ConfidenceLevel(row["confidence_level"]),
                    times_validated=row["times_validated"] or 0,
                    times_contradicted=row["times_contradicted"] or 0,
                    created_at=row["created_at"],
                    last_used=row["last_used"],
                )
                learnings.append(learning)
            
            return learnings
        except Exception:
            return []
    
    def build_learning_context(self, query: str) -> str:
        """Build context from relevant learnings for AI injection"""
        learnings = self.get_relevant_learnings(
            query,
            learning_types=[LearningType.STRATEGY, LearningType.CORRECTION],
            min_confidence=0.5,
            limit=3
        )
        
        if not learnings:
            return ""
        
        context_parts = [
            "## LEARNED STRATEGIES (from past successful interactions)",
            ""
        ]
        
        for i, learning in enumerate(learnings, 1):
            confidence_emoji = "🟢" if learning.confidence > 0.7 else "🟡"
            context_parts.append(
                f"{i}. {confidence_emoji} {learning.content}"
            )
            if learning.context.get("trigger"):
                context_parts.append(f"   Trigger: {learning.context['trigger']}")
        
        return "\n".join(context_parts)
    
    def validate_learning(self, learning_id: str, is_valid: bool):
        """Validate or contradict a learning based on new evidence"""
        if not self.bq_client:
            return
        field = "times_validated" if is_valid else "times_contradicted"
        
        sql = f"""
        UPDATE `{self.PROJECT_ID}.{self.DATASET_ID}.titan_learnings`
        SET {field} = {field} + 1,
            last_used = CURRENT_TIMESTAMP(),
            confidence = CASE 
                WHEN {is_valid} THEN LEAST(confidence + 0.05, 1.0)
                ELSE GREATEST(confidence - 0.1, 0.0)
            END,
            confidence_level = CASE
                WHEN confidence >= 0.85 THEN 'proven'
                WHEN confidence >= 0.6 THEN 'confident'
                WHEN confidence >= 0.3 THEN 'emerging'
                ELSE 'hypothesis'
            END
        WHERE learning_id = '{learning_id}'
        """
        
        try:
            self.bq_client.query(sql).result()
        except Exception:
            pass
    
    def get_evolution_metrics(self) -> EvolutionMetrics:
        """Get metrics about TITAN's evolution"""
        if not self.bq_client:
            return EvolutionMetrics(
                total_learnings=0,
                proven_learnings=0,
                active_hypotheses=0,
                avg_confidence=0,
                learning_velocity=0,
                accuracy_trend="unknown",
                top_learning_areas=[],
            )
        sql = f"""
        SELECT
            COUNT(*) as total_learnings,
            COUNTIF(confidence_level = 'proven') as proven_learnings,
            COUNTIF(confidence_level = 'hypothesis') as active_hypotheses,
            AVG(confidence) as avg_confidence,
            COUNT(DISTINCT DATE(created_at)) as days_active,
            ARRAY_AGG(DISTINCT learning_type ORDER BY learning_type LIMIT 5) as learning_types
        FROM `{self.PROJECT_ID}.{self.DATASET_ID}.titan_learnings`
        WHERE tenant_id = '{self.tenant_id}'
            AND created_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        """
        
        try:
            result = list(self.bq_client.query(sql).result())[0]
            
            total = result["total_learnings"] or 0
            days = result["days_active"] or 1
            velocity = total / days if days > 0 else 0
            
            return EvolutionMetrics(
                total_learnings=total,
                proven_learnings=result["proven_learnings"] or 0,
                active_hypotheses=result["active_hypotheses"] or 0,
                avg_confidence=result["avg_confidence"] or 0,
                learning_velocity=velocity,
                accuracy_trend="stable",  # Would need historical comparison
                top_learning_areas=result["learning_types"] or [],
            )
        except Exception:
            return EvolutionMetrics(
                total_learnings=0,
                proven_learnings=0,
                active_hypotheses=0,
                avg_confidence=0,
                learning_velocity=0,
                accuracy_trend="unknown",
                top_learning_areas=[],
            )
    
    def synthesize_insights(self) -> List[Dict[str, Any]]:
        """Synthesize learnings into actionable business insights"""
        if not self.genai_client:
            return []
        
        # Get recent high-confidence learnings
        learnings = self.get_relevant_learnings(
            "",  # Empty query to get all
            min_confidence=0.6,
            limit=10
        )
        
        if len(learnings) < 3:
            return []
        
        learnings_text = "\n".join([
            f"- {l.learning_type.value}: {l.content}" for l in learnings
        ])
        
        prompt = f"""Based on these learned patterns from restaurant business data, synthesize 3 actionable insights:

LEARNED PATTERNS:
{learnings_text}

For each insight, provide:
1. INSIGHT: Clear business insight
2. ACTION: Specific recommended action
3. EXPECTED_IMPACT: Quantified expected impact

Format as JSON array:
[{{"insight": "...", "action": "...", "expected_impact": "..."}}]
"""
        
        try:
            result = self.genai_client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            response_text = result.text
            
            if "[" in response_text:
                json_str = response_text[response_text.find("["):response_text.rfind("]")+1]
                return json.loads(json_str)
        except Exception:
            pass
        
        return []
