"""
Master Dashboard API Router
Super Admin endpoints for complete tenant and system management
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, EmailStr

from backend.master.tenant_registry import TenantRegistry, Tenant, TenantPlan, TenantStatus
from backend.master.usage_tracker import UsageTracker
from backend.master.feature_manager import FeatureManager, FEATURE_REGISTRY
from backend.master.health_monitor import HealthMonitor, AlertSeverity
from backend.master.ai_watchdog import AIWatchdog, InsightType, InsightPriority

router = APIRouter(prefix="/api/v1/master", tags=["Master Dashboard"])


# ============ Request/Response Models ============

class CreateTenantRequest(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    plan: str = "free"


class UpdateTenantRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    plan: Optional[str] = None
    status: Optional[str] = None


class UpdateCredentialsRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    petpooja_app_key: Optional[str] = None
    petpooja_app_secret: Optional[str] = None
    petpooja_access_token: Optional[str] = None
    drive_folder_expenses: Optional[str] = None
    drive_folder_purchases: Optional[str] = None
    drive_folder_inventory: Optional[str] = None


class FeatureOverrideRequest(BaseModel):
    feature_id: str
    enabled: bool
    reason: str


class CreateAlertRequest(BaseModel):
    severity: str
    category: str
    title: str
    message: str
    tenant_id: Optional[str] = None


class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    email: str
    phone: Optional[str]
    plan: str
    status: str
    created_at: str
    last_activity: Optional[str]
    health_score: float
    features: Dict[str, Any]


class OverviewResponse(BaseModel):
    total_tenants: int
    active_tenants: int
    total_cost_today: float
    total_cost_week: float
    active_alerts: int
    critical_alerts: int
    system_status: str
    ai_insights_pending: int


# ============ Startup ============

@router.on_event("startup")
async def init_master_tables():
    """Initialize all master dashboard tables"""
    try:
        TenantRegistry.init_table()
        UsageTracker.init_table()
        FeatureManager.init_table()
        HealthMonitor.init_tables()
        AIWatchdog.init_tables()
        print("Master Dashboard tables initialized")
    except Exception as e:
        print(f"Master table init warning: {e}")


@router.on_event("shutdown")
async def cleanup_master_resources():
    """Clean shutdown handler for master dashboard resources"""
    try:
        # Close any active monitoring connections or background tasks
        print("Master Dashboard resources cleaned up")
    except Exception as e:
        print(f"Master cleanup warning: {e}")


# ============ Health & Overview ============

@router.get("/health")
async def master_health():
    """Master dashboard health check"""
    return {"ok": True, "service": "master_dashboard", "version": "1.0.0"}


@router.get("/stats")
async def get_stats():
    """Get quick system stats"""
    try:
        total = TenantRegistry.get_tenant_count()
        active = TenantRegistry.get_tenant_count(TenantStatus.ACTIVE)
        system_health = HealthMonitor.get_system_health()
        
        return {
            "ok": True,
            "total_tenants": total,
            "active_tenants": active,
            "system_status": system_health.status.value,
            "active_alerts": system_health.active_alerts,
        }
    except Exception as e:
        return {"ok": True, "total_tenants": 0, "error": str(e)}


@router.get("/overview", response_model=OverviewResponse)
async def get_overview():
    """Get master dashboard overview"""
    try:
        # Get tenant counts
        total = TenantRegistry.get_tenant_count()
        active = TenantRegistry.get_tenant_count(TenantStatus.ACTIVE)
        
        # Get cost data
        cost_breakdown = UsageTracker.get_cost_breakdown(days=1)
        cost_week = UsageTracker.get_cost_breakdown(days=7)
        
        # Get system health
        system_health = HealthMonitor.get_system_health()
        
        # Get pending insights
        insights = AIWatchdog.get_insights(unacknowledged_only=True, limit=100)
        
        return OverviewResponse(
            total_tenants=total,
            active_tenants=active,
            total_cost_today=cost_breakdown.get("total", 0),
            total_cost_week=cost_week.get("total", 0),
            active_alerts=system_health.active_alerts,
            critical_alerts=system_health.critical_alerts,
            system_status=system_health.status.value,
            ai_insights_pending=len(insights),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Tenant Management ============

@router.get("/tenants")
async def list_tenants(
    status: Optional[str] = None,
    plan: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """List all tenants with optional filters"""
    try:
        status_enum = TenantStatus(status) if status else None
        plan_enum = TenantPlan(plan) if plan else None
        
        tenants = TenantRegistry.list_tenants(
            status=status_enum,
            plan=plan_enum,
            limit=limit,
            offset=offset,
        )
        
        return {
            "tenants": [
                {
                    "tenant_id": t.tenant_id,
                    "name": t.name,
                    "email": t.email,
                    "plan": t.plan.value,
                    "status": t.status.value,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "last_activity": t.last_activity.isoformat() if t.last_activity else None,
                    "health_score": t.health_score,
                }
                for t in tenants
            ],
            "count": len(tenants),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str):
    """Get detailed tenant information"""
    try:
        tenant = TenantRegistry.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Get usage summary
        usage = UsageTracker.get_usage_summary(tenant_id, days=30)
        
        # Get health status
        health = HealthMonitor.get_tenant_health(tenant_id)
        
        # Get features
        features = FeatureManager.get_tenant_features(tenant_id, tenant.plan.value)
        
        return {
            "tenant": {
                "tenant_id": tenant.tenant_id,
                "name": tenant.name,
                "email": tenant.email,
                "phone": tenant.phone,
                "plan": tenant.plan.value,
                "status": tenant.status.value,
                "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
                "last_activity": tenant.last_activity.isoformat() if tenant.last_activity else None,
                "health_score": tenant.health_score,
                "settings": {
                    "timezone": tenant.settings.timezone,
                    "currency": tenant.settings.currency,
                    "ai_model": tenant.settings.ai_model,
                },
            },
            "usage": {
                "total_ai_tokens": usage.total_ai_tokens,
                "total_ai_cost": usage.total_ai_cost,
                "total_bq_cost": usage.total_bq_cost,
                "total_api_calls": usage.total_api_calls,
                "avg_daily_messages": usage.avg_daily_messages,
            },
            "health": {
                "status": health.overall_status.value,
                "score": health.score,
                "sync_status": health.sync_status.value,
                "data_quality_score": health.data_quality_score,
                "active_alerts": health.active_alerts,
            },
            "features": features,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tenants")
async def create_tenant(request: CreateTenantRequest):
    """Create a new tenant"""
    try:
        plan = TenantPlan(request.plan)
        tenant = TenantRegistry.create_tenant(
            name=request.name,
            email=request.email,
            phone=request.phone,
            plan=plan,
        )
        
        return {
            "success": True,
            "tenant_id": tenant.tenant_id,
            "message": f"Tenant '{tenant.name}' created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tenants/{tenant_id}")
async def update_tenant(tenant_id: str, request: UpdateTenantRequest):
    """Update tenant details"""
    try:
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        if "plan" in updates:
            updates["plan"] = TenantPlan(updates["plan"])
        if "status" in updates:
            updates["status"] = TenantStatus(updates["status"])
        
        success = TenantRegistry.update_tenant(tenant_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return {"success": True, "message": "Tenant updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tenants/{tenant_id}/credentials")
async def update_tenant_credentials(tenant_id: str, request: UpdateCredentialsRequest):
    """Update tenant credentials (API keys, secrets)"""
    try:
        credentials = {k: v for k, v in request.dict().items() if v is not None}
        
        success = TenantRegistry.update_credentials(tenant_id, credentials)
        
        if not success:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return {"success": True, "message": "Credentials updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tenants/{tenant_id}/pause")
async def pause_tenant(tenant_id: str):
    """Pause a tenant account"""
    success = TenantRegistry.pause_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"success": True, "message": "Tenant paused"}


@router.post("/tenants/{tenant_id}/activate")
async def activate_tenant(tenant_id: str):
    """Activate a tenant account"""
    success = TenantRegistry.activate_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"success": True, "message": "Tenant activated"}


@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(tenant_id: str):
    """Suspend a tenant account"""
    success = TenantRegistry.suspend_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"success": True, "message": "Tenant suspended"}


@router.post("/tenants/{tenant_id}/change-plan")
async def change_tenant_plan(tenant_id: str, plan: str):
    """Change tenant subscription plan"""
    try:
        plan_enum = TenantPlan(plan)
        success = TenantRegistry.change_plan(tenant_id, plan_enum)
        
        if not success:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return {"success": True, "message": f"Plan changed to {plan}"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan")


# ============ Usage & Cost Analytics ============

@router.get("/usage")
async def get_all_usage(days: int = Query(default=7, le=90)):
    """Get usage analytics for all tenants"""
    try:
        all_usage = UsageTracker.get_all_tenants_usage(days=days)
        top_users = UsageTracker.get_top_users(days=days, limit=10)
        cost_breakdown = UsageTracker.get_cost_breakdown(days=days)
        
        return {
            "period_days": days,
            "all_tenants": all_usage,
            "top_users": top_users,
            "cost_breakdown": cost_breakdown,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/{tenant_id}")
async def get_tenant_usage(tenant_id: str, days: int = Query(default=30, le=90)):
    """Get detailed usage for a specific tenant"""
    try:
        summary = UsageTracker.get_usage_summary(tenant_id, days=days)
        
        # Get tenant to check limits
        tenant = TenantRegistry.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        limits = UsageTracker.check_usage_limits(tenant_id, tenant.features)
        
        return {
            "tenant_id": tenant_id,
            "period_days": days,
            "summary": {
                "total_ai_tokens": summary.total_ai_tokens,
                "total_ai_cost": summary.total_ai_cost,
                "total_bq_cost": summary.total_bq_cost,
                "total_api_calls": summary.total_api_calls,
                "avg_daily_messages": summary.avg_daily_messages,
                "total_reports": summary.total_reports,
                "total_tasks": summary.total_tasks,
            },
            "limits": limits,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Feature Management ============

@router.get("/features")
async def list_features():
    """List all available features"""
    features = FeatureManager.get_all_features()
    by_category = FeatureManager.get_features_by_category()
    
    return {
        "features": [
            {
                "feature_id": f.feature_id,
                "name": f.name,
                "description": f.description,
                "tiers": f.tiers,
                "category": f.category,
                "is_beta": f.is_beta,
                "rollout_percentage": f.rollout_percentage,
            }
            for f in features
        ],
        "by_category": {
            cat: [f.feature_id for f in feats]
            for cat, feats in by_category.items()
        },
    }


@router.get("/features/tiers/{tier}")
async def get_tier_features(tier: str):
    """Get features available for a subscription tier"""
    features = FeatureManager.get_features_for_tier(tier)
    return {"tier": tier, "features": features}


@router.post("/tenants/{tenant_id}/features/override")
async def set_feature_override(tenant_id: str, request: FeatureOverrideRequest):
    """Set a feature override for a tenant"""
    try:
        success = FeatureManager.set_feature_override(
            tenant_id=tenant_id,
            feature_id=request.feature_id,
            enabled=request.enabled,
            reason=request.reason,
            admin_id="master_admin",  # Would come from auth
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to set override")
        
        return {"success": True, "message": f"Feature '{request.feature_id}' override set"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tenants/{tenant_id}/features/override/{feature_id}")
async def remove_feature_override(tenant_id: str, feature_id: str):
    """Remove a feature override"""
    success = FeatureManager.remove_feature_override(tenant_id, feature_id)
    return {"success": success, "message": "Override removed"}


# ============ Health Monitoring ============

@router.get("/health/system")
async def get_system_health():
    """Get overall system health"""
    health = HealthMonitor.get_system_health()
    return {
        "status": health.status.value,
        "uptime_percentage": health.uptime_percentage,
        "active_tenants": health.active_tenants,
        "total_tenants": health.total_tenants,
        "api_response_time_ms": health.api_response_time_ms,
        "error_rate_24h": health.error_rate_24h,
        "active_alerts": health.active_alerts,
        "critical_alerts": health.critical_alerts,
    }


@router.get("/health/tenants")
async def check_all_tenant_health():
    """Run health check on all tenants"""
    results = HealthMonitor.check_all_tenants()
    return {"tenants": results, "checked_at": datetime.now().isoformat()}


@router.get("/health/{tenant_id}")
async def get_tenant_health(tenant_id: str):
    """Get health status for a specific tenant"""
    health = HealthMonitor.get_tenant_health(tenant_id)
    return {
        "tenant_id": health.tenant_id,
        "status": health.overall_status.value,
        "score": health.score,
        "last_activity": health.last_activity.isoformat() if health.last_activity else None,
        "sync_status": health.sync_status.value,
        "data_quality_score": health.data_quality_score,
        "api_health": health.api_health.value,
        "active_alerts": health.active_alerts,
        "details": health.details,
    }


# ============ Alerts ============

@router.get("/alerts")
async def list_alerts(
    tenant_id: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    """List active alerts"""
    try:
        sev = AlertSeverity(severity) if severity else None
        alerts = HealthMonitor.get_active_alerts(
            tenant_id=tenant_id,
            severity=sev,
            limit=limit,
        )
        
        return {
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "tenant_id": a.tenant_id,
                    "severity": a.severity.value,
                    "category": a.category,
                    "title": a.title,
                    "message": a.message,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in alerts
            ],
            "count": len(alerts),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts")
async def create_alert(request: CreateAlertRequest):
    """Create a new alert"""
    try:
        alert_id = HealthMonitor.create_alert(
            severity=AlertSeverity(request.severity),
            category=request.category,
            title=request.title,
            message=request.message,
            tenant_id=request.tenant_id,
        )
        
        return {"success": True, "alert_id": alert_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert"""
    success = HealthMonitor.resolve_alert(alert_id, "master_admin")
    return {"success": success, "message": "Alert resolved"}


@router.get("/alerts/summary")
async def get_alert_summary():
    """Get summary of alerts by severity"""
    summary = HealthMonitor.get_alert_summary()
    return {"summary": summary}


# ============ AI Watchdog ============

@router.get("/ai/insights")
async def list_insights(
    tenant_id: Optional[str] = None,
    insight_type: Optional[str] = None,
    priority: Optional[str] = None,
    unacknowledged_only: bool = False,
    limit: int = Query(default=50, le=200),
):
    """List AI-generated insights"""
    try:
        itype = InsightType(insight_type) if insight_type else None
        prio = InsightPriority(priority) if priority else None
        
        insights = AIWatchdog.get_insights(
            tenant_id=tenant_id,
            insight_type=itype,
            priority=prio,
            unacknowledged_only=unacknowledged_only,
            limit=limit,
        )
        
        return {
            "insights": [
                {
                    "insight_id": i.insight_id,
                    "type": i.insight_type.value,
                    "priority": i.priority.value,
                    "tenant_id": i.tenant_id,
                    "title": i.title,
                    "description": i.description,
                    "recommendation": i.recommendation,
                    "data": i.data,
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                    "acknowledged": i.acknowledged,
                }
                for i in insights
            ],
            "count": len(insights),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/insights/{insight_id}/acknowledge")
async def acknowledge_insight(insight_id: str):
    """Acknowledge an AI insight"""
    success = AIWatchdog.acknowledge_insight(insight_id, "master_admin")
    return {"success": success, "message": "Insight acknowledged"}


@router.get("/ai/digest")
async def get_daily_digest():
    """Get AI-generated daily digest"""
    digest = AIWatchdog.get_daily_digest()
    return digest


@router.post("/ai/run-analysis")
async def run_ai_analysis():
    """Manually trigger AI analysis on all tenants"""
    try:
        insights = AIWatchdog.run_daily_analysis()
        return {
            "success": True,
            "insights_generated": len(insights),
            "message": f"Analysis complete. {len(insights)} new insights generated.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Inactive Tenants ============

@router.get("/tenants/inactive")
async def get_inactive_tenants(days: int = Query(default=7, le=30)):
    """Get list of inactive tenants"""
    inactive = UsageTracker.get_inactive_tenants(days=days)
    return {
        "inactive_tenants": inactive,
        "count": len(inactive),
        "threshold_days": days,
    }
