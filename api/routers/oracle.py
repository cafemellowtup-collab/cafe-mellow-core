"""
Oracle Router - Advanced Intelligence Features
- Vision API for image analysis (invoices, food quality, inventory)
- Digital Twin Simulator for What-If scenarios
- Fraud Detection (KOT vs Bill reconciliation)
- Deductive Reasoning Engine
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
import base64

from pillars.config_vault import EffectiveSettings
from utils.bq_guardrails import query_to_df

router = APIRouter(prefix="/api/v1/oracle", tags=["oracle"])


class VisionAnalysisRequest(BaseModel):
    image_base64: str
    analysis_type: str  # "invoice", "food_quality", "inventory_shelf", "general"
    org_id: str
    location_id: str


class SimulationRequest(BaseModel):
    scenario_type: str  # "price_change", "vendor_switch", "recipe_modification"
    parameters: Dict[str, Any]
    org_id: str
    location_id: str
    start_date: str
    end_date: str


class DeductiveReasoningRequest(BaseModel):
    problem: str  # e.g., "Maida inventory is -526g"
    context: Optional[Dict[str, Any]] = None
    org_id: str
    location_id: str


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


@router.post("/vision/analyze")
def analyze_image(req: VisionAnalysisRequest) -> Dict[str, Any]:
    """
    Multi-Modal Vision Analysis
    
    Use Cases:
    - Invoice OCR: Extract line items from handwritten bills
    - Food Quality: Analyze plated food for presentation
    - Inventory Shelf: Count items from shelf photos
    """
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected")
    
    try:
        import google.generativeai as genai
        from PIL import Image
        import io
        
        # Initialize Gemini Vision API
        api_key = getattr(cfg, "GEMINI_API_KEY", "")
        if not api_key:
            raise HTTPException(status_code=400, detail="GEMINI_API_KEY missing")
        
        genai.configure(api_key=api_key)
        
        # Decode base64 image
        image_data = base64.b64decode(req.image_base64)
        image = Image.open(io.BytesIO(image_data))
        
        # Select model and prompt based on analysis type
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompts = {
            "invoice": """Analyze this invoice/bill image and extract:
1. Vendor name
2. Date
3. All line items with quantities and prices
4. Total amount
5. Payment method if visible

Format as structured JSON.""",
            
            "food_quality": """Analyze this food plate image and provide:
1. Visual appeal score (1-10)
2. Portion size assessment
3. Presentation quality
4. Any quality issues visible
5. Recommendations for improvement

Be specific and actionable.""",
            
            "inventory_shelf": """Analyze this inventory shelf image and count:
1. Number of visible items by type
2. Stock level assessment (low/medium/high)
3. Organization quality
4. Any expired or damaged items visible
5. Restocking recommendations

Provide counts and specific observations.""",
            
            "general": "Analyze this image in the context of restaurant operations. Provide detailed observations and actionable insights."
        }
        
        prompt = prompts.get(req.analysis_type, prompts["general"])
        
        response = model.generate_content([prompt, image])
        analysis_text = response.text
        
        # Log analysis to BigQuery for future learning
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        
        log_sql = f"""
        INSERT INTO `{project_id}.{dataset_id}.vision_analysis_log`
        (id, org_id, location_id, analysis_type, analysis_result, created_at)
        VALUES (
            '{req.org_id}_{req.location_id}_{int(datetime.now().timestamp())}',
            '{req.org_id}',
            '{req.location_id}',
            '{req.analysis_type}',
            '''{analysis_text.replace("'", "''")}''',
            CURRENT_TIMESTAMP()
        )
        """
        
        try:
            client.query(log_sql).result()
        except:
            pass  # Table might not exist yet
        
        return {
            "ok": True,
            "analysis_type": req.analysis_type,
            "analysis": analysis_text,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision analysis failed: {str(e)}")


@router.post("/simulate")
def simulate_scenario(req: SimulationRequest) -> Dict[str, Any]:
    """
    Digital Twin Simulator - What-If Scenario Planning
    
    Scenarios:
    - price_change: "What if I increase cake price by 10%?"
    - vendor_switch: "What if I switch to cheaper oil supplier?"
    - recipe_modification: "What if I reduce sugar by 20g per cake?"
    """
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected")
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        
        if req.scenario_type == "price_change":
            item_name = req.parameters.get("item_name", "")
            price_change_pct = req.parameters.get("price_change_pct", 0)
            
            # Get historical data
            base_query = f"""
            WITH historical_sales AS (
                SELECT
                    item_name,
                    COUNT(*) as order_count,
                    SUM(qty) as total_qty,
                    AVG(item_price) as avg_price,
                    SUM(item_price * qty) as total_revenue
                FROM `{project_id}.{dataset_id}.sales_items_parsed`
                WHERE SAFE_CAST(bill_date AS DATE) BETWEEN '{req.start_date}' AND '{req.end_date}'
                  AND LOWER(item_name) LIKE LOWER('%{item_name}%')
                GROUP BY item_name
            )
            SELECT * FROM historical_sales
            """
            
            df, _ = query_to_df(client, cfg, base_query, purpose="api.oracle.simulate.price_change")
            
            if df.empty:
                return {
                    "ok": True,
                    "scenario": "price_change",
                    "message": "No historical data found for this item",
                    "baseline": {},
                    "simulated": {}
                }
            
            # Simple elasticity model (in production, use ML)
            # Assumption: 1% price increase = 0.5% demand decrease
            elasticity = -0.5
            qty_impact_pct = elasticity * price_change_pct
            
            baseline_revenue = float(df['total_revenue'].sum())
            baseline_qty = float(df['total_qty'].sum())
            baseline_price = float(df['avg_price'].mean())
            
            simulated_price = baseline_price * (1 + price_change_pct / 100)
            simulated_qty = baseline_qty * (1 + qty_impact_pct / 100)
            simulated_revenue = simulated_price * simulated_qty
            
            revenue_impact = simulated_revenue - baseline_revenue
            revenue_impact_pct = (revenue_impact / baseline_revenue) * 100 if baseline_revenue > 0 else 0
            
            return {
                "ok": True,
                "scenario": "price_change",
                "item_name": item_name,
                "baseline": {
                    "avg_price": round(baseline_price, 2),
                    "total_qty": round(baseline_qty, 2),
                    "total_revenue": round(baseline_revenue, 2)
                },
                "simulated": {
                    "new_price": round(simulated_price, 2),
                    "estimated_qty": round(simulated_qty, 2),
                    "estimated_revenue": round(simulated_revenue, 2)
                },
                "impact": {
                    "revenue_change": round(revenue_impact, 2),
                    "revenue_change_pct": round(revenue_impact_pct, 2),
                    "qty_change_pct": round(qty_impact_pct, 2)
                },
                "recommendation": "Increase price" if revenue_impact > 0 else "Keep current price"
            }
        
        elif req.scenario_type == "vendor_switch":
            ingredient = req.parameters.get("ingredient", "")
            current_cost = req.parameters.get("current_cost_per_unit", 0)
            new_cost = req.parameters.get("new_cost_per_unit", 0)
            
            # Calculate usage from recipes and sales
            usage_query = f"""
            SELECT
                SUM(r.qty_required * COALESCE(s.total_qty, 0)) as total_usage_estimated
            FROM `{project_id}.{dataset_id}.recipes_sales_master` r
            LEFT JOIN (
                SELECT item_name, SUM(qty) as total_qty
                FROM `{project_id}.{dataset_id}.sales_items_parsed`
                WHERE SAFE_CAST(bill_date AS DATE) BETWEEN '{req.start_date}' AND '{req.end_date}'
                GROUP BY item_name
            ) s ON LOWER(r.item_name) = LOWER(s.item_name)
            WHERE LOWER(r.ingredient_name) LIKE LOWER('%{ingredient}%')
            """
            
            df, _ = query_to_df(client, cfg, usage_query, purpose="api.oracle.simulate.vendor_switch")
            
            total_usage = float(df['total_usage_estimated'].iloc[0]) if not df.empty else 0
            
            current_total_cost = total_usage * current_cost
            new_total_cost = total_usage * new_cost
            savings = current_total_cost - new_total_cost
            savings_pct = (savings / current_total_cost) * 100 if current_total_cost > 0 else 0
            
            return {
                "ok": True,
                "scenario": "vendor_switch",
                "ingredient": ingredient,
                "estimated_usage": round(total_usage, 2),
                "current_total_cost": round(current_total_cost, 2),
                "new_total_cost": round(new_total_cost, 2),
                "savings": round(savings, 2),
                "savings_pct": round(savings_pct, 2),
                "recommendation": "Switch vendor" if savings > 0 else "Keep current vendor"
            }
        
        else:
            return {
                "ok": False,
                "error": f"Scenario type '{req.scenario_type}' not implemented yet"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deduce")
def deductive_reasoning(req: DeductiveReasoningRequest) -> Dict[str, Any]:
    """
    Deductive Reasoning Engine - Find Root Cause and Suggest Action
    
    Example: "Maida inventory is -526g"
    AI deduces:
    1. Missing purchase bill (most likely)
    2. Recipe calculation error (possible)
    3. Wastage not logged (possible)
    
    Then suggests exact corrective action.
    """
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected")
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        
        # Parse problem to detect issue type
        problem_lower = req.problem.lower()
        
        if "negative" in problem_lower and "inventory" in problem_lower:
            # Extract ingredient name (simplified parsing)
            ingredient_name = ""
            for word in req.problem.split():
                if word not in ["negative", "inventory", "is", "-", "g", "kg", "ml", "l"]:
                    ingredient_name = word
                    break
            
            # Investigation queries
            investigation = {}
            
            # 1. Check recent purchases
            purchase_query = f"""
            SELECT
                MAX(SAFE_CAST(date AS DATE)) as last_purchase_date,
                COUNT(*) as purchase_count_30d
            FROM `{project_id}.{dataset_id}.purchases_master`
            WHERE LOWER(item_name) LIKE LOWER('%{ingredient_name}%')
              AND SAFE_CAST(date AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            """
            
            try:
                df_purchase, _ = query_to_df(client, cfg, purchase_query, purpose="api.oracle.deduce.purchases")
                if not df_purchase.empty:
                    investigation["last_purchase"] = str(df_purchase['last_purchase_date'].iloc[0])
                    investigation["purchase_count_30d"] = int(df_purchase['purchase_count_30d'].iloc[0])
            except:
                investigation["last_purchase"] = "unknown"
                investigation["purchase_count_30d"] = 0
            
            # 2. Check recipe usage
            usage_query = f"""
            SELECT
                COUNT(DISTINCT item_name) as recipe_count,
                SUM(qty_required) as total_qty_per_batch
            FROM `{project_id}.{dataset_id}.recipes_sales_master`
            WHERE LOWER(ingredient_name) LIKE LOWER('%{ingredient_name}%')
            """
            
            try:
                df_usage, _ = query_to_df(client, cfg, usage_query, purpose="api.oracle.deduce.usage")
                if not df_usage.empty:
                    investigation["recipe_count"] = int(df_usage['recipe_count'].iloc[0])
                    investigation["usage_per_batch"] = float(df_usage['total_qty_per_batch'].iloc[0])
            except:
                investigation["recipe_count"] = 0
                investigation["usage_per_batch"] = 0
            
            # 3. Check wastage logs
            wastage_query = f"""
            SELECT
                SUM(SAFE_CAST(amount AS FLOAT64)) as total_wastage_30d
            FROM `{project_id}.{dataset_id}.wastage_log`
            WHERE LOWER(item_name) LIKE LOWER('%{ingredient_name}%')
              AND SAFE_CAST(date AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            """
            
            try:
                df_wastage, _ = query_to_df(client, cfg, wastage_query, purpose="api.oracle.deduce.wastage")
                if not df_wastage.empty:
                    investigation["wastage_30d"] = float(df_wastage['total_wastage_30d'].iloc[0] or 0)
            except:
                investigation["wastage_30d"] = 0
            
            # Deductive logic
            root_causes = []
            corrective_actions = []
            
            # Hypothesis 1: Missing purchase bill (HIGH probability)
            if investigation.get("purchase_count_30d", 0) < 2:
                root_causes.append({
                    "hypothesis": "Missing purchase bill",
                    "probability": "HIGH",
                    "evidence": f"Only {investigation.get('purchase_count_30d', 0)} purchases logged in last 30 days"
                })
                corrective_actions.append({
                    "action": "Upload missing purchase bill to Drive",
                    "priority": "IMMEDIATE",
                    "details": f"Check with supplier for {ingredient_name} bills from last 2 weeks"
                })
            
            # Hypothesis 2: Recipe calculation error
            if investigation.get("recipe_count", 0) > 0:
                root_causes.append({
                    "hypothesis": "Recipe over-calculation",
                    "probability": "MEDIUM",
                    "evidence": f"Used in {investigation.get('recipe_count')} recipes"
                })
                corrective_actions.append({
                    "action": "Audit recipe quantities",
                    "priority": "MEDIUM",
                    "details": f"Review {ingredient_name} quantities in all recipes"
                })
            
            # Hypothesis 3: Unlogged wastage
            if investigation.get("wastage_30d", 0) == 0:
                root_causes.append({
                    "hypothesis": "Wastage not logged",
                    "probability": "LOW",
                    "evidence": "No wastage entries found"
                })
                corrective_actions.append({
                    "action": "Log any recent wastage",
                    "priority": "LOW",
                    "details": "Check kitchen for unreported spoilage or spillage"
                })
            
            return {
                "ok": True,
                "problem": req.problem,
                "ingredient": ingredient_name,
                "investigation": investigation,
                "root_causes": root_causes,
                "corrective_actions": corrective_actions,
                "confidence": "HIGH" if len(root_causes) > 0 else "LOW"
            }
        
        else:
            # Generic reasoning for other problems
            return {
                "ok": True,
                "problem": req.problem,
                "message": "Deductive reasoning for this problem type not yet implemented",
                "suggestion": "Use AI chat for analysis"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fraud/kot-reconciliation")
def fraud_detection_kot(
    org_id: str = Query(...),
    location_id: str = Query(...),
    date: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Loss Prevention Auditor
    Cross-reference KOT (Kitchen Order Tickets) vs Final Bills
    
    Flags:
    - Un-billed items (KOT exists but no bill)
    - Suspicious discounts (>20% without manager approval)
    - Cancelled orders after food prep
    """
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected")
    
    try:
        target_date = date or datetime.now().date().isoformat()
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        
        # This requires KOT data table (not in current schema)
        # Placeholder for future implementation
        
        return {
            "ok": True,
            "date": target_date,
            "message": "KOT reconciliation requires KOT data table (not yet implemented)",
            "recommendation": "Integrate KOT system with Petpooja API or manual upload"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
