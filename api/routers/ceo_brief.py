"""
Digital CEO Morning Briefing - Proactive Intelligence
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/ceo", tags=["CEO Intelligence"])


class MorningBriefing(BaseModel):
    date: str
    location: str
    data_quality: dict
    reconciliation: dict
    alerts: list
    summary: str


def _get_data_quality_brief(client, cfg, org_id: str, location_id: str, days: int = 30):
    """Get data quality score and tier for briefing"""
    try:
        from backend.core.analytics_engine import calculate_data_quality
        
        result = calculate_data_quality(client, cfg, org_id, location_id, days)
        return {
            "score": result.get("score", 0),
            "tier": result.get("tier", "UNKNOWN"),
            "dimensions": result.get("dimensions", {}),
            "message": _format_quality_message(result),
        }
    except Exception as e:
        return {
            "score": 0,
            "tier": "ERROR",
            "dimensions": {},
            "message": f"Unable to assess data quality: {str(e)}",
        }


def _format_quality_message(quality_data):
    """Format data quality into CEO-appropriate message"""
    score = quality_data.get("score", 0)
    tier = quality_data.get("tier", "UNKNOWN")
    
    if tier == "GREEN":
        return f"✅ Data Quality: {score:.0f}/100 (GREEN tier). Your data fortress is solid."
    elif tier == "YELLOW":
        return f"⚠️ Data Quality: {score:.0f}/100 (YELLOW tier). Minor gaps detected. Review recommended."
    elif tier == "RED":
        return f"🚨 Data Quality: {score:.0f}/100 (RED tier). Critical gaps. Upload recipes and expense records immediately."
    else:
        return f"❓ Data Quality: Unable to assess. Check your data pipelines."


def _get_reconciliation_brief(client, cfg, org_id: str, location_id: str):
    """Check yesterday's cash reconciliation (Shadow Ledger)"""
    try:
        from utils.bq_guardrails import query_to_df
        
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        
        # Query the universal_ledger for cash reconciliation
        q = f"""
        SELECT 
            entry_date,
            entry_type,
            amount,
            metadata
        FROM `{cfg.PROJECT_ID}.{cfg.DATASET_ID}.universal_ledger`
        WHERE org_id = '{org_id}'
          AND location_id = '{location_id}'
          AND entry_date = DATE('{yesterday}')
          AND entry_type IN ('cash_closing', 'cash_opening', 'cash_variance')
        ORDER BY entry_date DESC, created_at DESC
        """
        
        df, _ = query_to_df(client, cfg, q, purpose="ceo.brief.reconciliation")
        
        if df.empty:
            return {
                "status": "unknown",
                "variance": 0,
                "message": "⚪ No reconciliation data for yesterday. Run daily close.",
            }
        
        # Calculate variance
        closing = df[df["entry_type"] == "cash_closing"]["amount"].sum() if not df[df["entry_type"] == "cash_closing"].empty else 0
        opening = df[df["entry_type"] == "cash_opening"]["amount"].sum() if not df[df["entry_type"] == "cash_opening"].empty else 0
        variance = abs(closing - opening)
        
        if variance > 100:  # More than ₹100 variance
            return {
                "status": "alert",
                "variance": variance,
                "message": f"🚨 ALERT: ₹{variance:,.0f} missing from yesterday's cash reconciliation. Your Personal Budget is restricted until resolved.",
            }
        else:
            return {
                "status": "ok",
                "variance": variance,
                "message": f"✅ Yesterday's cash reconciled. Variance: ₹{variance:,.0f} (acceptable).",
            }
            
    except Exception as e:
        return {
            "status": "error",
            "variance": 0,
            "message": f"Unable to check reconciliation: {str(e)}",
        }


@router.get("/morning-brief", response_model=MorningBriefing)
async def get_morning_brief(
    org_id: str = Query(..., description="Organization ID"),
    location_id: str = Query(..., description="Location ID"),
):
    """
    Get the Digital CEO's Morning Briefing
    
    Includes:
    - Data quality score and tier
    - Yesterday's cash reconciliation (Shadow Ledger check)
    - Critical alerts from task queue
    """
    try:
        from pillars.config_vault import EffectiveSettings
        from google.cloud import bigquery
        import os
        
        cfg = EffectiveSettings()
        key_file = getattr(cfg, "KEY_FILE", "service-key.json")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
        
        if not os.path.exists(key_path):
            raise HTTPException(status_code=500, detail="BigQuery credentials not found")
        
        client = bigquery.Client.from_service_account_json(key_path)
        
        # Get data quality
        quality = _get_data_quality_brief(client, cfg, org_id, location_id)
        
        # Get reconciliation status
        reconciliation = _get_reconciliation_brief(client, cfg, org_id, location_id)
        
        # Get critical alerts
        try:
            from utils.bq_guardrails import query_to_df
            
            q_alerts = f"""
            SELECT task_type, item_involved, description, priority
            FROM `{cfg.PROJECT_ID}.{cfg.DATASET_ID}.ai_task_queue`
            WHERE status = 'Pending'
              AND priority IN ('HIGH', 'CRITICAL')
            ORDER BY created_at DESC
            LIMIT 5
            """
            alerts_df, _ = query_to_df(client, cfg, q_alerts, purpose="ceo.brief.critical_alerts")
            alerts = alerts_df.to_dict("records") if not alerts_df.empty else []
        except:
            alerts = []
        
        # Build summary
        summary_parts = [
            f"Good morning. This is your Digital CEO briefing for {location_id}.",
            quality["message"],
            reconciliation["message"],
        ]
        
        if alerts:
            summary_parts.append(f"⚠️ {len(alerts)} critical alert(s) require attention.")
        
        summary = "\n\n".join(summary_parts)
        
        return MorningBriefing(
            date=date.today().isoformat(),
            location=location_id,
            data_quality=quality,
            reconciliation=reconciliation,
            alerts=alerts,
            summary=summary,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate morning brief: {str(e)}")
