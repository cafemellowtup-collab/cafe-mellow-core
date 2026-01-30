"""
AI Watchdog - Proactive AI monitoring and insights
Handles: Anomaly detection, churn prediction, usage insights, automated alerts
"""

import json
from datetime import datetime, timezone, timedelta, date
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError

PROJECT_ID = "cafe-mellow-core-2026"
DATASET_ID = "cafe_operations"
_bq_init_error: Optional[Exception] = None
try:
    bq = bigquery.Client(project=PROJECT_ID)
except DefaultCredentialsError as e:
    bq = None
    _bq_init_error = e
except Exception as e:
    bq = None
    _bq_init_error = e


class InsightType(str, Enum):
    USAGE_ANOMALY = "usage_anomaly"
    CHURN_RISK = "churn_risk"
    GROWTH_OPPORTUNITY = "growth_opportunity"
    COST_ALERT = "cost_alert"
    FEATURE_SUGGESTION = "feature_suggestion"
    ENGAGEMENT_DROP = "engagement_drop"
    HIGH_PERFORMER = "high_performer"


class InsightPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class AIInsight:
    """AI-generated insight about a tenant or system"""
    insight_id: str
    insight_type: InsightType
    priority: InsightPriority
    tenant_id: Optional[str]
    title: str
    description: str
    recommendation: str
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class AIWatchdog:
    """
    AI-powered proactive monitoring and insights generation
    """
    
    TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.ai_insights"
    
    @classmethod
    def init_tables(cls):
        """Initialize AI watchdog tables"""
        schema = [
            bigquery.SchemaField("insight_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("insight_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("priority", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("tenant_id", "STRING"),
            bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("recommendation", "STRING"),
            bigquery.SchemaField("data", "JSON"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("acknowledged", "BOOL"),
            bigquery.SchemaField("acknowledged_by", "STRING"),
            bigquery.SchemaField("acknowledged_at", "TIMESTAMP"),
        ]
        
        table = bigquery.Table(cls.TABLE_ID, schema=schema)
        try:
            if bq:
                bq.create_table(table)
                print(f"Created table {cls.TABLE_ID}")
        except Exception as e:
            if "Already Exists" in str(e):
                print(f"Table {cls.TABLE_ID} already exists")
            else:
                raise e
    
    @classmethod
    def get_insights(
        cls,
        tenant_id: Optional[str] = None,
        insight_type: Optional[InsightType] = None,
        priority: Optional[InsightPriority] = None,
        unacknowledged_only: bool = False,
        limit: int = 50,
    ) -> List[AIInsight]:
        """Get AI insights with filters - Mock implementation"""
        # Mock insights for demonstration
        mock_insights = [
            AIInsight(
                insight_id="insight_001",
                insight_type=InsightType.GROWTH_OPPORTUNITY,
                priority=InsightPriority.HIGH,
                tenant_id="tenant_001",
                title="Revenue Growth Opportunity",
                description="Coffee sales showing 25% growth trend",
                recommendation="Consider expanding coffee menu offerings",
                data={"growth_rate": 25.3, "category": "beverages"}
            ),
            AIInsight(
                insight_id="insight_002",
                insight_type=InsightType.COST_ALERT,
                priority=InsightPriority.MEDIUM,
                tenant_id="tenant_002",
                title="Ingredient Cost Increase",
                description="Milk prices increased by 8% this month",
                recommendation="Consider bulk purchasing or alternative suppliers",
                data={"cost_increase": 8.2, "category": "ingredients"}
            )
        ]
        
        # Apply filters
        filtered = mock_insights
        if tenant_id:
            filtered = [i for i in filtered if i.tenant_id == tenant_id]
        if insight_type:
            filtered = [i for i in filtered if i.insight_type == insight_type]
        if priority:
            filtered = [i for i in filtered if i.priority == priority]
        if unacknowledged_only:
            filtered = [i for i in filtered if not i.acknowledged]
            
        return filtered[:limit]
    
    @classmethod
    def acknowledge_insight(cls, insight_id: str, admin_id: str) -> bool:
        """Acknowledge an insight - Mock implementation"""
        return True
    
    @classmethod
    def get_daily_digest(cls) -> Dict[str, Any]:
        """Get AI-generated daily digest - Mock implementation"""
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": "System health excellent, 2 growth opportunities identified",
            "key_insights": [
                "Coffee sales trending up 25%",
                "Milk costs increased 8% - action recommended"
            ],
            "recommendations": [
                "Expand coffee menu offerings",
                "Review milk suppliers for cost optimization"
            ],
            "tenant_count": 12,
            "alerts_generated": 3,
            "opportunities_found": 2
        }
    
    @classmethod
    def run_daily_analysis(cls) -> List[AIInsight]:
        """Run AI analysis on all tenants - Mock implementation"""
        insights = [
            AIInsight(
                insight_id="daily_001",
                insight_type=InsightType.HIGH_PERFORMER,
                priority=InsightPriority.LOW,
                tenant_id="tenant_001",
                title="Exceptional Performance",
                description="Tenant achieving 95% efficiency metrics",
                recommendation="Consider featuring as case study"
            ),
            AIInsight(
                insight_id="daily_002",
                insight_type=InsightType.ENGAGEMENT_DROP,
                priority=InsightPriority.MEDIUM,
                tenant_id="tenant_003",
                title="Usage Decline",
                description="20% drop in AI chat usage last week",
                recommendation="Proactive outreach to understand needs"
            )
        ]
        return insights




@dataclass
class TenantPattern:
    """Learned usage pattern for a tenant"""
    tenant_id: str
    avg_daily_messages: float
    avg_daily_logins: float
    peak_usage_hour: int
    most_used_features: List[str]
    activity_trend: str  # increasing, stable, decreasing
    engagement_score: float
    churn_risk_score: float


class AIWatchdog:
    """
    AI-powered monitoring and insights engine
    """
    
    INSIGHTS_TABLE = f"{PROJECT_ID}.{DATASET_ID}.ai_insights"
    PATTERNS_TABLE = f"{PROJECT_ID}.{DATASET_ID}.tenant_patterns"
    
    # Thresholds for anomaly detection
    USAGE_SPIKE_THRESHOLD = 2.0  # 2x normal usage
    USAGE_DROP_THRESHOLD = 0.3  # 30% of normal usage
    INACTIVITY_DAYS_WARNING = 5
    INACTIVITY_DAYS_CRITICAL = 10
    HIGH_COST_THRESHOLD_INR = 1000  # per day
    
    @classmethod
    def init_tables(cls):
        """Initialize AI watchdog tables"""
        insights_schema = [
            bigquery.SchemaField("insight_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("insight_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("priority", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("tenant_id", "STRING"),
            bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("recommendation", "STRING"),
            bigquery.SchemaField("data", "JSON"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("acknowledged", "BOOL"),
            bigquery.SchemaField("acknowledged_by", "STRING"),
        ]
        
        patterns_schema = [
            bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("avg_daily_messages", "FLOAT64"),
            bigquery.SchemaField("avg_daily_logins", "FLOAT64"),
            bigquery.SchemaField("peak_usage_hour", "INT64"),
            bigquery.SchemaField("most_used_features", "JSON"),
            bigquery.SchemaField("activity_trend", "STRING"),
            bigquery.SchemaField("engagement_score", "FLOAT64"),
            bigquery.SchemaField("churn_risk_score", "FLOAT64"),
            bigquery.SchemaField("updated_at", "TIMESTAMP"),
        ]
        
        for table_id, schema in [
            (cls.INSIGHTS_TABLE, insights_schema),
            (cls.PATTERNS_TABLE, patterns_schema),
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
    def run_daily_analysis(cls) -> List[AIInsight]:
        """Run daily AI analysis on all tenants"""
        insights = []
        
        # Get all active tenants
        tenant_query = f"""
            SELECT tenant_id, plan, created_at
            FROM `{PROJECT_ID}.{DATASET_ID}.tenant_registry`
            WHERE status = 'active'
        """
        
        try:
            tenants = list(bq.query(tenant_query).result())
        except:
            return insights
        
        for tenant in tenants:
            tenant_id = tenant.tenant_id
            
            # Check for usage anomalies
            anomaly = cls._detect_usage_anomaly(tenant_id)
            if anomaly:
                insights.append(anomaly)
            
            # Check for churn risk
            churn = cls._detect_churn_risk(tenant_id)
            if churn:
                insights.append(churn)
            
            # Check for cost alerts
            cost_alert = cls._check_cost_threshold(tenant_id)
            if cost_alert:
                insights.append(cost_alert)
            
            # Check for engagement drop
            engagement = cls._check_engagement_drop(tenant_id)
            if engagement:
                insights.append(engagement)
        
        # Save insights to database
        for insight in insights:
            cls._save_insight(insight)
        
        return insights
    
    @classmethod
    def _detect_usage_anomaly(cls, tenant_id: str) -> Optional[AIInsight]:
        """Detect unusual usage patterns"""
        # Get last 30 days average
        avg_query = f"""
            SELECT AVG(chat_messages) as avg_msgs, AVG(ai_tokens) as avg_tokens
            FROM `{PROJECT_ID}.{DATASET_ID}.tenant_usage`
            WHERE tenant_id = '{tenant_id}'
            AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            AND date < DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        """
        
        # Get yesterday's usage
        yesterday_query = f"""
            SELECT chat_messages, ai_tokens
            FROM `{PROJECT_ID}.{DATASET_ID}.tenant_usage`
            WHERE tenant_id = '{tenant_id}'
            AND date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        """
        
        try:
            avg_result = list(bq.query(avg_query).result())
            yesterday_result = list(bq.query(yesterday_query).result())
            
            if not avg_result or not yesterday_result:
                return None
            
            avg_msgs = avg_result[0].avg_msgs or 0
            yesterday_msgs = yesterday_result[0].chat_messages or 0
            
            if avg_msgs == 0:
                return None
            
            ratio = yesterday_msgs / avg_msgs
            
            if ratio > cls.USAGE_SPIKE_THRESHOLD:
                return AIInsight(
                    insight_id=f"anomaly_{tenant_id}_{date.today().isoformat()}",
                    insight_type=InsightType.USAGE_ANOMALY,
                    priority=InsightPriority.MEDIUM,
                    tenant_id=tenant_id,
                    title=f"Usage spike detected",
                    description=f"Yesterday's usage was {ratio:.1f}x higher than average ({yesterday_msgs} vs {avg_msgs:.0f} messages)",
                    recommendation="Review tenant activity to ensure this is legitimate usage and not abuse",
                    data={"ratio": ratio, "yesterday": yesterday_msgs, "average": avg_msgs},
                    created_at=datetime.now(timezone.utc),
                )
            
            if ratio < cls.USAGE_DROP_THRESHOLD and avg_msgs > 5:
                return AIInsight(
                    insight_id=f"drop_{tenant_id}_{date.today().isoformat()}",
                    insight_type=InsightType.ENGAGEMENT_DROP,
                    priority=InsightPriority.MEDIUM,
                    tenant_id=tenant_id,
                    title=f"Significant usage drop",
                    description=f"Yesterday's usage dropped to {ratio:.0%} of average ({yesterday_msgs} vs {avg_msgs:.0f} messages)",
                    recommendation="Reach out to tenant to check if they're experiencing issues",
                    data={"ratio": ratio, "yesterday": yesterday_msgs, "average": avg_msgs},
                    created_at=datetime.now(timezone.utc),
                )
        except Exception as e:
            print(f"Usage anomaly detection error: {e}")
        
        return None
    
    @classmethod
    def _detect_churn_risk(cls, tenant_id: str) -> Optional[AIInsight]:
        """Detect tenants at risk of churning"""
        # Get last activity date
        query = f"""
            SELECT MAX(date) as last_active
            FROM `{PROJECT_ID}.{DATASET_ID}.tenant_usage`
            WHERE tenant_id = '{tenant_id}'
            AND (chat_messages > 0 OR api_calls > 0)
        """
        
        try:
            result = list(bq.query(query).result())
            if not result or not result[0].last_active:
                return None
            
            last_active = result[0].last_active
            days_inactive = (date.today() - last_active).days
            
            if days_inactive >= cls.INACTIVITY_DAYS_CRITICAL:
                return AIInsight(
                    insight_id=f"churn_{tenant_id}_{date.today().isoformat()}",
                    insight_type=InsightType.CHURN_RISK,
                    priority=InsightPriority.HIGH,
                    tenant_id=tenant_id,
                    title=f"High churn risk - {days_inactive} days inactive",
                    description=f"This tenant hasn't used the platform in {days_inactive} days",
                    recommendation="Urgent: Schedule a check-in call or send re-engagement email",
                    data={"days_inactive": days_inactive, "last_active": last_active.isoformat()},
                    created_at=datetime.now(timezone.utc),
                )
            
            if days_inactive >= cls.INACTIVITY_DAYS_WARNING:
                return AIInsight(
                    insight_id=f"inactive_{tenant_id}_{date.today().isoformat()}",
                    insight_type=InsightType.CHURN_RISK,
                    priority=InsightPriority.MEDIUM,
                    tenant_id=tenant_id,
                    title=f"Declining engagement - {days_inactive} days inactive",
                    description=f"This tenant's activity has dropped significantly",
                    recommendation="Send a friendly check-in or feature highlight email",
                    data={"days_inactive": days_inactive, "last_active": last_active.isoformat()},
                    created_at=datetime.now(timezone.utc),
                )
        except Exception as e:
            print(f"Churn detection error: {e}")
        
        return None
    
    @classmethod
    def _check_cost_threshold(cls, tenant_id: str) -> Optional[AIInsight]:
        """Check if tenant is exceeding cost thresholds"""
        query = f"""
            SELECT SUM(ai_cost_inr + bq_cost_inr) as total_cost
            FROM `{PROJECT_ID}.{DATASET_ID}.tenant_usage`
            WHERE tenant_id = '{tenant_id}'
            AND date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        """
        
        try:
            result = list(bq.query(query).result())
            if not result:
                return None
            
            total_cost = result[0].total_cost or 0
            
            if total_cost > cls.HIGH_COST_THRESHOLD_INR:
                return AIInsight(
                    insight_id=f"cost_{tenant_id}_{date.today().isoformat()}",
                    insight_type=InsightType.COST_ALERT,
                    priority=InsightPriority.HIGH,
                    tenant_id=tenant_id,
                    title=f"High cost alert - ₹{total_cost:.2f} yesterday",
                    description=f"This tenant's usage cost exceeded the threshold of ₹{cls.HIGH_COST_THRESHOLD_INR}",
                    recommendation="Review usage patterns and consider rate limiting or plan upgrade",
                    data={"cost": total_cost, "threshold": cls.HIGH_COST_THRESHOLD_INR},
                    created_at=datetime.now(timezone.utc),
                )
        except Exception as e:
            print(f"Cost check error: {e}")
        
        return None
    
    @classmethod
    def _check_engagement_drop(cls, tenant_id: str) -> Optional[AIInsight]:
        """Check for significant engagement drop week-over-week"""
        query = f"""
            WITH this_week AS (
                SELECT SUM(chat_messages) as msgs
                FROM `{PROJECT_ID}.{DATASET_ID}.tenant_usage`
                WHERE tenant_id = '{tenant_id}'
                AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
            ),
            last_week AS (
                SELECT SUM(chat_messages) as msgs
                FROM `{PROJECT_ID}.{DATASET_ID}.tenant_usage`
                WHERE tenant_id = '{tenant_id}'
                AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
                AND date < DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
            )
            SELECT 
                this_week.msgs as this_week,
                last_week.msgs as last_week
            FROM this_week, last_week
        """
        
        try:
            result = list(bq.query(query).result())
            if not result:
                return None
            
            this_week = result[0].this_week or 0
            last_week = result[0].last_week or 0
            
            if last_week > 10 and this_week < last_week * 0.5:
                drop_pct = (1 - this_week / last_week) * 100
                return AIInsight(
                    insight_id=f"engagement_drop_{tenant_id}_{date.today().isoformat()}",
                    insight_type=InsightType.ENGAGEMENT_DROP,
                    priority=InsightPriority.MEDIUM,
                    tenant_id=tenant_id,
                    title=f"Week-over-week engagement dropped {drop_pct:.0f}%",
                    description=f"Usage dropped from {last_week} to {this_week} messages",
                    recommendation="Check if tenant is experiencing issues or needs support",
                    data={"this_week": this_week, "last_week": last_week, "drop_pct": drop_pct},
                    created_at=datetime.now(timezone.utc),
                )
        except Exception as e:
            print(f"Engagement check error: {e}")
        
        return None
    
    @classmethod
    def _save_insight(cls, insight: AIInsight):
        """Save insight to database"""
        row = {
            "insight_id": insight.insight_id,
            "insight_type": insight.insight_type.value,
            "priority": insight.priority.value,
            "tenant_id": insight.tenant_id,
            "title": insight.title,
            "description": insight.description,
            "recommendation": insight.recommendation,
            "data": insight.data,
            "created_at": insight.created_at.isoformat(),
            "acknowledged": insight.acknowledged,
            "acknowledged_by": insight.acknowledged_by,
        }
        
        errors = bq.insert_rows_json(cls.INSIGHTS_TABLE, [row])
        if errors:
            print(f"Insight save error: {errors}")
    
    @classmethod
    def get_insights(
        cls,
        tenant_id: Optional[str] = None,
        insight_type: Optional[InsightType] = None,
        priority: Optional[InsightPriority] = None,
        unacknowledged_only: bool = False,
        limit: int = 50,
    ) -> List[AIInsight]:
        """Get AI insights with filters"""
        conditions = []
        
        if tenant_id:
            conditions.append(f"(tenant_id = '{tenant_id}' OR tenant_id IS NULL)")
        
        if insight_type:
            conditions.append(f"insight_type = '{insight_type.value}'")
        
        if priority:
            conditions.append(f"priority = '{priority.value}'")
        
        if unacknowledged_only:
            conditions.append("acknowledged = FALSE")
        
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        query = f"""
            SELECT * FROM `{cls.INSIGHTS_TABLE}`
            {where}
            ORDER BY created_at DESC
            LIMIT {limit}
        """
        
        try:
            results = bq.query(query).result()
            return [
                AIInsight(
                    insight_id=row.insight_id,
                    insight_type=InsightType(row.insight_type),
                    priority=InsightPriority(row.priority),
                    tenant_id=row.tenant_id,
                    title=row.title,
                    description=row.description,
                    recommendation=row.recommendation,
                    data=row.data if isinstance(row.data, dict) else {},
                    created_at=row.created_at,
                    acknowledged=row.acknowledged or False,
                    acknowledged_by=row.acknowledged_by,
                )
                for row in results
            ]
        except Exception as e:
            print(f"Get insights error: {e}")
            return []
    
    @classmethod
    def acknowledge_insight(cls, insight_id: str, admin_id: str) -> bool:
        """Acknowledge an insight"""
        query = f"""
            UPDATE `{cls.INSIGHTS_TABLE}`
            SET acknowledged = TRUE, acknowledged_by = '{admin_id}'
            WHERE insight_id = '{insight_id}'
        """
        
        try:
            bq.query(query).result()
            return True
        except:
            return False
    
    @classmethod
    def get_daily_digest(cls) -> Dict[str, Any]:
        """Generate daily digest for master admin"""
        insights = cls.get_insights(unacknowledged_only=True, limit=100)
        
        # Group by type
        by_type = {}
        for insight in insights:
            t = insight.insight_type.value
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(insight)
        
        # Group by priority
        by_priority = {p.value: 0 for p in InsightPriority}
        for insight in insights:
            by_priority[insight.priority.value] += 1
        
        return {
            "date": date.today().isoformat(),
            "total_insights": len(insights),
            "by_priority": by_priority,
            "by_type": {k: len(v) for k, v in by_type.items()},
            "urgent_items": [
                {"tenant_id": i.tenant_id, "title": i.title, "type": i.insight_type.value}
                for i in insights if i.priority == InsightPriority.URGENT
            ],
            "high_priority_items": [
                {"tenant_id": i.tenant_id, "title": i.title, "type": i.insight_type.value}
                for i in insights if i.priority == InsightPriority.HIGH
            ][:10],
        }
