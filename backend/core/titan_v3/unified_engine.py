"""
TITAN v3 Unified Intelligence Engine
=====================================
The master orchestration layer that unifies all v3 AI components:
- Personality Engine (Dual-Heart)
- SQL-GraphRAG (Deep Reasoning)
- Phoenix Protocols (Self-Healing)
- Active Senses (External Data)
- Evolution Core (Learning)

This is the single entry point for all AI interactions.
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
import json
import time

from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError

try:
    from google import genai
    _GENAI_AVAILABLE = True
except ImportError:
    genai = None
    _GENAI_AVAILABLE = False

from .personality_engine import PersonalityEngine, PersonalityMode
from .graph_rag import GraphRAG
from .phoenix_protocols import PhoenixProtocols, HealingStatus
from .active_senses import ActiveSenses
from .evolution_core import EvolutionCore, LearningType

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


@dataclass
class TitanResponse:
    """Unified response from TITAN v3"""
    content: str
    personality_mode: PersonalityMode
    confidence: float
    sources: List[str] = field(default_factory=list)
    graph_context: Optional[str] = None
    external_context: Optional[str] = None
    learning_context: Optional[str] = None
    processing_time_ms: int = 0
    model_used: str = "gemini-2.0-flash"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TitanContext:
    """Complete context for AI generation"""
    business_metrics: Dict[str, Any]
    graph_insights: str
    external_senses: str
    learned_strategies: str
    personality_instructions: str
    user_sentiment: str
    query_type: str


class TitanV3Engine:
    """
    TITAN v3 Unified Intelligence Engine
    
    The "brain" that orchestrates all AI components for optimal responses.
    """
    
    def __init__(
        self,
        tenant_id: str = "default",
        gemini_api_key: Optional[str] = None,
        location: str = "Bangalore, India"
    ):
        self.tenant_id = tenant_id
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        # Centralized config
        self.PROJECT_ID, self.DATASET_ID = get_bq_config()
        
        # Initialize all v3 components
        self.personality = PersonalityEngine()
        self.graph_rag = GraphRAG(tenant_id=tenant_id)
        self.phoenix = PhoenixProtocols(gemini_api_key=self.api_key)
        self.senses = ActiveSenses(location=location)
        self.evolution = EvolutionCore(tenant_id=tenant_id)
        
        # Initialize Gemini client (new google.genai API)
        self.genai_client = None
        self.flash_model_name = "gemini-2.0-flash"
        self.pro_model_name = "gemini-2.5-pro"
        
        if self.api_key and _GENAI_AVAILABLE:
            try:
                self.genai_client = genai.Client(api_key=self.api_key)
            except Exception:
                self.genai_client = None
        
        self.bq_client, self._bq_init_error = _get_bq_client(self.PROJECT_ID)
    
    async def process_query(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None,
        business_context: Optional[Dict] = None,
        use_pro_model: bool = False
    ) -> TitanResponse:
        """
        Process a user query through the complete v3 pipeline.
        
        Pipeline:
        1. Analyze user sentiment and query type (Personality Engine)
        2. Build graph context for deep reasoning (GraphRAG)
        3. Inject external data (Active Senses)
        4. Apply learned strategies (Evolution Core)
        5. Generate response with appropriate personality
        6. Record interaction for learning
        """
        start_time = time.time()
        
        # Step 1: Personality Analysis
        sentiment = self.personality.detect_sentiment(query)
        query_type = self.personality.classify_query_type(query)
        mode = self.personality.select_mode(sentiment, query_type)
        personality_instructions = self.personality.get_tone_instructions(mode)
        
        # Step 2: Graph Context (Deep Reasoning)
        graph_context = ""
        try:
            # Extract entities and find relationships
            entities = self._extract_entities(query)
            if entities:
                impact_analysis = await asyncio.to_thread(
                    self.graph_rag.analyze_impact,
                    entities[0],
                    depth=2
                )
                if impact_analysis:
                    graph_context = self._format_graph_context(impact_analysis)
        except Exception:
            pass
        
        # Step 3: External Senses
        external_context = ""
        try:
            external_context = await self.senses.build_external_context()
        except Exception:
            pass
        
        # Step 4: Learned Strategies
        learning_context = self.evolution.build_learning_context(query)
        
        # Step 5: Build Complete Context
        context = TitanContext(
            business_metrics=business_context or {},
            graph_insights=graph_context,
            external_senses=external_context,
            learned_strategies=learning_context,
            personality_instructions=personality_instructions,
            user_sentiment=sentiment,
            query_type=query_type,
        )
        
        # Step 6: Generate Response
        response_content = await self._generate_response(
            query=query,
            context=context,
            conversation_history=conversation_history,
            use_pro=use_pro_model
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Step 7: Record for Learning
        try:
            self.evolution.record_interaction(
                user_query=query,
                ai_response=response_content,
                personality_mode=mode.value,
                query_type=query_type,
                response_time_ms=processing_time,
            )
        except Exception:
            pass
        
        return TitanResponse(
            content=response_content,
            personality_mode=mode,
            confidence=0.85,
            sources=["BigQuery", "GraphRAG", "ActiveSenses"],
            graph_context=graph_context if graph_context else None,
            external_context=external_context if external_context else None,
            learning_context=learning_context if learning_context else None,
            processing_time_ms=processing_time,
            model_used="gemini-2.5-pro" if use_pro_model else "gemini-2.0-flash",
            metadata={
                "sentiment": sentiment,
                "query_type": query_type,
                "mode": mode.value,
            }
        )
    
    async def _generate_response(
        self,
        query: str,
        context: TitanContext,
        conversation_history: Optional[List[Dict]],
        use_pro: bool = False
    ) -> str:
        """Generate AI response with full context injection"""
        
        if not self.flash_model:
            return "AI service unavailable. Please configure GEMINI_API_KEY."
        
        # Build the mega-prompt
        system_prompt = self._build_system_prompt(context)
        
        # Build conversation context
        history_text = ""
        if conversation_history:
            recent = conversation_history[-5:]  # Last 5 messages
            history_text = "\n".join([
                f"{'User' if m.get('role') == 'user' else 'TITAN'}: {m.get('content', '')[:500]}"
                for m in recent
            ])
        
        full_prompt = f"""{system_prompt}

## CONVERSATION HISTORY
{history_text if history_text else "No previous conversation."}

## CURRENT QUERY
{query}

## YOUR RESPONSE
Respond according to your personality mode and the context provided. Be data-driven and actionable.
"""
        
        try:
            model = self.pro_model if use_pro else self.flash_model
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"I encountered an issue processing your request. Error: {str(e)}"
    
    def _build_system_prompt(self, context: TitanContext) -> str:
        """Build the complete system prompt with all context"""
        
        prompt_parts = [
            "# TITAN v3 - Self-Evolving Business Intelligence",
            "",
            "You are TITAN, an advanced AI CFO assistant with deep reasoning capabilities.",
            "",
            "## PERSONALITY MODE",
            context.personality_instructions,
            "",
        ]
        
        # Add business metrics if available
        if context.business_metrics:
            prompt_parts.extend([
                "## BUSINESS CONTEXT (Pre-calculated - DO NOT recalculate)",
                "```json",
                json.dumps(context.business_metrics, indent=2, default=str),
                "```",
                "",
            ])
        
        # Add graph insights
        if context.graph_insights:
            prompt_parts.extend([
                "## RELATIONSHIP INSIGHTS (GraphRAG)",
                context.graph_insights,
                "",
            ])
        
        # Add external context
        if context.external_senses:
            prompt_parts.extend([
                context.external_senses,
                "",
            ])
        
        # Add learned strategies
        if context.learned_strategies:
            prompt_parts.extend([
                context.learned_strategies,
                "",
            ])
        
        # Add response format
        prompt_parts.extend([
            "## RESPONSE FORMAT",
            "Structure your response as:",
            "1. **FINDING**: Key insight from the data",
            "2. **CAUSE**: Why this is happening (use graph relationships)",
            "3. **ACTION**: Specific recommendation",
            "4. **IMPACT**: Expected outcome if action is taken",
            "",
            "Keep responses concise but actionable. Use ₹ for currency.",
        ])
        
        return "\n".join(prompt_parts)
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract business entities from query for graph traversal"""
        entities = []
        
        # Common business entities to look for
        entity_patterns = [
            "revenue", "sales", "profit", "expense", "cost",
            "staff", "employee", "inventory", "stock", "supplier",
            "customer", "order", "product", "menu", "price",
        ]
        
        query_lower = query.lower()
        for pattern in entity_patterns:
            if pattern in query_lower:
                entities.append(pattern)
        
        return entities[:3]  # Limit to top 3
    
    def _format_graph_context(self, impact_analysis: Dict) -> str:
        """Format graph analysis for prompt injection"""
        parts = ["### Relationship Analysis"]
        
        if "impact_chain" in impact_analysis:
            parts.append("**Impact Chain:**")
            for item in impact_analysis["impact_chain"][:5]:
                parts.append(f"- {item.get('source', '?')} → {item.get('target', '?')} ({item.get('relationship', 'affects')})")
        
        if "affected_areas" in impact_analysis:
            parts.append(f"\n**Affected Areas:** {', '.join(impact_analysis['affected_areas'][:5])}")
        
        return "\n".join(parts)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all v3 components"""
        return {
            "version": "3.0.0",
            "status": "healthy",
            "components": {
                "personality_engine": "active",
                "graph_rag": "active",
                "phoenix_protocols": "active",
                "active_senses": "active",
                "evolution_core": "active",
            },
            "gemini_configured": bool(self.api_key),
            "tenant_id": self.tenant_id,
        }
    
    def get_evolution_metrics(self) -> Dict[str, Any]:
        """Get learning and evolution metrics"""
        metrics = self.evolution.get_evolution_metrics()
        healing_stats = self.phoenix.get_healing_stats()
        
        return {
            "learning": {
                "total_learnings": metrics.total_learnings,
                "proven_learnings": metrics.proven_learnings,
                "avg_confidence": metrics.avg_confidence,
                "learning_velocity": metrics.learning_velocity,
            },
            "self_healing": healing_stats,
        }
    
    def analyze_file_structure(self, sample_rows: Dict[str, Any]) -> Optional[int]:
        """
        AI Judge for Structure Detective - Phase 2D
        
        When the Detective finds two header candidates with similar scores,
        this method uses AI to determine which is the detailed transaction ledger.
        
        Args:
            sample_rows: Dict with candidate1 and candidate2, each containing:
                - row_idx: The row index
                - headers: List of header values
                
        Returns:
            1 if candidate1 is the transaction ledger
            2 if candidate2 is the transaction ledger
            None if unable to determine
        """
        if not self.flash_model:
            return None
        
        try:
            candidate1 = sample_rows.get("candidate1", {})
            candidate2 = sample_rows.get("candidate2", {})
            
            prompt = f"""You are analyzing a spreadsheet with multiple tables.

I see two potential header rows:

Row {candidate1.get('row_idx', '?')}: {candidate1.get('headers', [])}
Row {candidate2.get('row_idx', '?')}: {candidate2.get('headers', [])}

Which one is the DETAILED TRANSACTION LEDGER (the one with individual transactions,
not a summary table)?

Rules:
- Transaction ledgers have columns like: Date, Item, Qty, Amount, Invoice, Order
- Summary tables have columns like: Category, Total, Count, Average
- Prefer the table with MORE columns (more detailed)
- Prefer the table that appears LATER in the file (summaries often come first)

Respond with ONLY the number 1 or 2 (nothing else):
- 1 = Row {candidate1.get('row_idx', '?')} is the transaction ledger
- 2 = Row {candidate2.get('row_idx', '?')} is the transaction ledger"""
            
            response = self.genai_client.models.generate_content(
                model=self.flash_model_name,
                contents=prompt
            )
            result = response.text.strip()
            
            if result == "1":
                return 1
            elif result == "2":
                return 2
            else:
                return None
                
        except Exception as e:
            print(f"[TITAN] AI Judge error: {e}")
            return None


# Singleton instance for easy access
_engine_instance: Optional[TitanV3Engine] = None


def get_titan_engine(
    tenant_id: str = "default",
    gemini_api_key: Optional[str] = None
) -> TitanV3Engine:
    """Get or create TITAN v3 engine instance"""
    global _engine_instance

    if gemini_api_key is None:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if (
        _engine_instance is None
        or _engine_instance.tenant_id != tenant_id
        or (gemini_api_key and _engine_instance.api_key != gemini_api_key)
    ):
        _engine_instance = TitanV3Engine(
            tenant_id=tenant_id,
            gemini_api_key=gemini_api_key
        )
    
    return _engine_instance
