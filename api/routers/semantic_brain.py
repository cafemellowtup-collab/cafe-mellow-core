"""
Semantic Brain API Router
=========================
Exposes the Universal Semantic Brain through REST API.

Endpoints:
- POST /api/v1/brain/classify - Classify any data
- POST /api/v1/brain/ingest - Universal ingestion pipeline
- GET /api/v1/brain/categories - List all categories
- GET /api/v1/brain/events - Query events
- GET /api/v1/brain/summary - 360 analysis summary
- POST /api/v1/brain/verify - Human verification
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.universal_adapter.semantic_brain import (
    BusinessConcept, SubCategory, get_classifier, classify_data
)
from backend.universal_adapter.polymorphic_ledger import (
    init_all_universal_tables, query_events, get_category_summary,
    cross_category_analysis
)
from backend.universal_adapter.universal_ingestion import (
    universal_ingest, get_360_summary, verify_event,
    get_pending_reviews, DEFAULT_TENANT_ID
)


router = APIRouter(prefix="/api/v1/brain", tags=["semantic-brain"])


# =============================================================================
# Request/Response Models
# =============================================================================

class ClassifyRequest(BaseModel):
    data: Dict[str, Any]
    source_hint: Optional[str] = None


class ClassifyResponse(BaseModel):
    ok: bool
    category: str
    sub_category: str
    confidence: float
    reasoning: str
    requires_review: bool
    extracted_amount: Optional[float] = None
    extracted_date: Optional[str] = None
    key_entities: List[str] = []


class IngestRequest(BaseModel):
    data: Dict[str, Any]
    source_system: str
    tenant_id: Optional[str] = None
    auto_store: bool = True


class IngestResponse(BaseModel):
    ok: bool
    event_id: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    confidence: Optional[float] = None
    requires_review: bool = False
    review_reason: Optional[str] = None
    error: Optional[str] = None


class VerifyRequest(BaseModel):
    event_id: str
    tenant_id: Optional[str] = None
    verified_by: str = "human"
    correct_category: Optional[str] = None


class BatchIngestRequest(BaseModel):
    records: List[Dict[str, Any]]
    source_system: str
    tenant_id: Optional[str] = None


# =============================================================================
# Initialization
# =============================================================================

@router.on_event("startup")
async def startup_event():
    """Initialize Universal Brain tables on startup"""
    init_all_universal_tables()


@router.get("/health")
async def health_check():
    """Health check for Semantic Brain"""
    return {
        "ok": True,
        "service": "semantic-brain",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "capabilities": [
            "auto-classification",
            "multi-tenant",
            "360-analysis",
            "pattern-learning"
        ]
    }


# =============================================================================
# Classification Endpoints
# =============================================================================

@router.post("/classify", response_model=ClassifyResponse)
async def classify_data_endpoint(req: ClassifyRequest):
    """
    Classify ANY data using AI.
    
    The system understands:
    - Sales, Expenses, Inventory, Recipes, Menu
    - CRM, Staff, Vendors, Feedback
    - Reservations, Loyalty, Marketing
    - Finance, Operations, Infrastructure
    
    If it doesn't match anything, it creates a new category.
    """
    try:
        classification = await classify_data(req.data, req.source_hint)
        
        return ClassifyResponse(
            ok=True,
            category=classification.primary_concept.value,
            sub_category=classification.sub_category.value,
            confidence=classification.confidence_score,
            reasoning=classification.reasoning,
            requires_review=classification.requires_human_review,
            extracted_amount=classification.extracted_amount,
            extracted_date=classification.extracted_date,
            key_entities=classification.key_entities
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def list_categories():
    """List all available business categories"""
    return {
        "ok": True,
        "categories": [
            {
                "name": concept.value,
                "description": _get_concept_description(concept)
            }
            for concept in BusinessConcept
        ],
        "sub_categories": [sub.value for sub in SubCategory]
    }


def _get_concept_description(concept: BusinessConcept) -> str:
    """Get description for a business concept"""
    descriptions = {
        BusinessConcept.SALES: "Money coming IN from customers (orders, bills, invoices)",
        BusinessConcept.EXPENSE: "Money going OUT (purchases, salaries, utilities)",
        BusinessConcept.INVENTORY: "Physical goods, stock levels, ingredients",
        BusinessConcept.RECIPE: "How to make products, preparation steps",
        BusinessConcept.MENU: "Products for sale, prices, categories",
        BusinessConcept.CRM: "Customer information, contacts, preferences",
        BusinessConcept.STAFF: "Employee data, attendance, payroll",
        BusinessConcept.VENDOR: "Supplier information, contacts",
        BusinessConcept.FEEDBACK: "Reviews, ratings, complaints",
        BusinessConcept.RESERVATION: "Bookings, table management",
        BusinessConcept.LOYALTY: "Points, rewards, memberships",
        BusinessConcept.MARKETING: "Campaigns, promotions, offers",
        BusinessConcept.FINANCE: "Accounting, taxes, ledgers",
        BusinessConcept.OPERATIONS: "Shifts, schedules, tasks",
        BusinessConcept.INFRASTRUCTURE: "Equipment, sensors, utilities",
        BusinessConcept.UNKNOWN: "New category to be created"
    }
    return descriptions.get(concept, "")


# =============================================================================
# Universal Ingestion Endpoints
# =============================================================================

@router.post("/ingest", response_model=IngestResponse)
async def universal_ingest_endpoint(req: IngestRequest):
    """
    Universal ingestion - accepts ANY data.
    
    The system will:
    1. Classify the data automatically
    2. Store it with AI-generated tags
    3. Flag for review if confidence is low
    
    This handles 2 Crore+ scenarios without predefined rules.
    """
    try:
        result = await universal_ingest(
            data=req.data,
            source_system=req.source_system,
            tenant_id=req.tenant_id
        )
        
        return IngestResponse(
            ok=result.success,
            event_id=result.event_id,
            category=result.classification.primary_concept.value if result.classification else None,
            sub_category=result.classification.sub_category.value if result.classification else None,
            confidence=result.classification.confidence_score if result.classification else None,
            requires_review=result.requires_review,
            review_reason=result.review_reason,
            error=result.error
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/batch")
async def batch_ingest_endpoint(req: BatchIngestRequest):
    """
    Batch ingestion for bulk data imports.
    Handles Excel files, API dumps, etc.
    """
    from backend.universal_adapter.universal_ingestion import get_pipeline, TenantContext
    
    tenant = TenantContext(
        tenant_id=req.tenant_id or DEFAULT_TENANT_ID,
        tenant_name="",
        settings={}
    ) if req.tenant_id else None
    
    pipeline = get_pipeline(tenant)
    
    import asyncio
    results = await pipeline.batch_ingest(req.records, req.source_system)
    
    return {
        "ok": True,
        **results
    }


# =============================================================================
# Query Endpoints
# =============================================================================

@router.get("/events")
async def query_events_endpoint(
    tenant_id: str = Query(default=DEFAULT_TENANT_ID),
    category: Optional[str] = None,
    sub_category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    verified_only: bool = False,
    limit: int = Query(default=50, ge=1, le=500)
):
    """
    Query events from the Universal Ledger.
    Filter by category, date, verification status.
    """
    events = query_events(
        tenant_id=tenant_id,
        category=category,
        sub_category=sub_category,
        start_date=start_date,
        end_date=end_date,
        verified_only=verified_only,
        limit=limit
    )
    
    return {
        "ok": True,
        "count": len(events),
        "events": events
    }


@router.get("/summary")
async def get_summary_endpoint(
    tenant_id: str = Query(default=DEFAULT_TENANT_ID),
    days: int = Query(default=30, ge=1, le=365)
):
    """
    Get 360-degree business summary.
    Cross-category analysis for executive dashboard.
    """
    summary = get_360_summary(tenant_id, days)
    return {
        "ok": True,
        **summary
    }


@router.get("/analysis/cross-category")
async def cross_category_endpoint(
    tenant_id: str = Query(default=DEFAULT_TENANT_ID),
    category_a: str = Query(..., description="First category"),
    category_b: str = Query(..., description="Second category")
):
    """
    Analyze correlation between two categories.
    Example: Sales vs Marketing, Expenses vs Revenue
    """
    analysis = cross_category_analysis(tenant_id, category_a, category_b)
    return {
        "ok": True,
        **analysis
    }


# =============================================================================
# Verification Endpoints
# =============================================================================

@router.get("/pending-reviews")
async def get_pending_reviews_endpoint(
    tenant_id: str = Query(default=DEFAULT_TENANT_ID),
    limit: int = Query(default=50, ge=1, le=200)
):
    """Get events pending human review"""
    reviews = get_pending_reviews(tenant_id, limit)
    return {
        "ok": True,
        "count": len(reviews),
        "pending": reviews
    }


@router.post("/verify")
async def verify_event_endpoint(req: VerifyRequest):
    """
    Verify an event (human approval).
    Optionally correct the category if AI was wrong.
    """
    success = verify_event(
        event_id=req.event_id,
        tenant_id=req.tenant_id or DEFAULT_TENANT_ID,
        verified_by=req.verified_by,
        correct_category=req.correct_category
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Verification failed")
    
    return {
        "ok": True,
        "message": "Event verified successfully"
    }


# =============================================================================
# Demo Endpoints (For Testing)
# =============================================================================

@router.post("/demo/test-classification")
async def demo_classification():
    """
    Demo endpoint showing the AI can classify diverse data.
    """
    test_cases = [
        {
            "name": "Sales Order",
            "data": {"orderID": "ORD001", "customer": "John", "total": 500, "items": ["Coffee", "Cake"]},
            "expected": "sales"
        },
        {
            "name": "Expense",
            "data": {"vendor": "Amul", "item": "Milk", "quantity": "50L", "amount": 2500},
            "expected": "expense"
        },
        {
            "name": "Staff Record",
            "data": {"employee": "Ravi", "role": "Chef", "salary": 35000, "joining_date": "2024-01-15"},
            "expected": "staff"
        },
        {
            "name": "Customer Feedback",
            "data": {"guest": "Sarah", "rating": 5, "comment": "Amazing coffee!", "visit_date": "2025-01-27"},
            "expected": "feedback"
        },
        {
            "name": "Recipe",
            "data": {"item": "Cappuccino", "ingredients": ["Espresso", "Milk", "Foam"], "prep_time": "5min"},
            "expected": "recipe"
        },
        {
            "name": "Unknown/New Category",
            "data": {"sensor_id": "TEMP001", "temperature": 24.5, "humidity": 65, "location": "Kitchen"},
            "expected": "infrastructure"
        }
    ]
    
    results = []
    for test in test_cases:
        classification = await classify_data(test["data"])
        results.append({
            "name": test["name"],
            "input": test["data"],
            "expected": test["expected"],
            "actual": classification.primary_concept.value,
            "confidence": classification.confidence_score,
            "reasoning": classification.reasoning,
            "match": classification.primary_concept.value == test["expected"]
        })
    
    return {
        "ok": True,
        "message": "This demonstrates AI auto-classification without predefined rules",
        "total_tests": len(results),
        "correct": sum(1 for r in results if r["match"]),
        "results": results
    }
