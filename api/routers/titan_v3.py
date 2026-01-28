"""
TITAN v3 API Router
===================
REST API endpoints for the TITAN v3 Self-Evolving Intelligence System.
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.core.titan_v3 import (
    TitanV3Engine,
    get_titan_engine,
    PersonalityEngine,
    PersonalityMode,
    GraphRAG,
    ActiveSenses,
    EvolutionCore,
    PhoenixProtocols,
)

router = APIRouter(prefix="/titan/v3", tags=["TITAN v3"])


# Request/Response Models
class QueryRequest(BaseModel):
    query: str = Field(..., description="User query to process")
    tenant_id: str = Field(default="default", description="Tenant identifier")
    conversation_history: Optional[List[Dict]] = Field(default=None, description="Previous messages")
    business_context: Optional[Dict] = Field(default=None, description="Pre-calculated business metrics")
    use_pro_model: bool = Field(default=False, description="Use Gemini Pro instead of Flash")


class QueryResponse(BaseModel):
    content: str
    personality_mode: str
    confidence: float
    processing_time_ms: int
    model_used: str
    metadata: Dict[str, Any]


class PersonalityAnalysis(BaseModel):
    sentiment: str
    query_type: str
    recommended_mode: str
    tone_instructions: str


class GraphNode(BaseModel):
    entity_id: str
    entity_type: str
    name: str
    attributes: Optional[Dict] = None


class GraphRelationship(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str
    strength: float = 1.0
    attributes: Optional[Dict] = None


class ImpactAnalysisRequest(BaseModel):
    entity_id: str
    depth: int = Field(default=2, ge=1, le=5)


class LearningFeedback(BaseModel):
    interaction_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class HealthResponse(BaseModel):
    version: str
    status: str
    components: Dict[str, str]
    gemini_configured: bool


# Endpoints

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check health of TITAN v3 system"""
    engine = get_titan_engine()
    return engine.get_health_status()


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query through the full TITAN v3 pipeline.
    
    Pipeline includes:
    - Personality analysis (Predator/Partner mode selection)
    - Graph context building (relationship analysis)
    - External senses (weather, market data)
    - Learned strategy application
    - Response generation
    """
    try:
        engine = get_titan_engine(
            tenant_id=request.tenant_id,
            gemini_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        response = await engine.process_query(
            query=request.query,
            conversation_history=request.conversation_history,
            business_context=request.business_context,
            use_pro_model=request.use_pro_model
        )
        
        return QueryResponse(
            content=response.content,
            personality_mode=response.personality_mode.value,
            confidence=response.confidence,
            processing_time_ms=response.processing_time_ms,
            model_used=response.model_used,
            metadata=response.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/personality", response_model=PersonalityAnalysis)
async def analyze_personality(query: str = Query(..., description="Query to analyze")):
    """Analyze query for personality mode selection"""
    personality = PersonalityEngine()
    
    sentiment = personality.detect_sentiment(query)
    query_type = personality.classify_query_type(query)
    mode = personality.select_mode(sentiment, query_type)
    instructions = personality.get_tone_instructions(mode)
    
    return PersonalityAnalysis(
        sentiment=sentiment,
        query_type=query_type,
        recommended_mode=mode.value,
        tone_instructions=instructions
    )


@router.post("/graph/node")
async def add_graph_node(
    node: GraphNode,
    tenant_id: str = Query(default="default")
):
    """Add a node to the knowledge graph"""
    graph = GraphRAG(tenant_id=tenant_id)
    
    success = graph.add_node(
        entity_id=node.entity_id,
        entity_type=node.entity_type,
        name=node.name,
        attributes=node.attributes
    )
    
    return {"success": success, "node_id": node.entity_id}


@router.post("/graph/relationship")
async def add_graph_relationship(
    relationship: GraphRelationship,
    tenant_id: str = Query(default="default")
):
    """Add a relationship to the knowledge graph"""
    graph = GraphRAG(tenant_id=tenant_id)
    
    success = graph.add_relationship(
        source_id=relationship.source_id,
        target_id=relationship.target_id,
        relationship_type=relationship.relationship_type,
        strength=relationship.strength,
        attributes=relationship.attributes
    )
    
    return {"success": success}


@router.post("/graph/impact")
async def analyze_impact(
    request: ImpactAnalysisRequest,
    tenant_id: str = Query(default="default")
):
    """Analyze impact of an entity through the graph"""
    graph = GraphRAG(tenant_id=tenant_id)
    
    result = graph.analyze_impact(
        entity_id=request.entity_id,
        depth=request.depth
    )
    
    return result


@router.get("/graph/context")
async def build_graph_context(
    query: str = Query(...),
    tenant_id: str = Query(default="default")
):
    """Build graph context for a query"""
    graph = GraphRAG(tenant_id=tenant_id)
    context = graph.build_query_context(query)
    
    return {"context": context}


@router.get("/senses/weather")
async def get_weather(
    location: str = Query(default="Bangalore, India")
):
    """Get current weather and business impact"""
    senses = ActiveSenses(location=location)
    weather = await senses.get_weather()
    
    return {
        "condition": weather.condition,
        "temperature_c": weather.temperature_c,
        "humidity": weather.humidity,
        "precipitation_chance": weather.precipitation_chance,
        "wind_speed_kmh": weather.wind_speed_kmh,
        "business_impact": weather.business_impact,
        "forecast_24h": weather.forecast_24h[:6]  # Next 6 hours
    }


@router.get("/senses/market")
async def get_market_prices(
    commodities: Optional[str] = Query(default=None, description="Comma-separated list")
):
    """Get current commodity prices"""
    senses = ActiveSenses()
    
    items = commodities.split(",") if commodities else None
    market = await senses.get_market_prices(items)
    
    return {
        "commodities": market.commodities,
        "price_changes": market.price_changes,
        "cost_opportunities": market.cost_opportunities,
        "alerts": market.alerts
    }


@router.get("/senses/context")
async def get_external_context(
    location: str = Query(default="Bangalore, India")
):
    """Get complete external context for AI injection"""
    senses = ActiveSenses(location=location)
    context = await senses.build_external_context()
    
    return {"context": context}


@router.get("/senses/recommendations")
async def get_sense_recommendations(
    location: str = Query(default="Bangalore, India")
):
    """Get actionable recommendations from external senses"""
    senses = ActiveSenses(location=location)
    
    # Refresh data first
    await senses.get_weather()
    await senses.get_market_prices()
    
    recommendations = senses.get_recommendation()
    
    return {"recommendations": recommendations}


@router.post("/learning/feedback")
async def submit_feedback(
    feedback: LearningFeedback,
    tenant_id: str = Query(default="default")
):
    """Submit feedback for an interaction to enable learning"""
    evolution = EvolutionCore(tenant_id=tenant_id)
    
    # Note: This would update the interaction record
    # For now, return success
    return {
        "success": True,
        "interaction_id": feedback.interaction_id,
        "rating": feedback.rating
    }


@router.get("/learning/strategies")
async def get_learned_strategies(
    query: str = Query(...),
    tenant_id: str = Query(default="default"),
    min_confidence: float = Query(default=0.5, ge=0, le=1)
):
    """Get learned strategies relevant to a query"""
    evolution = EvolutionCore(tenant_id=tenant_id)
    
    learnings = evolution.get_relevant_learnings(
        query=query,
        min_confidence=min_confidence
    )
    
    return {
        "learnings": [
            {
                "id": l.learning_id,
                "type": l.learning_type.value,
                "content": l.content,
                "confidence": l.confidence,
                "confidence_level": l.confidence_level.value,
                "times_validated": l.times_validated,
            }
            for l in learnings
        ]
    }


@router.get("/learning/context")
async def get_learning_context(
    query: str = Query(...),
    tenant_id: str = Query(default="default")
):
    """Get formatted learning context for AI injection"""
    evolution = EvolutionCore(tenant_id=tenant_id)
    context = evolution.build_learning_context(query)
    
    return {"context": context}


@router.get("/evolution/metrics")
async def get_evolution_metrics(
    tenant_id: str = Query(default="default")
):
    """Get evolution and learning metrics"""
    engine = get_titan_engine(tenant_id=tenant_id)
    return engine.get_evolution_metrics()


@router.get("/evolution/insights")
async def get_synthesized_insights(
    tenant_id: str = Query(default="default")
):
    """Get AI-synthesized insights from learnings"""
    evolution = EvolutionCore(tenant_id=tenant_id)
    insights = evolution.synthesize_insights()
    
    return {"insights": insights}


@router.get("/phoenix/stats")
async def get_healing_stats():
    """Get self-healing statistics"""
    phoenix = PhoenixProtocols()
    return phoenix.get_healing_stats()


@router.get("/capabilities")
async def get_capabilities():
    """List all TITAN v3 capabilities"""
    return {
        "version": "3.0.0",
        "capabilities": {
            "personality_engine": {
                "description": "Dual-Heart personality system",
                "modes": ["predator", "partner", "hybrid"],
                "features": ["sentiment_detection", "query_classification", "dynamic_tone"]
            },
            "graph_rag": {
                "description": "SQL-based knowledge graph for deep reasoning",
                "features": ["relationship_tracking", "impact_analysis", "recursive_traversal"]
            },
            "phoenix_protocols": {
                "description": "Self-healing code system",
                "features": ["error_detection", "ai_diagnosis", "hot_patching", "auto_recovery"]
            },
            "active_senses": {
                "description": "Real-time external data integration",
                "senses": ["weather", "market_prices", "local_events"]
            },
            "evolution_core": {
                "description": "Continuous learning and improvement",
                "features": ["pattern_extraction", "strategy_learning", "insight_synthesis"]
            }
        }
    }
