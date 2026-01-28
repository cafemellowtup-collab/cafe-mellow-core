"""
Intelligence Engine API Router
==============================
Exposes the unified TITAN Intelligence Engine through REST API.

Endpoints:
- GET /api/v1/intelligence/health - Health check
- POST /api/v1/intelligence/process - Process query with full context
- GET /api/v1/intelligence/metrics - Get real-time business metrics
- GET /api/v1/intelligence/anomalies - Detect anomalies
- POST /api/v1/intelligence/learn - Record learning from interaction
- GET /api/v1/intelligence/patterns - Get learned patterns
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.core.intelligence_engine import (
    TitanIntelligenceEngine,
    get_intelligence_engine,
    process_query,
    QueryIntent,
    ResponseType,
)
from backend.core.titan_prompts import (
    build_optimized_prompt,
    post_process_response,
    classify_query,
    TITAN_SYSTEM_PROMPT,
)


router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])


# ============ Request/Response Models ============

class ProcessQueryRequest(BaseModel):
    query: str
    tenant_id: Optional[str] = "cafe_mellow_001"
    include_system_prompt: bool = True
    

class ProcessQueryResponse(BaseModel):
    ok: bool
    prompt: str
    system_prompt: Optional[str]
    intent: str
    response_type: str
    metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    timestamp: str


class LearnRequest(BaseModel):
    query: str
    response: str
    feedback: Optional[str] = None
    tenant_id: Optional[str] = "cafe_mellow_001"


class MetricsResponse(BaseModel):
    ok: bool
    tenant_id: str
    timestamp: str
    revenue: Dict[str, Any]
    expenses: Dict[str, Any]
    profit: Dict[str, Any]
    operations: Dict[str, Any]
    top_items: List[Dict[str, Any]]


# ============ Endpoints ============

@router.get("/health")
async def health_check(tenant_id: str = Query(default="cafe_mellow_001")):
    """Health check for Intelligence Engine"""
    try:
        engine = get_intelligence_engine(tenant_id)
        health = await engine.health_check()
        return health
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@router.post("/process", response_model=ProcessQueryResponse)
async def process_user_query(req: ProcessQueryRequest):
    """
    Process a user query with full intelligence context.
    
    This is the main entry point for AI-enhanced queries.
    Returns optimized prompt with business context injected.
    """
    try:
        result = await process_query(req.query, req.tenant_id)
        
        return ProcessQueryResponse(
            ok=True,
            prompt=result["prompt"],
            system_prompt=TITAN_SYSTEM_PROMPT if req.include_system_prompt else None,
            intent=result["intent"],
            response_type=result["response_type"],
            metrics=result["metrics"],
            alerts=result["alerts"],
            timestamp=result["timestamp"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=MetricsResponse)
async def get_business_metrics(
    tenant_id: str = Query(default="cafe_mellow_001"),
    force_refresh: bool = Query(default=False),
):
    """
    Get real-time business metrics for context injection.
    
    Cached for 5 minutes unless force_refresh=true.
    """
    try:
        engine = get_intelligence_engine(tenant_id)
        metrics = await engine.get_business_metrics(force_refresh=force_refresh)
        
        return MetricsResponse(
            ok=True,
            tenant_id=tenant_id,
            timestamp=metrics.timestamp.isoformat(),
            revenue={
                "today": metrics.revenue_today,
                "last_7d": metrics.revenue_7d,
                "last_30d": metrics.revenue_30d,
                "change_7d_pct": metrics.revenue_change_7d,
                "orders_today": metrics.orders_today,
                "orders_7d": metrics.orders_7d,
                "avg_order_value": metrics.avg_order_value,
            },
            expenses={
                "today": metrics.expenses_today,
                "last_7d": metrics.expenses_7d,
                "last_30d": metrics.expenses_30d,
                "change_7d_pct": metrics.expense_change_7d,
                "top_categories": metrics.top_expense_categories,
            },
            profit={
                "last_7d": metrics.profit_7d,
                "margin_7d_pct": metrics.profit_margin_7d,
            },
            operations={
                "pending_tasks": metrics.pending_tasks,
                "low_stock_items": metrics.low_stock_items,
                "inventory_value": metrics.total_inventory_value,
            },
            top_items=metrics.top_items,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies")
async def detect_anomalies(tenant_id: str = Query(default="cafe_mellow_001")):
    """
    Detect anomalies in business data.
    
    Returns list of detected anomalies with severity and recommendations.
    """
    try:
        engine = get_intelligence_engine(tenant_id)
        anomalies = await engine.detect_anomalies()
        
        return {
            "ok": True,
            "tenant_id": tenant_id,
            "anomalies": anomalies,
            "count": len(anomalies),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learn")
async def learn_from_interaction(req: LearnRequest):
    """
    Record learning from user interaction.
    
    Used to improve AI responses over time based on:
    - Successful queries
    - User feedback
    - Interaction patterns
    """
    try:
        engine = get_intelligence_engine(req.tenant_id)
        await engine.learn_from_interaction(
            query=req.query,
            response=req.response,
            feedback=req.feedback,
        )
        
        return {
            "ok": True,
            "message": "Learning recorded successfully",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns")
async def get_learned_patterns(
    tenant_id: str = Query(default="cafe_mellow_001"),
    limit: int = Query(default=20, le=100),
):
    """
    Get learned patterns and rules for the tenant.
    """
    try:
        engine = get_intelligence_engine(tenant_id)
        patterns = await engine.get_learned_patterns(limit=limit)
        
        return {
            "ok": True,
            "tenant_id": tenant_id,
            "patterns": patterns,
            "count": len(patterns),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_active_alerts(
    tenant_id: str = Query(default="cafe_mellow_001"),
    limit: int = Query(default=10, le=50),
):
    """
    Get active alerts for the tenant.
    """
    try:
        engine = get_intelligence_engine(tenant_id)
        alerts = await engine.get_active_alerts(limit=limit)
        
        return {
            "ok": True,
            "tenant_id": tenant_id,
            "alerts": alerts,
            "count": len(alerts),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classify")
async def classify_intent(query: str = Query(...)):
    """
    Classify a query's intent.
    
    Returns the detected intent type and suggested response format.
    """
    try:
        engine = get_intelligence_engine()
        intent = engine.classify_intent(query)
        response_type = engine._suggest_response_type(intent)
        
        # Also get prompt-level classification
        prompt_class = classify_query(query)
        
        return {
            "ok": True,
            "query": query,
            "intent": intent.value,
            "response_type": response_type.value,
            "prompt_classification": prompt_class,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context-preview")
async def preview_context(
    query: str = Query(...),
    tenant_id: str = Query(default="cafe_mellow_001"),
):
    """
    Preview the full context that would be injected for a query.
    
    Useful for debugging and understanding AI behavior.
    """
    try:
        engine = get_intelligence_engine(tenant_id)
        context = await engine.build_context(query)
        prompt = engine.build_optimized_prompt(query, context)
        
        return {
            "ok": True,
            "query": query,
            "tenant_id": tenant_id,
            "intent": context.query_intent.value,
            "response_type": context.suggested_response_type.value,
            "context_preview": prompt,
            "metrics_summary": {
                "revenue_7d": context.metrics.revenue_7d,
                "expenses_7d": context.metrics.expenses_7d,
                "profit_7d": context.metrics.profit_7d,
                "profit_margin": context.metrics.profit_margin_7d,
            },
            "alerts_count": len(context.active_alerts),
            "patterns_count": len(context.recent_patterns),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
