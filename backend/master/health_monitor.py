"""
Health Monitor - System and tenant health monitoring
Handles: Uptime tracking, error detection, data quality, sync status
"""

import json
from datetime import datetime, timezone, timedelta, date
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from google.cloud import bigquery

PROJECT_ID = "cafe-mellow-core-2026"
DATASET_ID = "cafe_operations"
bq = bigquery.Client(project=PROJECT_ID)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthAlert:
    """Health alert record"""
    alert_id: str
    tenant_id: Optional[str]  # None for system-wide alerts
    severity: AlertSeverity
    category: str  # sync, api, data_quality, usage, system
    title: str
    message: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


@dataclass
class TenantHealth:
    """Health status for a tenant"""
    tenant_id: str
    overall_status: HealthStatus
    score: float  # 0-100
    last_activity: Optional[datetime]
    sync_status: HealthStatus
    data_quality_score: float
    api_health: HealthStatus
    active_alerts: int
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """Overall system health"""
    status: HealthStatus
    uptime_percentage: float
    active_tenants: int
    total_tenants: int
    api_response_time_ms: float
    error_rate_24h: float
    active_alerts: int
    critical_alerts: int


class HealthMonitor:
    """
    Monitor health of system and all tenants
    """
    
    ALERTS_TABLE = f"{PROJECT_ID}.{DATASET_ID}.health_alerts"
    METRICS_TABLE = f"{PROJECT_ID}.{DATASET_ID}.health_metrics"
    
    @classmethod
    def init_tables(cls):
        """Initialize health monitoring tables"""
        # Alerts table
        alerts_schema = [
            bigquery.SchemaField("alert_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("tenant_id", "STRING"),
            bigquery.SchemaField("severity", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("message", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("resolved_at", "TIMESTAMP"),
            bigquery.SchemaField("resolved_by", "STRING"),
        ]
        
        # Metrics table for time-series health data
        metrics_schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("tenant_id", "STRING"),
            bigquery.SchemaField("metric_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("metric_value", "FLOAT64"),
            bigquery.SchemaField("metadata", "JSON"),
        ]
        
        for table_id, schema in [
            (cls.ALERTS_TABLE, alerts_schema),
            (cls.METRICS_TABLE, metrics_schema),
        ]:
            table = bigquery.Table(table_id, schema=schema)
            try:
                bq.create_table(table)
                print(f"Created table {table_id}")
            except Exception as e:
                if "Already Exists" in str(e):
                    print(f"Table {table_id} already exists")
                else:
                    raise e
    
    @classmethod
    def create_alert(
        cls,
        severity: AlertSeverity,
        category: str,
        title: str,
        message: str,
        tenant_id: Optional[str] = None,
    ) -> str:
        """Create a new health alert"""
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(title) % 10000}"
        
        row = {
            "alert_id": alert_id,
            "tenant_id": tenant_id,
            "severity": severity.value,
            "category": category,
            "title": title,
            "message": message,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "resolved_at": None,
            "resolved_by": None,
        }
        
        errors = bq.insert_rows_json(cls.ALERTS_TABLE, [row])
        if errors:
            print(f"Alert creation error: {errors}")
        
        return alert_id
    
    @classmethod
    def resolve_alert(cls, alert_id: str, resolved_by: str) -> bool:
        """Resolve an alert"""
        query = f"""
            UPDATE `{cls.ALERTS_TABLE}`
            SET resolved_at = CURRENT_TIMESTAMP(),
                resolved_by = '{resolved_by}'
            WHERE alert_id = '{alert_id}'
        """
        bq.query(query).result()
        return True
    
    @classmethod
    def get_active_alerts(
        cls,
        tenant_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 50,
    ) -> List[HealthAlert]:
        """Get active (unresolved) alerts"""
        conditions = ["resolved_at IS NULL"]
        
        if tenant_id:
            conditions.append(f"(tenant_id = '{tenant_id}' OR tenant_id IS NULL)")
        
        if severity:
            conditions.append(f"severity = '{severity.value}'")
        
        query = f"""
            SELECT * FROM `{cls.ALERTS_TABLE}`
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT {limit}
        """
        
        results = bq.query(query).result()
        return [
            HealthAlert(
                alert_id=row.alert_id,
                tenant_id=row.tenant_id,
                severity=AlertSeverity(row.severity),
                category=row.category,
                title=row.title,
                message=row.message,
                created_at=row.created_at,
                resolved_at=row.resolved_at,
                resolved_by=row.resolved_by,
            )
            for row in results
        ]
    
    @classmethod
    def record_metric(
        cls,
        metric_name: str,
        metric_value: float,
        tenant_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """Record a health metric"""
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "metadata": metadata or {},
        }
        
        errors = bq.insert_rows_json(cls.METRICS_TABLE, [row])
        if errors:
            print(f"Metric recording error: {errors}")
    
    @classmethod
    def get_tenant_health(cls, tenant_id: str) -> TenantHealth:
        """Calculate health status for a tenant"""
        # Get last activity
        activity_query = f"""
            SELECT MAX(date) as last_active
            FROM `{PROJECT_ID}.{DATASET_ID}.tenant_usage`
            WHERE tenant_id = '{tenant_id}'
        """
        activity_result = list(bq.query(activity_query).result())
        last_activity = activity_result[0].last_active if activity_result else None
        
        # Get active alerts count
        alerts = cls.get_active_alerts(tenant_id=tenant_id)
        active_alerts = len(alerts)
        critical_alerts = len([a for a in alerts if a.severity == AlertSeverity.CRITICAL])
        
        # Calculate data quality score (simplified)
        data_quality_score = 95.0  # Default good
        
        # Check quarantine for data quality issues
        quarantine_query = f"""
            SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET_ID}.quarantine`
            WHERE tenant_id = '{tenant_id}' AND status = 'pending'
        """
        try:
            quarantine_result = list(bq.query(quarantine_query).result())
            quarantine_count = quarantine_result[0].cnt if quarantine_result else 0
            if quarantine_count > 10:
                data_quality_score -= 20
            elif quarantine_count > 5:
                data_quality_score -= 10
        except:
            pass
        
        # Determine overall status
        if critical_alerts > 0:
            overall_status = HealthStatus.CRITICAL
            score = 30.0
        elif active_alerts > 3:
            overall_status = HealthStatus.WARNING
            score = 60.0
        elif data_quality_score < 70:
            overall_status = HealthStatus.WARNING
            score = 70.0
        else:
            overall_status = HealthStatus.HEALTHY
            score = min(100.0, data_quality_score + (10 if active_alerts == 0 else 0))
        
        # Determine sync status
        days_since_activity = 0
        if last_activity:
            days_since_activity = (date.today() - last_activity).days
        
        if days_since_activity > 7:
            sync_status = HealthStatus.CRITICAL
        elif days_since_activity > 3:
            sync_status = HealthStatus.WARNING
        else:
            sync_status = HealthStatus.HEALTHY
        
        return TenantHealth(
            tenant_id=tenant_id,
            overall_status=overall_status,
            score=score,
            last_activity=datetime.combine(last_activity, datetime.min.time()) if last_activity else None,
            sync_status=sync_status,
            data_quality_score=data_quality_score,
            api_health=HealthStatus.HEALTHY,
            active_alerts=active_alerts,
            details={
                "critical_alerts": critical_alerts,
                "days_since_activity": days_since_activity,
                "quarantine_pending": quarantine_count if 'quarantine_count' in dir() else 0,
            },
        )
    
    @classmethod
    def get_system_health(cls) -> SystemHealth:
        """Get overall system health"""
        # Get tenant counts
        tenant_query = f"""
            SELECT 
                COUNT(*) as total,
                COUNTIF(status = 'active') as active
            FROM `{PROJECT_ID}.{DATASET_ID}.tenant_registry`
        """
        try:
            tenant_result = list(bq.query(tenant_query).result())
            total_tenants = tenant_result[0].total if tenant_result else 0
            active_tenants = tenant_result[0].active if tenant_result else 0
        except:
            total_tenants = 0
            active_tenants = 0
        
        # Get active alerts
        alerts = cls.get_active_alerts()
        active_alerts = len(alerts)
        critical_alerts = len([a for a in alerts if a.severity == AlertSeverity.CRITICAL])
        
        # Determine status
        if critical_alerts > 0:
            status = HealthStatus.CRITICAL
        elif active_alerts > 10:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.HEALTHY
        
        return SystemHealth(
            status=status,
            uptime_percentage=99.9,  # Would come from actual monitoring
            active_tenants=active_tenants,
            total_tenants=total_tenants,
            api_response_time_ms=150.0,  # Would come from actual metrics
            error_rate_24h=0.1,  # Would come from actual metrics
            active_alerts=active_alerts,
            critical_alerts=critical_alerts,
        )
    
    @classmethod
    def check_all_tenants(cls) -> List[Dict[str, Any]]:
        """Run health check on all tenants"""
        # Get all tenant IDs
        query = f"""
            SELECT tenant_id FROM `{PROJECT_ID}.{DATASET_ID}.tenant_registry`
            WHERE status = 'active'
        """
        
        results = []
        try:
            tenant_rows = bq.query(query).result()
            for row in tenant_rows:
                health = cls.get_tenant_health(row.tenant_id)
                results.append({
                    "tenant_id": health.tenant_id,
                    "status": health.overall_status.value,
                    "score": health.score,
                    "active_alerts": health.active_alerts,
                })
        except Exception as e:
            print(f"Health check error: {e}")
        
        return results
    
    @classmethod
    def get_alert_summary(cls) -> Dict[str, int]:
        """Get summary of alerts by severity"""
        query = f"""
            SELECT severity, COUNT(*) as count
            FROM `{cls.ALERTS_TABLE}`
            WHERE resolved_at IS NULL
            GROUP BY severity
        """
        
        summary = {s.value: 0 for s in AlertSeverity}
        try:
            results = bq.query(query).result()
            for row in results:
                summary[row.severity] = row.count
        except:
            pass
        
        return summary
