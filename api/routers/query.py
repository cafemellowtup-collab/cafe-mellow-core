"""
Query API - Natural Language Business Queries
==============================================
Phase 4A: Ask questions in plain English, get data-driven answers.

Endpoints:
- POST /ask - Ask a business question
- POST /preference - Update user preferences
- GET /profile - Get data profile for tenant
"""

import sys
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

# Windows encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class QueryRequest(BaseModel):
    """Request to ask a business question."""
    question: str
    execute_sql: bool = True


class QueryResponse(BaseModel):
    """Response with answer and data."""
    question_understood: bool
    sql_generated: bool
    sql: Optional[str] = None
    executed: bool
    answer_text: str
    visualization_hint: Optional[str] = None
    confidence: float
    data: Optional[list] = None
    row_count: int = 0
    timestamp: str
    error: Optional[str] = None


class PreferenceRequest(BaseModel):
    """Request to update preferences."""
    instruction: str


class PreferenceResponse(BaseModel):
    """Response after updating preferences."""
    ok: bool
    instruction: str
    extracted: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    req: QueryRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID")
):
    """
    Ask a business question in natural language.
    
    The Titan Cortex will:
    1. Analyze your data profile
    2. Apply your preferences (exclusions, rules)
    3. Generate appropriate SQL
    4. Execute and return formatted answer
    
    Examples:
    - "What were my total sales this week?"
    - "Top 5 selling items last month"
    - "If I sell 10kg of coffee at Rs 500/kg, what's my revenue?"
    """
    try:
        from backend.universal_adapter.query_engine import get_engine
        
        engine = get_engine()
        result = engine.ask(req.question, x_tenant_id, req.execute_sql)
        
        return QueryResponse(
            question_understood=result.get("question_understood", False),
            sql_generated=result.get("sql_generated", False),
            sql=result.get("sql"),
            executed=result.get("executed", False),
            answer_text=result.get("answer_text", ""),
            visualization_hint=result.get("visualization_hint"),
            confidence=result.get("confidence", 0.0),
            data=result.get("data"),
            row_count=result.get("row_count", 0),
            timestamp=result.get("timestamp", ""),
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preference", response_model=PreferenceResponse)
async def update_preference(
    req: PreferenceRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID")
):
    """
    Update user preferences using natural language.
    
    Examples:
    - "Don't include personal expenses in reports"
    - "My fiscal year starts in April"
    - "Show all amounts in USD"
    - "Only show me sales data"
    """
    try:
        from backend.universal_adapter.titan_cortex import get_cortex
        
        cortex = get_cortex(x_tenant_id)
        result = cortex.update_preference(req.instruction)
        
        return PreferenceResponse(
            ok=result.get("ok", False),
            instruction=req.instruction,
            extracted=result.get("extracted"),
            message=result.get("message")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile")
async def get_data_profile(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID")
):
    """
    Get the data profile for a tenant.
    
    Returns information about:
    - What data categories are available
    - Data maturity level (empty, minimal, partial, full)
    - Date range of data
    - Total events
    """
    try:
        from backend.universal_adapter.titan_cortex import get_cortex
        
        cortex = get_cortex(x_tenant_id)
        profile = cortex.get_data_profile(x_tenant_id)
        preferences = cortex.get_preferences()
        
        return {
            "ok": True,
            "tenant_id": x_tenant_id,
            "profile": profile,
            "preferences": preferences
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for query service."""
    return {
        "ok": True,
        "service": "Titan Cortex Query Engine",
        "version": "4.0.0",
        "status": "operational"
    }
