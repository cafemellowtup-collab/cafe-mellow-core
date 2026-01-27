"""
Universal Ingestion Pipeline - The Complete Brain
=================================================
Connects ALL components into ONE unified pipeline:

1. AIRLOCK: Accept ANY data (never crash)
2. SEMANTIC BRAIN: AI classifies what it is
3. POLYMORPHIC LEDGER: Store with AI tags
4. CONFIDENCE CHECK: Auto-approve or ask human
5. PATTERN CACHE: Learn for cost optimization

This is the "Universal Brain" that handles 2 Crore+ scenarios.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from .semantic_brain import (
    SemanticClassifier, SemanticClassification, BusinessConcept,
    classify_data_sync, get_classifier
)
from .polymorphic_ledger import (
    store_universal_event, query_events, get_category_summary,
    init_all_universal_tables
)


# =============================================================================
# Multi-Tenant Context
# =============================================================================

DEFAULT_TENANT_ID = "cafe_mellow_001"  # Default for single-tenant mode


@dataclass
class TenantContext:
    """
    Tenant context for multi-tenant SaaS mode.
    Every operation requires tenant isolation.
    """
    tenant_id: str
    tenant_name: str
    settings: Dict[str, Any]
    
    @classmethod
    def default(cls) -> "TenantContext":
        return cls(
            tenant_id=DEFAULT_TENANT_ID,
            tenant_name="Cafe Mellow",
            settings={}
        )


# =============================================================================
# Ingestion Result
# =============================================================================

@dataclass
class IngestionResult:
    """
    Result of universal ingestion.
    """
    success: bool
    event_id: Optional[str]
    classification: Optional[SemanticClassification]
    requires_review: bool
    review_reason: Optional[str]
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "event_id": self.event_id,
            "classification": {
                "category": self.classification.primary_concept.value if self.classification else None,
                "sub_category": self.classification.sub_category.value if self.classification else None,
                "confidence": self.classification.confidence_score if self.classification else None,
                "reasoning": self.classification.reasoning if self.classification else None,
            } if self.classification else None,
            "requires_review": self.requires_review,
            "review_reason": self.review_reason,
            "error": self.error
        }


# =============================================================================
# Universal Ingestion Pipeline
# =============================================================================

class UniversalIngestionPipeline:
    """
    The complete universal ingestion pipeline.
    Handles ANY data from ANY source automatically.
    """
    
    def __init__(self, tenant: Optional[TenantContext] = None):
        self.tenant = tenant or TenantContext.default()
        self.classifier = get_classifier()
        self._pattern_cache: Dict[str, SemanticClassification] = {}
    
    async def ingest(
        self,
        data: Dict[str, Any],
        source_system: str,
        raw_log_id: Optional[str] = None,
        auto_store: bool = True
    ) -> IngestionResult:
        """
        Ingest ANY data through the universal pipeline.
        
        Args:
            data: The raw data (any format, any schema)
            source_system: Where it came from (petpooja, excel, api, etc.)
            raw_log_id: Optional reference to raw_logs entry
            auto_store: Whether to auto-store high-confidence data
        
        Returns:
            IngestionResult with classification and storage info
        """
        try:
            # Step 1: Check pattern cache for known schemas
            fingerprint = self._compute_fingerprint(data)
            
            if fingerprint in self._pattern_cache:
                classification = self._pattern_cache[fingerprint]
                print(f"🔄 Cache hit for pattern: {fingerprint}")
            else:
                # Step 2: Semantic classification (AI Brain)
                classification = await self.classifier.classify(data, source_system)
                
                # Cache successful classifications
                if classification.confidence_score >= 0.7:
                    self._pattern_cache[fingerprint] = classification
                    print(f"📚 Cached new pattern: {fingerprint} -> {classification.primary_concept.value}")
            
            # Step 3: Determine if auto-store or human review
            requires_review = classification.requires_human_review
            
            event_id = None
            if auto_store and not requires_review:
                # Step 4: Store in polymorphic ledger
                event_id = store_universal_event(
                    data=data,
                    tenant_id=self.tenant.tenant_id,
                    source_system=source_system,
                    classification=classification,
                    raw_log_id=raw_log_id
                )
            
            return IngestionResult(
                success=True,
                event_id=event_id,
                classification=classification,
                requires_review=requires_review,
                review_reason=classification.review_reason
            )
            
        except Exception as e:
            print(f"❌ Ingestion error: {e}")
            return IngestionResult(
                success=False,
                event_id=None,
                classification=None,
                requires_review=True,
                review_reason=f"Ingestion error: {str(e)}",
                error=str(e)
            )
    
    def ingest_sync(
        self,
        data: Dict[str, Any],
        source_system: str,
        raw_log_id: Optional[str] = None,
        auto_store: bool = True
    ) -> IngestionResult:
        """Synchronous version of ingest"""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.ingest(data, source_system, raw_log_id, auto_store)
        )
    
    def _compute_fingerprint(self, data: Dict[str, Any]) -> str:
        """Compute schema fingerprint"""
        structure = {}
        for key, value in data.items():
            if isinstance(value, dict):
                structure[key] = "object"
            elif isinstance(value, list):
                structure[key] = "array"
            elif isinstance(value, (int, float)):
                structure[key] = "number"
            elif isinstance(value, bool):
                structure[key] = "boolean"
            else:
                structure[key] = "string"
        
        structure_str = json.dumps(structure, sort_keys=True)
        return hashlib.md5(structure_str.encode()).hexdigest()[:16]
    
    async def batch_ingest(
        self,
        records: List[Dict[str, Any]],
        source_system: str
    ) -> Dict[str, Any]:
        """
        Ingest multiple records in batch.
        Optimized for bulk data imports.
        """
        results = {
            "total": len(records),
            "success": 0,
            "failed": 0,
            "pending_review": 0,
            "events": [],
            "errors": []
        }
        
        for i, record in enumerate(records):
            try:
                result = await self.ingest(record, source_system)
                
                if result.success:
                    results["success"] += 1
                    if result.requires_review:
                        results["pending_review"] += 1
                    results["events"].append({
                        "index": i,
                        "event_id": result.event_id,
                        "category": result.classification.primary_concept.value if result.classification else None
                    })
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "index": i,
                        "error": result.error
                    })
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "index": i,
                    "error": str(e)
                })
        
        return results


# =============================================================================
# Global Pipeline Instance
# =============================================================================

_pipeline: Optional[UniversalIngestionPipeline] = None


def get_pipeline(tenant: Optional[TenantContext] = None) -> UniversalIngestionPipeline:
    """Get or create global pipeline instance"""
    global _pipeline
    if _pipeline is None or (tenant and tenant.tenant_id != _pipeline.tenant.tenant_id):
        _pipeline = UniversalIngestionPipeline(tenant)
    return _pipeline


async def universal_ingest(
    data: Dict[str, Any],
    source_system: str,
    tenant_id: Optional[str] = None,
    raw_log_id: Optional[str] = None
) -> IngestionResult:
    """
    Main entry point for universal ingestion.
    
    Args:
        data: Any data in any format
        source_system: Source identifier
        tenant_id: Optional tenant ID for multi-tenant mode
        raw_log_id: Optional raw_logs reference
    
    Returns:
        IngestionResult with classification and storage info
    """
    tenant = TenantContext(
        tenant_id=tenant_id or DEFAULT_TENANT_ID,
        tenant_name="",
        settings={}
    ) if tenant_id else None
    
    pipeline = get_pipeline(tenant)
    return await pipeline.ingest(data, source_system, raw_log_id)


def universal_ingest_sync(
    data: Dict[str, Any],
    source_system: str,
    tenant_id: Optional[str] = None,
    raw_log_id: Optional[str] = None
) -> IngestionResult:
    """Synchronous version of universal_ingest"""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        universal_ingest(data, source_system, tenant_id, raw_log_id)
    )


# =============================================================================
# Integration with Existing Airlock
# =============================================================================

def process_raw_log_with_brain(
    log_id: str,
    raw_payload: Dict[str, Any],
    source_type: str,
    tenant_id: Optional[str] = None
) -> IngestionResult:
    """
    Process a raw_logs entry through the Universal Brain.
    This integrates with the existing Airlock system.
    """
    return universal_ingest_sync(
        data=raw_payload,
        source_system=source_type,
        tenant_id=tenant_id,
        raw_log_id=log_id
    )


# =============================================================================
# Review & Verification
# =============================================================================

def get_pending_reviews(tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get events pending human review"""
    return query_events(
        tenant_id=tenant_id,
        verified_only=False,
        limit=limit
    )


def verify_event(
    event_id: str,
    tenant_id: str,
    verified_by: str,
    correct_category: Optional[str] = None
) -> bool:
    """
    Verify an event (human approval).
    Optionally correct the category if AI was wrong.
    """
    from .polymorphic_ledger import _get_bq_client
    
    client, cfg = _get_bq_client()
    if not client:
        return False
    
    dataset = getattr(cfg, "BQ_DATASET", "cafe_operations")
    table_id = f"{client.project}.{dataset}.universal_ledger"
    
    try:
        if correct_category:
            sql = f"""
            UPDATE `{table_id}`
            SET 
                verified = TRUE,
                verified_by = @verified_by,
                verified_at = CURRENT_TIMESTAMP(),
                original_category = category,
                category = @correct_category
            WHERE event_id = @event_id AND tenant_id = @tenant_id
            """
        else:
            sql = f"""
            UPDATE `{table_id}`
            SET 
                verified = TRUE,
                verified_by = @verified_by,
                verified_at = CURRENT_TIMESTAMP()
            WHERE event_id = @event_id AND tenant_id = @tenant_id
            """
        
        from google.cloud import bigquery
        
        params = [
            bigquery.ScalarQueryParameter("event_id", "STRING", event_id),
            bigquery.ScalarQueryParameter("tenant_id", "STRING", tenant_id),
            bigquery.ScalarQueryParameter("verified_by", "STRING", verified_by),
        ]
        
        if correct_category:
            params.append(bigquery.ScalarQueryParameter("correct_category", "STRING", correct_category))
        
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        client.query(sql, job_config=job_config).result()
        
        print(f"✅ Verified event: {event_id}")
        return True
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


# =============================================================================
# Analytics Queries (360 Analysis)
# =============================================================================

def get_360_summary(tenant_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Get 360-degree business summary.
    Cross-category analysis for executive dashboard.
    """
    from datetime import timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    summary = get_category_summary(
        tenant_id=tenant_id,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )
    
    # Calculate key metrics
    categories = summary.get("categories", [])
    
    sales_total = sum(c.get("total_amount", 0) for c in categories if c.get("category") == "sales")
    expense_total = sum(c.get("total_amount", 0) for c in categories if c.get("category") == "expense")
    
    return {
        "period_days": days,
        "total_events": summary.get("totals", {}).get("events", 0),
        "total_monetary_value": summary.get("totals", {}).get("amount", 0),
        "sales_total": sales_total,
        "expense_total": expense_total,
        "profit_estimate": sales_total - expense_total,
        "categories": categories,
        "data_quality": {
            "total_categories": len(categories),
            "avg_confidence": sum(c.get("avg_confidence", 0) for c in categories) / max(len(categories), 1)
        }
    }


def ask_question(tenant_id: str, question: str) -> Dict[str, Any]:
    """
    Natural language query interface.
    The AI can answer questions about any category.
    
    Example questions:
    - "What were my top expenses last week?"
    - "Show me the correlation between marketing and sales"
    - "Which vendors do I owe money to?"
    """
    # This would integrate with the Oracle/Chat system
    # For now, return a placeholder
    return {
        "question": question,
        "answer": "This feature integrates with the Oracle AI system for natural language queries.",
        "suggested_queries": [
            f"SELECT category, SUM(amount) FROM universal_ledger WHERE tenant_id = '{tenant_id}' GROUP BY category",
            f"SELECT * FROM universal_ledger WHERE tenant_id = '{tenant_id}' ORDER BY timestamp DESC LIMIT 10"
        ]
    }
