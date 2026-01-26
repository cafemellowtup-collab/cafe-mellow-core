"""
Forecast Router - Predictive Oracle Widget
Predicts tomorrow's inventory needs and sales based on:
- Historical patterns
- Weather data
- Holiday calendar
- Day of week trends
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from pillars.config_vault import EffectiveSettings
from utils.bq_guardrails import query_to_df

router = APIRouter(prefix="/api/v1/forecast", tags=["forecast"])


class ForecastRequest(BaseModel):
    org_id: str
    location_id: str
    forecast_date: str  # YYYY-MM-DD
    include_weather: bool = True


def _get_bq_client():
    try:
        from google.cloud import bigquery
        import os
        
        cfg = EffectiveSettings()
        key_file = getattr(cfg, "KEY_FILE", "service-key.json")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
        
        if not os.path.exists(key_path):
            return None
        return bigquery.Client.from_service_account_json(key_path)
    except Exception:
        return None


def _is_holiday(date_str: str) -> tuple[bool, Optional[str]]:
    """Check if date is a holiday (India focus)"""
    # Simplified holiday detection - in production, use holiday API
    holidays = {
        "2026-01-26": "Republic Day",
        "2026-03-08": "Holi",
        "2026-08-15": "Independence Day",
        "2026-10-02": "Gandhi Jayanti",
        "2026-10-24": "Diwali",
        "2026-12-25": "Christmas",
    }
    return date_str in holidays, holidays.get(date_str)


def _get_weather_forecast(date_str: str, location: str = "Bangalore") -> Dict[str, Any]:
    """Get weather forecast (placeholder - integrate OpenWeatherMap API)"""
    # In production, call actual weather API
    return {
        "temperature_c": 28,
        "condition": "Partly Cloudy",
        "precipitation_chance": 20,
        "impact": "normal"  # "normal", "high_traffic", "low_traffic"
    }


@router.post("/daily")
def daily_forecast(req: ForecastRequest) -> Dict[str, Any]:
    """
    Predictive Oracle: Forecast tomorrow's operations
    
    Predictions:
    - Expected revenue range
    - Top items to prep
    - Inventory requirements
    - Staff recommendations
    """
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected")
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        
        forecast_date = datetime.strptime(req.forecast_date, "%Y-%m-%d").date()
        day_of_week = forecast_date.strftime("%A")
        
        # Check if holiday
        is_holiday, holiday_name = _is_holiday(req.forecast_date)
        
        # Get weather
        weather = _get_weather_forecast(req.forecast_date) if req.include_weather else None
        
        # Historical analysis: Same day of week, last 4 weeks
        same_dow_dates = []
        for i in range(1, 5):
            past_date = forecast_date - timedelta(weeks=i)
            same_dow_dates.append(past_date.isoformat())
        
        dates_filter = "', '".join(same_dow_dates)
        
        # Revenue prediction based on historical same-day-of-week
        revenue_query = f"""
        WITH historical AS (
            SELECT
                SAFE_CAST(bill_date AS DATE) as dt,
                SUM(SAFE_CAST(order_total AS FLOAT64)) as daily_revenue,
                COUNT(DISTINCT order_id) as order_count
            FROM `{project_id}.{dataset_id}.sales_enhanced`
            WHERE SAFE_CAST(bill_date AS DATE) IN ('{dates_filter}')
              AND NOT REGEXP_CONTAINS(LOWER(COALESCE(order_status, '')), r"cancel")
            GROUP BY dt
        )
        SELECT
            AVG(daily_revenue) as avg_revenue,
            STDDEV(daily_revenue) as stddev_revenue,
            AVG(order_count) as avg_orders,
            MIN(daily_revenue) as min_revenue,
            MAX(daily_revenue) as max_revenue
        FROM historical
        """
        
        try:
            df_revenue, _ = query_to_df(client, cfg, revenue_query, purpose="api.forecast.revenue")
        except Exception as e:
            # If query fails, return estimate based on simple assumptions
            return {
                "ok": True,
                "forecast_date": req.forecast_date,
                "day_of_week": day_of_week,
                "is_holiday": is_holiday,
                "holiday_name": holiday_name,
                "weather": weather,
                "predicted_revenue": {"min": 0, "avg": 0, "max": 0, "confidence": "low", "avg_orders": 0},
                "top_items": [],
                "inventory_requirements": [],
                "staff_recommendations": {"kitchen_staff": 2, "service_staff": 1, "peak_hours": ["12:00-14:00", "19:00-21:00"], "rationale": "No historical data available"},
                "generated_at": datetime.now().isoformat(),
                "error": f"Limited data: {str(e)[:100]}"
            }
        
        if df_revenue.empty:
            predicted_revenue = {"min": 0, "avg": 0, "max": 0, "confidence": "low", "avg_orders": 0}
        else:
            avg_rev = float(df_revenue['avg_revenue'].iloc[0] or 0)
            std_rev = float(df_revenue['stddev_revenue'].iloc[0] or 0)
            min_rev = float(df_revenue['min_revenue'].iloc[0] or 0)
            max_rev = float(df_revenue['max_revenue'].iloc[0] or 0)
            avg_orders = float(df_revenue['avg_orders'].iloc[0] or 0)
            
            # Adjust for weather impact
            weather_multiplier = 1.0
            if weather:
                if weather.get("impact") == "high_traffic":
                    weather_multiplier = 1.15
                elif weather.get("impact") == "low_traffic":
                    weather_multiplier = 0.85
            
            # Adjust for holiday
            holiday_multiplier = 1.3 if is_holiday else 1.0
            
            predicted_revenue = {
                "min": round(min_rev * weather_multiplier * holiday_multiplier, 2),
                "avg": round(avg_rev * weather_multiplier * holiday_multiplier, 2),
                "max": round(max_rev * weather_multiplier * holiday_multiplier, 2),
                "confidence": "high" if std_rev / avg_rev < 0.2 else "medium",
                "avg_orders": round(avg_orders * weather_multiplier * holiday_multiplier, 0)
            }
        
        # Top items prediction - Use simpler query for performance
        items_query = f"""
        SELECT
            item_name,
            SUM(SAFE_CAST(quantity AS FLOAT64)) / 4 as avg_qty,
            SUM(SAFE_CAST(total_revenue AS FLOAT64)) / 4 as avg_revenue
        FROM `{project_id}.{dataset_id}.sales_items_parsed`
        WHERE SAFE_CAST(bill_date AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 28 DAY)
        GROUP BY item_name
        ORDER BY avg_revenue DESC
        LIMIT 10
        """
        
        df_items, _ = query_to_df(client, cfg, items_query, purpose="api.forecast.items")
        
        top_items = []
        if not df_items.empty:
            for _, row in df_items.iterrows():
                top_items.append({
                    "item_name": row['item_name'],
                    "predicted_qty": round(float(row['avg_qty']), 1),
                    "predicted_revenue": round(float(row['avg_revenue']), 2)
                })
        
        # Inventory requirements (if recipes available)
        inventory_requirements = []
        if top_items:
            top_item_names = "', '".join([item['item_name'] for item in top_items[:5]])
            
            inventory_query = f"""
            SELECT
                r.ingredient_name,
                SUM(r.qty_required * {top_items[0]['predicted_qty']}) as total_qty_needed
            FROM `{project_id}.{dataset_id}.recipes_sales_master` r
            WHERE LOWER(r.item_name) IN (LOWER('{top_item_names}'))
            GROUP BY r.ingredient_name
            ORDER BY total_qty_needed DESC
            LIMIT 15
            """
            
            try:
                df_inv, _ = query_to_df(client, cfg, inventory_query, purpose="api.forecast.inventory")
                
                if not df_inv.empty:
                    for _, row in df_inv.iterrows():
                        inventory_requirements.append({
                            "ingredient": row['ingredient_name'],
                            "qty_needed": round(float(row['total_qty_needed']), 2)
                        })
            except:
                pass  # Table might not exist
        
        # Staff recommendations
        staff_recommendations = {
            "kitchen_staff": 3 if predicted_revenue.get("avg", 0) > 20000 else 2,
            "service_staff": 2 if predicted_revenue.get("avg", 0) > 20000 else 1,
            "peak_hours": ["12:00-14:00", "19:00-21:00"],
            "rationale": f"{day_of_week} typically sees moderate traffic"
        }
        
        if is_holiday:
            staff_recommendations["kitchen_staff"] += 1
            staff_recommendations["service_staff"] += 1
            staff_recommendations["rationale"] = f"Holiday ({holiday_name}) - expect higher traffic"
        
        return {
            "ok": True,
            "forecast_date": req.forecast_date,
            "day_of_week": day_of_week,
            "is_holiday": is_holiday,
            "holiday_name": holiday_name,
            "weather": weather,
            "predicted_revenue": predicted_revenue,
            "top_items": top_items,
            "inventory_requirements": inventory_requirements,
            "staff_recommendations": staff_recommendations,
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/week")
def weekly_forecast(
    org_id: str = Query(...),
    location_id: str = Query(...),
    start_date: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    7-day rolling forecast
    """
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected")
    
    try:
        base_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else datetime.now().date()
        
        weekly_predictions = []
        
        for i in range(7):
            forecast_date = base_date + timedelta(days=i)
            
            req = ForecastRequest(
                org_id=org_id,
                location_id=location_id,
                forecast_date=forecast_date.isoformat(),
                include_weather=True
            )
            
            daily_pred = daily_forecast(req)
            
            weekly_predictions.append({
                "date": forecast_date.isoformat(),
                "day": forecast_date.strftime("%A"),
                "revenue_range": f"₹{daily_pred['predicted_revenue']['min']}-{daily_pred['predicted_revenue']['max']}",
                "confidence": daily_pred['predicted_revenue']['confidence'],
                "is_holiday": daily_pred.get('is_holiday', False)
            })
        
        return {
            "ok": True,
            "week_start": base_date.isoformat(),
            "predictions": weekly_predictions,
            "total_week_estimate": sum([p.get('predicted_revenue', {}).get('avg', 0) for p in [daily_forecast(ForecastRequest(org_id=org_id, location_id=location_id, forecast_date=(base_date + timedelta(days=i)).isoformat())) for i in range(7)]])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
