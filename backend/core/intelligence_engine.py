"""
TITAN Intelligence Engine
=========================
Unified AI orchestration layer that connects all modules:
- Semantic Brain (classification, entity extraction)
- Metacognitive Learning (patterns, strategies)
- AI Watchdog (anomalies, predictions)
- Optimized Prompts (response formatting)
- Real-time Data Pipeline (context injection)

This is the central nervous system of TITAN ERP.
"""

import json
import os
import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError


# ============ Configuration ============

PROJECT_ID = "cafe-mellow-core-2026"
DATASET_ID = "cafe_operations"


def _get_bq_client() -> Tuple[Optional[bigquery.Client], Optional[Exception]]:
    try:
        key_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "service-key.json")
        )
        if os.path.exists(key_path):
            return bigquery.Client.from_service_account_json(key_path), None
        return bigquery.Client(project=PROJECT_ID), None
    except DefaultCredentialsError as e:
        return None, e
    except Exception as e:
        return None, e


# ============ Enums ============

class QueryIntent(str, Enum):
    REVENUE = "revenue"
    EXPENSE = "expense"
    PROFIT = "profit"
    INVENTORY = "inventory"
    COMPARISON = "comparison"
    FORECAST = "forecast"
    ANOMALY = "anomaly"
    STAFF = "staff"
    BRIEF = "brief"
    TASK = "task"
    GENERAL = "general"


class ResponseType(str, Enum):
    KPI_CARD = "kpi_card"
    TABLE = "table"
    CHART = "chart"
    ALERT = "alert"
    TASK_LIST = "task_list"
    NARRATIVE = "narrative"
    MIXED = "mixed"


# ============ Data Classes ============

@dataclass
class BusinessMetrics:
    """Real-time business metrics for context injection"""
    timestamp: datetime
    tenant_id: str
    
    # Revenue metrics
    revenue_today: float = 0
    revenue_7d: float = 0
    revenue_30d: float = 0
    revenue_change_7d: float = 0
    orders_today: int = 0
    orders_7d: int = 0
    avg_order_value: float = 0
    
    # Expense metrics
    expenses_today: float = 0
    expenses_7d: float = 0
    expenses_30d: float = 0
    expense_change_7d: float = 0
    
    # Profit metrics
    profit_7d: float = 0
    profit_margin_7d: float = 0
    
    # Inventory
    low_stock_items: int = 0
    total_inventory_value: float = 0
    
    # Operations
    pending_tasks: int = 0
    active_alerts: int = 0
    
    # Top performers
    top_items: List[Dict[str, Any]] = field(default_factory=list)
    top_expense_categories: List[Dict[str, Any]] = field(default_factory=list)


@dataclass 
class IntelligenceContext:
    """Full context for AI responses"""
    metrics: BusinessMetrics
    recent_patterns: List[Dict[str, Any]]
    learned_rules: List[Dict[str, Any]]
    active_alerts: List[Dict[str, Any]]
    conversation_summary: str
    query_intent: QueryIntent
    suggested_response_type: ResponseType


@dataclass
class AIResponse:
    """Structured AI response"""
    content: str
    response_type: ResponseType
    data: Dict[str, Any]
    tasks_extracted: List[Dict[str, Any]]
    confidence: float
    processing_time_ms: int
    context_used: List[str]


# ============ Intelligence Engine ============

class TitanIntelligenceEngine:
    """
    Central intelligence orchestrator for TITAN ERP
    
    Responsibilities:
    1. Query understanding and intent classification
    2. Real-time context gathering
    3. Pattern and rule retrieval
    4. Response optimization
    5. Learning from interactions
    """
    
    def __init__(self, tenant_id: str = "cafe_mellow_001"):
        self.tenant_id = tenant_id
        self.bq, self._bq_init_error = _get_bq_client()
        self._metrics_cache: Dict[str, Tuple[BusinessMetrics, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)
    
    # ============ Query Intent Classification ============
    
    def classify_intent(self, query: str) -> QueryIntent:
        """Classify user query intent for targeted response"""
        query_lower = query.lower()
        
        intent_patterns = {
            QueryIntent.REVENUE: [
                "revenue", "sales", "income", "earnings", "turnover",
                "how much did we make", "total sales", "money coming in"
            ],
            QueryIntent.EXPENSE: [
                "expense", "cost", "spending", "outflow", "purchases",
                "how much did we spend", "where is money going"
            ],
            QueryIntent.PROFIT: [
                "profit", "margin", "bottom line", "net income", "p&l",
                "are we making money", "profit and loss"
            ],
            QueryIntent.INVENTORY: [
                "inventory", "stock", "supplies", "ingredients", "raw material",
                "what do we have", "low stock", "negative"
            ],
            QueryIntent.COMPARISON: [
                "compare", "versus", "vs", "difference", "change",
                "better or worse", "improved", "declined", "last week"
            ],
            QueryIntent.FORECAST: [
                "forecast", "predict", "projection", "estimate", "expect",
                "what will", "next week", "next month"
            ],
            QueryIntent.ANOMALY: [
                "anomaly", "unusual", "strange", "wrong", "issue", "problem",
                "what's wrong", "investigate"
            ],
            QueryIntent.STAFF: [
                "staff", "employee", "team", "performance", "attendance",
                "who is performing", "labor"
            ],
            QueryIntent.BRIEF: [
                "brief", "summary", "overview", "update", "status",
                "what's happening", "how are we doing", "today"
            ],
            QueryIntent.TASK: [
                "task", "action", "todo", "pending", "assign",
                "what needs to be done"
            ],
        }
        
        scores = {}
        for intent, keywords in intent_patterns.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[intent] = score
        
        if not scores:
            return QueryIntent.GENERAL
        
        return max(scores, key=scores.get)
    
    # ============ Real-time Metrics ============
    
    async def get_business_metrics(self, force_refresh: bool = False) -> BusinessMetrics:
        """Get real-time business metrics with caching"""
        cache_key = self.tenant_id
        
        # Check cache
        if not force_refresh and cache_key in self._metrics_cache:
            cached, cached_at = self._metrics_cache[cache_key]
            if datetime.now() - cached_at < self._cache_ttl:
                return cached
        
        metrics = BusinessMetrics(
            timestamp=datetime.now(),
            tenant_id=self.tenant_id
        )
        
        if not self.bq:
            return metrics
        
        try:
            # Parallel queries for performance
            await asyncio.gather(
                self._fetch_revenue_metrics(metrics),
                self._fetch_expense_metrics(metrics),
                self._fetch_inventory_metrics(metrics),
                self._fetch_operations_metrics(metrics),
            )
            
            # Calculate derived metrics
            metrics.profit_7d = metrics.revenue_7d - metrics.expenses_7d
            metrics.profit_margin_7d = (
                (metrics.profit_7d / metrics.revenue_7d * 100) 
                if metrics.revenue_7d > 0 else 0
            )
            
            # Cache results
            self._metrics_cache[cache_key] = (metrics, datetime.now())
            
        except Exception as e:
            print(f"Metrics fetch error: {e}")
        
        return metrics
    
    async def _fetch_revenue_metrics(self, metrics: BusinessMetrics):
        """Fetch revenue-related metrics"""
        try:
            query = f"""
                WITH daily_sales AS (
                    SELECT 
                        DATE(created_at) as sale_date,
                        COUNT(*) as orders,
                        SUM(CAST(JSON_EXTRACT_SCALAR(payload, '$.total') AS FLOAT64)) as revenue
                    FROM `{PROJECT_ID}.{DATASET_ID}.sales_raw`
                    WHERE tenant_id = '{self.tenant_id}'
                    AND DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                    GROUP BY DATE(created_at)
                )
                SELECT 
                    SUM(CASE WHEN sale_date = CURRENT_DATE() THEN revenue ELSE 0 END) as revenue_today,
                    SUM(CASE WHEN sale_date = CURRENT_DATE() THEN orders ELSE 0 END) as orders_today,
                    SUM(CASE WHEN sale_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) THEN revenue ELSE 0 END) as revenue_7d,
                    SUM(CASE WHEN sale_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) THEN orders ELSE 0 END) as orders_7d,
                    SUM(CASE WHEN sale_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY) 
                        AND sale_date < DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) THEN revenue ELSE 0 END) as revenue_prev_7d,
                    SUM(revenue) as revenue_30d
                FROM daily_sales
            """
            result = list(self.bq.query(query).result())
            if result:
                row = result[0]
                metrics.revenue_today = float(row.revenue_today or 0)
                metrics.revenue_7d = float(row.revenue_7d or 0)
                metrics.revenue_30d = float(row.revenue_30d or 0)
                metrics.orders_today = int(row.orders_today or 0)
                metrics.orders_7d = int(row.orders_7d or 0)
                
                prev_7d = float(row.revenue_prev_7d or 0)
                if prev_7d > 0:
                    metrics.revenue_change_7d = ((metrics.revenue_7d - prev_7d) / prev_7d) * 100
                
                if metrics.orders_7d > 0:
                    metrics.avg_order_value = metrics.revenue_7d / metrics.orders_7d
            
            # Top items
            top_query = f"""
                SELECT 
                    JSON_EXTRACT_SCALAR(payload, '$.item_name') as item,
                    COUNT(*) as orders,
                    SUM(CAST(JSON_EXTRACT_SCALAR(payload, '$.total') AS FLOAT64)) as revenue
                FROM `{PROJECT_ID}.{DATASET_ID}.sales_raw`
                WHERE tenant_id = '{self.tenant_id}'
                AND DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                GROUP BY item
                ORDER BY revenue DESC
                LIMIT 5
            """
            top_result = self.bq.query(top_query).result()
            metrics.top_items = [
                {"item": row.item, "orders": row.orders, "revenue": float(row.revenue or 0)}
                for row in top_result
            ]
            
        except Exception as e:
            print(f"Revenue metrics error: {e}")
    
    async def _fetch_expense_metrics(self, metrics: BusinessMetrics):
        """Fetch expense-related metrics"""
        try:
            query = f"""
                SELECT 
                    SUM(CASE WHEN DATE(expense_date) = CURRENT_DATE() THEN CAST(amount AS FLOAT64) ELSE 0 END) as expenses_today,
                    SUM(CASE WHEN DATE(expense_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) THEN CAST(amount AS FLOAT64) ELSE 0 END) as expenses_7d,
                    SUM(CASE WHEN DATE(expense_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY) 
                        AND DATE(expense_date) < DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) THEN CAST(amount AS FLOAT64) ELSE 0 END) as expenses_prev_7d,
                    SUM(CAST(amount AS FLOAT64)) as expenses_30d
                FROM `{PROJECT_ID}.{DATASET_ID}.expenses`
                WHERE tenant_id = '{self.tenant_id}'
                AND DATE(expense_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            """
            result = list(self.bq.query(query).result())
            if result:
                row = result[0]
                metrics.expenses_today = float(row.expenses_today or 0)
                metrics.expenses_7d = float(row.expenses_7d or 0)
                metrics.expenses_30d = float(row.expenses_30d or 0)
                
                prev_7d = float(row.expenses_prev_7d or 0)
                if prev_7d > 0:
                    metrics.expense_change_7d = ((metrics.expenses_7d - prev_7d) / prev_7d) * 100
            
            # Top expense categories
            cat_query = f"""
                SELECT 
                    category,
                    SUM(CAST(amount AS FLOAT64)) as total
                FROM `{PROJECT_ID}.{DATASET_ID}.expenses`
                WHERE tenant_id = '{self.tenant_id}'
                AND DATE(expense_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                GROUP BY category
                ORDER BY total DESC
                LIMIT 5
            """
            cat_result = self.bq.query(cat_query).result()
            metrics.top_expense_categories = [
                {"category": row.category or "Uncategorized", "total": float(row.total or 0)}
                for row in cat_result
            ]
            
        except Exception as e:
            print(f"Expense metrics error: {e}")
    
    async def _fetch_inventory_metrics(self, metrics: BusinessMetrics):
        """Fetch inventory-related metrics"""
        try:
            query = f"""
                SELECT 
                    COUNT(CASE WHEN CAST(quantity AS FLOAT64) < CAST(reorder_level AS FLOAT64) THEN 1 END) as low_stock,
                    SUM(CAST(quantity AS FLOAT64) * CAST(unit_cost AS FLOAT64)) as total_value
                FROM `{PROJECT_ID}.{DATASET_ID}.inventory`
                WHERE tenant_id = '{self.tenant_id}'
            """
            result = list(self.bq.query(query).result())
            if result:
                row = result[0]
                metrics.low_stock_items = int(row.low_stock or 0)
                metrics.total_inventory_value = float(row.total_value or 0)
        except Exception as e:
            print(f"Inventory metrics error: {e}")
    
    async def _fetch_operations_metrics(self, metrics: BusinessMetrics):
        """Fetch operations-related metrics"""
        try:
            # Pending tasks
            tasks_query = f"""
                SELECT COUNT(*) as count
                FROM `{PROJECT_ID}.{DATASET_ID}.ai_task_queue`
                WHERE tenant_id = '{self.tenant_id}'
                AND status = 'Pending'
            """
            tasks_result = list(self.bq.query(tasks_query).result())
            if tasks_result:
                metrics.pending_tasks = int(tasks_result[0].count or 0)
            
        except Exception as e:
            print(f"Operations metrics error: {e}")
    
    # ============ Pattern & Rule Retrieval ============
    
    async def get_learned_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get learned patterns and rules for the tenant"""
        if not self.bq:
            return []
        try:
            query = f"""
                SELECT 
                    rule_type,
                    description,
                    confidence_score,
                    usage_count
                FROM `{PROJECT_ID}.{DATASET_ID}.system_knowledge_base`
                WHERE org_id = '{self.tenant_id}'
                AND status = 'active'
                ORDER BY confidence_score DESC, usage_count DESC
                LIMIT {limit}
            """
            result = self.bq.query(query).result()
            return [dict(row) for row in result]
        except Exception:
            return []
    
    async def get_active_alerts(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get active alerts for the tenant"""
        if not self.bq:
            return []
        try:
            query = f"""
                SELECT 
                    task_type,
                    description,
                    priority,
                    created_at
                FROM `{PROJECT_ID}.{DATASET_ID}.ai_task_queue`
                WHERE tenant_id = '{self.tenant_id}'
                AND status = 'Pending'
                AND priority IN ('Critical', 'High')
                ORDER BY 
                    CASE priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 ELSE 3 END,
                    created_at DESC
                LIMIT {limit}
            """
            result = self.bq.query(query).result()
            return [dict(row) for row in result]
        except Exception:
            return []
    
    # ============ Context Building ============
    
    async def build_context(self, query: str) -> IntelligenceContext:
        """Build full intelligence context for AI response"""
        start_time = datetime.now()
        
        # Parallel context gathering
        metrics_task = self.get_business_metrics()
        patterns_task = self.get_learned_patterns()
        alerts_task = self.get_active_alerts()
        
        metrics, patterns, alerts = await asyncio.gather(
            metrics_task, patterns_task, alerts_task
        )
        
        # Classify intent
        intent = self.classify_intent(query)
        
        # Determine suggested response type
        response_type = self._suggest_response_type(intent)
        
        return IntelligenceContext(
            metrics=metrics,
            recent_patterns=patterns,
            learned_rules=[],  # Could add business rules
            active_alerts=alerts,
            conversation_summary="",  # Could add conversation history summary
            query_intent=intent,
            suggested_response_type=response_type
        )
    
    def _suggest_response_type(self, intent: QueryIntent) -> ResponseType:
        """Suggest optimal response type based on intent"""
        type_mapping = {
            QueryIntent.REVENUE: ResponseType.KPI_CARD,
            QueryIntent.EXPENSE: ResponseType.TABLE,
            QueryIntent.PROFIT: ResponseType.KPI_CARD,
            QueryIntent.INVENTORY: ResponseType.TABLE,
            QueryIntent.COMPARISON: ResponseType.CHART,
            QueryIntent.FORECAST: ResponseType.CHART,
            QueryIntent.ANOMALY: ResponseType.ALERT,
            QueryIntent.STAFF: ResponseType.TABLE,
            QueryIntent.BRIEF: ResponseType.MIXED,
            QueryIntent.TASK: ResponseType.TASK_LIST,
            QueryIntent.GENERAL: ResponseType.NARRATIVE,
        }
        return type_mapping.get(intent, ResponseType.NARRATIVE)
    
    # ============ Prompt Building ============
    
    def build_optimized_prompt(self, query: str, context: IntelligenceContext) -> str:
        """Build optimized prompt with full context injection"""
        metrics = context.metrics
        
        # Format top items
        top_items_str = "\n".join([
            f"  - {item['item']}: ₹{item['revenue']:,.0f} ({item['orders']} orders)"
            for item in metrics.top_items[:5]
        ]) or "  - No data"
        
        # Format expense categories
        expense_str = "\n".join([
            f"  - {cat['category']}: ₹{cat['total']:,.0f}"
            for cat in metrics.top_expense_categories[:5]
        ]) or "  - No data"
        
        # Format alerts
        alerts_str = "\n".join([
            f"  - [{a.get('priority', 'Medium')}] {a.get('description', 'Unknown')}"
            for a in context.active_alerts[:3]
        ]) or "  - None"
        
        # Format patterns
        patterns_str = "\n".join([
            f"  - {p.get('description', '')}"
            for p in context.recent_patterns[:3]
        ]) or "  - No learned patterns yet"
        
        context_block = f"""
## CURRENT BUSINESS STATE (as of {metrics.timestamp.strftime('%Y-%m-%d %H:%M')})

### Revenue Performance
- Today: ₹{metrics.revenue_today:,.0f}
- Last 7 days: ₹{metrics.revenue_7d:,.0f} ({metrics.revenue_change_7d:+.1f}% vs previous week)
- Orders (7d): {metrics.orders_7d:,}
- Avg Order Value: ₹{metrics.avg_order_value:,.0f}

### Top Revenue Items (7d)
{top_items_str}

### Expense Summary
- Today: ₹{metrics.expenses_today:,.0f}
- Last 7 days: ₹{metrics.expenses_7d:,.0f} ({metrics.expense_change_7d:+.1f}%)
- Top Categories:
{expense_str}

### Profit Analysis (7d)
- Net Profit: ₹{metrics.profit_7d:,.0f}
- Margin: {metrics.profit_margin_7d:.1f}%

### Operations Status
- Pending Tasks: {metrics.pending_tasks}
- Low Stock Items: {metrics.low_stock_items}
- Inventory Value: ₹{metrics.total_inventory_value:,.0f}

### Active Alerts
{alerts_str}

### Learned Patterns
{patterns_str}

---
QUERY INTENT: {context.query_intent.value}
SUGGESTED RESPONSE FORMAT: {context.suggested_response_type.value}
---

USER QUERY: {query}
"""
        return context_block
    
    # ============ Learning ============
    
    async def learn_from_interaction(
        self, 
        query: str, 
        response: str, 
        feedback: Optional[str] = None
    ):
        """Learn from user interactions"""
        if not self.bq:
            return
        try:
            # Extract patterns from successful interactions
            interaction_hash = hashlib.md5(f"{query}:{response}".encode()).hexdigest()[:16]
            
            # Store interaction for analysis
            row = {
                "interaction_id": f"{self.tenant_id}_{interaction_hash}",
                "tenant_id": self.tenant_id,
                "query": query[:1000],
                "response_summary": response[:500],
                "query_intent": self.classify_intent(query).value,
                "feedback": feedback,
                "timestamp": datetime.now().isoformat(),
            }
            
            table_id = f"{PROJECT_ID}.{DATASET_ID}.ai_interactions"
            errors = self.bq.insert_rows_json(table_id, [row])
            
            if errors:
                print(f"Learning storage error: {errors}")
                
        except Exception as e:
            print(f"Learning error: {e}")
    
    # ============ Anomaly Detection ============
    
    async def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies in business data"""
        anomalies = []
        metrics = await self.get_business_metrics()
        
        # Revenue anomaly (significant drop)
        if metrics.revenue_change_7d < -20:
            anomalies.append({
                "type": "revenue_drop",
                "severity": "high",
                "message": f"Revenue dropped {abs(metrics.revenue_change_7d):.1f}% vs last week",
                "value": metrics.revenue_7d,
                "change": metrics.revenue_change_7d,
            })
        
        # Expense anomaly (significant increase)
        if metrics.expense_change_7d > 30:
            anomalies.append({
                "type": "expense_spike",
                "severity": "medium",
                "message": f"Expenses increased {metrics.expense_change_7d:.1f}% vs last week",
                "value": metrics.expenses_7d,
                "change": metrics.expense_change_7d,
            })
        
        # Low margin warning
        if metrics.profit_margin_7d < 10 and metrics.revenue_7d > 0:
            anomalies.append({
                "type": "low_margin",
                "severity": "high",
                "message": f"Profit margin is only {metrics.profit_margin_7d:.1f}%",
                "value": metrics.profit_7d,
                "margin": metrics.profit_margin_7d,
            })
        
        # Low stock alert
        if metrics.low_stock_items > 5:
            anomalies.append({
                "type": "low_stock",
                "severity": "medium",
                "message": f"{metrics.low_stock_items} items below reorder level",
                "count": metrics.low_stock_items,
            })
        
        return anomalies
    
    # ============ Health Check ============
    
    async def health_check(self) -> Dict[str, Any]:
        """Check intelligence engine health"""
        if not self.bq:
            bq_status = "not_configured"
        else:
            try:
                # Test BigQuery connection
                self.bq.query("SELECT 1").result()
                bq_status = "healthy"
            except Exception as e:
                bq_status = f"error: {str(e)[:50]}"
         
        return {
            "status": "healthy" if bq_status == "healthy" else "degraded",
            "tenant_id": self.tenant_id,
            "bigquery": bq_status,
            "cache_size": len(self._metrics_cache),
            "timestamp": datetime.now().isoformat(),
        }


# ============ Singleton Instance ============

_engine_instances: Dict[str, TitanIntelligenceEngine] = {}

def get_intelligence_engine(tenant_id: str = "cafe_mellow_001") -> TitanIntelligenceEngine:
    """Get or create intelligence engine for tenant"""
    if tenant_id not in _engine_instances:
        _engine_instances[tenant_id] = TitanIntelligenceEngine(tenant_id)
    return _engine_instances[tenant_id]


# ============ Convenience Functions ============

async def process_query(query: str, tenant_id: str = "cafe_mellow_001") -> Dict[str, Any]:
    """
    Main entry point for processing user queries
    
    Returns structured response with:
    - content: AI response text
    - context: Business metrics used
    - intent: Detected query intent
    - suggested_visuals: Recommended visualizations
    """
    engine = get_intelligence_engine(tenant_id)
    
    # Build context
    context = await engine.build_context(query)
    
    # Build optimized prompt
    prompt = engine.build_optimized_prompt(query, context)
    
    return {
        "prompt": prompt,
        "intent": context.query_intent.value,
        "response_type": context.suggested_response_type.value,
        "metrics": {
            "revenue_7d": context.metrics.revenue_7d,
            "expenses_7d": context.metrics.expenses_7d,
            "profit_7d": context.metrics.profit_7d,
            "orders_7d": context.metrics.orders_7d,
        },
        "alerts": context.active_alerts,
        "timestamp": datetime.now().isoformat(),
    }
