"""
HR Router - Human Resources & Payroll APIs
Uses Entity model for Employee/Vendor distinction
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr

from backend.core.security import Entity, EntityType

router = APIRouter(prefix="/api/v1/hr", tags=["hr"])


class EntityCreateRequest(BaseModel):
    """Request to create an entity"""
    entity_type: EntityType
    name: str
    org_id: str
    location_id: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    employee_id: Optional[str] = None
    vendor_code: Optional[str] = None
    payment_details: Optional[dict] = None
    tax_details: Optional[dict] = None


@router.post("/entities")
async def create_entity(request: EntityCreateRequest):
    """
    Create a new entity (Employee/Vendor/Contractor)
    CRITICAL: Entities are NOT Users
    """
    try:
        import uuid
        from google.cloud import bigquery
        from pillars.config_vault import EffectiveSettings
        
        cfg = EffectiveSettings()
        client = bigquery.Client.from_service_account_json(cfg.KEY_FILE)
        
        entity = Entity(
            id=str(uuid.uuid4()),
            entity_type=request.entity_type,
            name=request.name,
            org_id=request.org_id,
            location_id=request.location_id,
            contact_phone=request.contact_phone,
            contact_email=request.contact_email,
            employee_id=request.employee_id,
            vendor_code=request.vendor_code,
            payment_details=request.payment_details,
            tax_details=request.tax_details,
        )
        
        table_id = f"{cfg.PROJECT_ID}.{cfg.DATASET_ID}.entities"
        
        rows = [entity.dict()]
        errors = client.insert_rows_json(table_id, rows)
        
        if errors:
            raise HTTPException(status_code=500, detail=f"Insert failed: {errors}")
        
        return {"ok": True, "entity_id": entity.id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities")
async def list_entities(
    org_id: str = Query(...),
    location_id: Optional[str] = Query(None),
    entity_type: Optional[EntityType] = Query(None),
    is_active: bool = Query(True),
    limit: int = Query(100, le=500)
):
    """List entities with tenant isolation"""
    try:
        from google.cloud import bigquery
        from pillars.config_vault import EffectiveSettings
        from backend.core.security import TenantContext
        from utils.bq_guardrails import query_to_df
        
        cfg = EffectiveSettings()
        client = bigquery.Client.from_service_account_json(cfg.KEY_FILE)
        
        context = TenantContext(org_id=org_id, location_id=location_id or "", user_id="system")
        
        where_conditions = [context.to_sql_where()]
        where_conditions.append(f"is_active = {is_active}")
        
        if entity_type:
            where_conditions.append(f"entity_type = '{entity_type.value}'")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT *
        FROM `{cfg.PROJECT_ID}.{cfg.DATASET_ID}.entities`
        WHERE {where_clause}
        ORDER BY name
        LIMIT {limit}
        """
        
        df, _ = query_to_df(client, cfg, query, purpose="api.hr.list_entities")
        
        return {
            "ok": True,
            "entities": df.to_dict("records") if not df.empty else [],
            "count": len(df)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payroll/calculate")
async def calculate_payroll(
    org_id: str = Query(...),
    location_id: str = Query(...),
    period_start: str = Query(...),
    period_end: str = Query(...)
):
    """
    Calculate payroll for a period
    Uses ledger entries for salary advances and deductions
    """
    try:
        from google.cloud import bigquery
        from pillars.config_vault import EffectiveSettings
        from utils.bq_guardrails import query_to_df
        
        cfg = EffectiveSettings()
        client = bigquery.Client.from_service_account_json(cfg.KEY_FILE)
        
        query = f"""
        WITH employees AS (
            SELECT id, name, employee_id, payment_details
            FROM `{cfg.PROJECT_ID}.{cfg.DATASET_ID}.entities`
            WHERE org_id = '{org_id}' 
                AND location_id = '{location_id}'
                AND entity_type = 'employee'
                AND is_active = TRUE
        ),
        advances AS (
            SELECT 
                entity_id,
                SUM(amount) as total_advances
            FROM `{cfg.PROJECT_ID}.{cfg.DATASET_ID}.ledger_universal`
            WHERE org_id = '{org_id}' 
                AND location_id = '{location_id}'
                AND type = 'SALARY_ADVANCE'
                AND entry_date BETWEEN DATE('{period_start}') AND DATE('{period_end}')
            GROUP BY entity_id
        )
        SELECT 
            e.id,
            e.name,
            e.employee_id,
            JSON_VALUE(e.payment_details, '$.monthly_salary') as monthly_salary,
            COALESCE(a.total_advances, 0) as advances,
            CAST(JSON_VALUE(e.payment_details, '$.monthly_salary') AS FLOAT64) - COALESCE(a.total_advances, 0) as net_payable
        FROM employees e
        LEFT JOIN advances a ON e.id = a.entity_id
        ORDER BY e.name
        """
        
        df, _ = query_to_df(client, cfg, query, purpose="api.hr.calculate_payroll")
        
        return {
            "ok": True,
            "period_start": period_start,
            "period_end": period_end,
            "payroll": df.to_dict("records") if not df.empty else [],
            "total_payable": float(df["net_payable"].sum()) if not df.empty else 0
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
