"""
Analytics Router - Business Intelligence APIs
Integrated with Chameleon Brain for adaptive strategies
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from backend.core.chameleon import DataQualityEngine, StrategySelector

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/data_quality")
async def get_data_quality(
    org_id: str = Query(...),
    location_id: str = Query(...),
    days: int = Query(30, ge=7, le=90)
):
    """
    Get data quality score for a tenant
    This drives the Chameleon adaptive strategy
    """
    try:
        from google.cloud import bigquery
        from pillars.config_vault import EffectiveSettings
        
        cfg = EffectiveSettings()
        client = bigquery.Client.from_service_account_json(cfg.KEY_FILE)
        
        engine = DataQualityEngine(client, cfg)
        score = engine.calculate_score(org_id, location_id, days)
        
        return {
            "ok": True,
            "score": score.score,
            "tier": score.tier,
            "dimensions": score.dimensions,
            "recommendations": score.recommendations,
            "calculated_at": score.calculated_at.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profit")
async def calculate_profit(
    org_id: str = Query(...),
    location_id: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
    force_strategy: Optional[str] = Query(None)
):
    """
    Calculate profit using adaptive strategy based on data quality
    
    Chameleon Brain:
    - RED tier (< 50): Estimation via Sales - Purchases
    - YELLOW tier (50-90): Hybrid COGS + Purchase fallback
    - GREEN tier (> 90): Full audit-grade COGS
    """
    try:
        from google.cloud import bigquery
        from pillars.config_vault import EffectiveSettings
        from backend.core.chameleon import AdaptiveStrategy
        
        cfg = EffectiveSettings()
        client = bigquery.Client.from_service_account_json(cfg.KEY_FILE)
        
        if force_strategy:
            strategy = AdaptiveStrategy(force_strategy)
        else:
            engine = DataQualityEngine(client, cfg)
            quality_score = engine.calculate_score(org_id, location_id)
            strategy = StrategySelector.select_profit_strategy(quality_score)
        
        query = StrategySelector.get_strategy_sql(
            strategy=strategy,
            project_id=cfg.PROJECT_ID,
            dataset_id=cfg.DATASET_ID,
            org_id=org_id,
            location_id=location_id,
            start_date=start_date,
            end_date=end_date
        )
        
        result = client.query(query).result()
        
        for row in result:
            return {
                "ok": True,
                "strategy": strategy.value,
                "revenue": float(row.get("revenue") or row.get("total_revenue") or 0),
                "cost": float(row.get("cost") or row.get("total_cost") or row.get("total_cogs") or 0),
                "profit": float(row.get("estimated_profit") or row.get("profit") or 0),
                "start_date": start_date,
                "end_date": end_date
            }
        
        return {
            "ok": True,
            "strategy": strategy.value,
            "revenue": 0,
            "cost": 0,
            "profit": 0,
            "error": "No data found for date range"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
