"""
TITAN Data Intelligence Layer
==============================
Queries actual BigQuery data based on user intent.
This is the CRITICAL missing piece - the AI needs REAL numbers.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class QueryIntent(Enum):
    PROFIT = "profit"
    REVENUE = "revenue"
    EXPENSES = "expenses"
    SALES = "sales"
    TOP_ITEMS = "top_items"
    TRENDS = "trends"
    COMPARISON = "comparison"
    STAFF = "staff"
    INVENTORY = "inventory"
    PROFIT_LEAKS = "profit_leaks"
    PERFORMANCE = "performance"
    UNKNOWN = "unknown"


@dataclass
class DataContext:
    """Container for actual business data to inject into AI prompt"""
    intent: QueryIntent
    time_period: str
    data: Dict[str, Any]
    summary: str
    raw_numbers: Dict[str, float]
    has_zero_data: bool = False
    system_hint: Optional[str] = None
    visual_data: Optional[Dict[str, Any]] = None


class DataIntelligence:
    """
    Smart data fetcher that understands user intent and queries relevant data.
    This is what makes TITAN CFO actually useful.
    """
    
    def __init__(self, client, settings):
        self.client = client
        self.settings = settings
        self.project_id = getattr(settings, 'PROJECT_ID', '')
        self.dataset_id = getattr(settings, 'DATASET_ID', '')
    
    def detect_intent(self, message: str) -> Tuple[QueryIntent, str]:
        """Detect user's data intent and time period"""
        msg = message.lower()
        
        # Time period detection
        time_period = "last_7_days"
        if "today" in msg:
            time_period = "today"
        elif "yesterday" in msg:
            time_period = "yesterday"
        elif "this week" in msg:
            time_period = "this_week"
        elif "last week" in msg:
            time_period = "last_week"
        elif "this month" in msg:
            time_period = "this_month"
        elif "last month" in msg:
            time_period = "last_month"
        elif "this year" in msg:
            time_period = "this_year"
        elif any(x in msg for x in ["7 day", "week", "weekly"]):
            time_period = "last_7_days"
        elif any(x in msg for x in ["30 day", "month", "monthly"]):
            time_period = "last_30_days"
        
        # Intent detection - order matters (more specific first)
        if any(x in msg for x in ["profit leak", "leaking", "losing money", "waste", "wastage"]):
            return QueryIntent.PROFIT_LEAKS, time_period
        elif any(x in msg for x in ["staff performance", "employee", "team performance"]):
            return QueryIntent.STAFF, time_period
        elif any(x in msg for x in ["top item", "best seller", "top selling", "popular"]):
            return QueryIntent.TOP_ITEMS, time_period
        elif any(x in msg for x in ["trend", "growth", "compare", "vs", "versus"]):
            return QueryIntent.TRENDS, time_period
        elif any(x in msg for x in ["profit", "margin", "net", "bottom line"]):
            return QueryIntent.PROFIT, time_period
        elif any(x in msg for x in ["revenue", "sales", "income", "earning"]):
            return QueryIntent.REVENUE, time_period
        elif any(x in msg for x in ["expense", "cost", "spending", "spend"]):
            return QueryIntent.EXPENSES, time_period
        elif any(x in msg for x in ["inventory", "stock", "item"]):
            return QueryIntent.INVENTORY, time_period
        elif any(x in msg for x in ["scan", "overview", "summary", "brief", "status"]):
            return QueryIntent.PROFIT, time_period  # Default to profit for overview
        
        return QueryIntent.UNKNOWN, time_period
    
    def _get_date_filter(self, time_period: str) -> Tuple[str, str, str]:
        """Get SQL date filter and human-readable label"""
        today = datetime.now().date()
        
        filters = {
            "today": (
                f"DATE(bill_date) = '{today}'",
                f"DATE(expense_date) = '{today}'",
                "Today"
            ),
            "yesterday": (
                f"DATE(bill_date) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)",
                f"DATE(expense_date) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)",
                "Yesterday"
            ),
            "this_week": (
                "DATE(bill_date) >= DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY))",
                "DATE(expense_date) >= DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY))",
                "This Week"
            ),
            "last_week": (
                "DATE(bill_date) >= DATE_SUB(DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY)), INTERVAL 7 DAY) AND DATE(bill_date) < DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY))",
                "DATE(expense_date) >= DATE_SUB(DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY)), INTERVAL 7 DAY) AND DATE(expense_date) < DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY))",
                "Last Week"
            ),
            "this_month": (
                "DATE(bill_date) >= DATE_TRUNC(CURRENT_DATE(), MONTH)",
                "DATE(expense_date) >= DATE_TRUNC(CURRENT_DATE(), MONTH)",
                "This Month"
            ),
            "last_month": (
                "DATE(bill_date) >= DATE_SUB(DATE_TRUNC(CURRENT_DATE(), MONTH), INTERVAL 1 MONTH) AND DATE(bill_date) < DATE_TRUNC(CURRENT_DATE(), MONTH)",
                "DATE(expense_date) >= DATE_SUB(DATE_TRUNC(CURRENT_DATE(), MONTH), INTERVAL 1 MONTH) AND DATE(expense_date) < DATE_TRUNC(CURRENT_DATE(), MONTH)",
                "Last Month"
            ),
            "last_7_days": (
                "DATE(bill_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)",
                "DATE(expense_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)",
                "Last 7 Days"
            ),
            "last_30_days": (
                "DATE(bill_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)",
                "DATE(expense_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)",
                "Last 30 Days"
            ),
            "this_year": (
                "DATE(bill_date) >= DATE_TRUNC(CURRENT_DATE(), YEAR)",
                "DATE(expense_date) >= DATE_TRUNC(CURRENT_DATE(), YEAR)",
                "This Year"
            ),
        }
        
        return filters.get(time_period, filters["last_7_days"])
    
    def _safe_query(self, sql: str) -> Optional[Any]:
        """Execute query safely, return None on error"""
        try:
            return self.client.query(sql).to_dataframe()
        except Exception as e:
            print(f"Query error: {e}")
            return None
    
    def fetch_profit_data(self, time_period: str) -> DataContext:
        """Fetch actual profit data (Revenue - Expenses)"""
        sales_filter, expense_filter, label = self._get_date_filter(time_period)
        
        # Get revenue
        revenue_sql = f"""
        SELECT 
            COALESCE(SUM(total_revenue), 0) as total_revenue,
            COUNT(DISTINCT bill_no) as order_count,
            COUNT(DISTINCT DATE(bill_date)) as days_count
        FROM `{self.project_id}.{self.dataset_id}.sales_items_parsed`
        WHERE {sales_filter}
        """
        
        # Get expenses
        expense_sql = f"""
        SELECT 
            COALESCE(SUM(amount), 0) as total_expenses,
            COUNT(*) as expense_count
        FROM `{self.project_id}.{self.dataset_id}.expenses_master`
        WHERE {expense_filter}
        """
        
        rev_df = self._safe_query(revenue_sql)
        exp_df = self._safe_query(expense_sql)
        
        revenue = float(rev_df.iloc[0]['total_revenue']) if rev_df is not None and not rev_df.empty else 0
        orders = int(rev_df.iloc[0]['order_count']) if rev_df is not None and not rev_df.empty else 0
        days = int(rev_df.iloc[0]['days_count']) if rev_df is not None and not rev_df.empty else 1
        expenses = float(exp_df.iloc[0]['total_expenses']) if exp_df is not None and not exp_df.empty else 0
        expense_count = int(exp_df.iloc[0]['expense_count']) if exp_df is not None and not exp_df.empty else 0
        
        profit = revenue - expenses
        margin = (profit / revenue * 100) if revenue > 0 else 0
        avg_daily_revenue = revenue / max(days, 1)
        avg_order_value = revenue / max(orders, 1)
        
        # Detect zero data scenario
        has_zero_data = revenue == 0 and orders == 0
        system_hint = None
        
        if has_zero_data:
            system_hint = "[SYSTEM_NOTE: Zero revenue detected. This indicates a POS sync issue or data pipeline failure. Guide user to check technical systems, not business strategy.]"
            summary = f"""## {label} FINANCIAL DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ **DATA SYNC ALERT**
**REVENUE:** ₹0.00 (No sales data found)
**EXPENSES:** ₹{expenses:,.2f}
**Orders:** 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 **Likely Issue:** POS system not syncing or data pipeline offline
"""
        else:
            summary = f"""## {label} FINANCIAL DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**REVENUE:** ₹{revenue:,.2f}
**EXPENSES:** ₹{expenses:,.2f}
**NET PROFIT:** ₹{profit:,.2f}
**PROFIT MARGIN:** {margin:.1f}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Orders:** {orders}
**Avg Order Value:** ₹{avg_order_value:,.2f}
**Avg Daily Revenue:** ₹{avg_daily_revenue:,.2f}
**Expense Items:** {expense_count}
"""
        
        # Prepare visual data for charts
        visual_data = {
            "kpi_cards": [
                {"label": "Revenue", "value": revenue, "format": "currency"},
                {"label": "Expenses", "value": expenses, "format": "currency"},
                {"label": "Net Profit", "value": profit, "format": "currency"},
                {"label": "Margin", "value": margin, "format": "percentage"}
            ],
            "chart_type": "bar",
            "chart_data": [
                {"name": "Revenue", "value": revenue, "color": "#10b981"},
                {"name": "Expenses", "value": expenses, "color": "#ef4444"},
                {"name": "Profit", "value": profit, "color": "#3b82f6"}
            ]
        }
        
        return DataContext(
            intent=QueryIntent.PROFIT,
            time_period=label,
            data={
                "revenue": revenue,
                "expenses": expenses,
                "profit": profit,
                "margin": margin,
                "orders": orders,
                "avg_order_value": avg_order_value,
                "days": days
            },
            summary=summary,
            raw_numbers={"revenue": revenue, "expenses": expenses, "profit": profit, "margin": margin},
            has_zero_data=has_zero_data,
            system_hint=system_hint,
            visual_data=visual_data
        )
    
    def fetch_expense_breakdown(self, time_period: str) -> DataContext:
        """Fetch expense breakdown by category"""
        _, expense_filter, label = self._get_date_filter(time_period)
        
        breakdown_sql = f"""
        SELECT 
            COALESCE(category, 'Uncategorized') as category,
            SUM(amount) as total,
            COUNT(*) as count
        FROM `{self.project_id}.{self.dataset_id}.expenses_master`
        WHERE {expense_filter}
        GROUP BY category
        ORDER BY total DESC
        LIMIT 10
        """
        
        total_sql = f"""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM `{self.project_id}.{self.dataset_id}.expenses_master`
        WHERE {expense_filter}
        """
        
        breakdown_df = self._safe_query(breakdown_sql)
        total_df = self._safe_query(total_sql)
        
        total_expenses = float(total_df.iloc[0]['total']) if total_df is not None and not total_df.empty else 0
        
        summary = f"""## {label} EXPENSE BREAKDOWN (ACTUAL NUMBERS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**TOTAL EXPENSES:** ₹{total_expenses:,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        categories = {}
        if breakdown_df is not None and not breakdown_df.empty:
            for _, row in breakdown_df.iterrows():
                cat = row['category']
                amt = float(row['total'])
                cnt = int(row['count'])
                pct = (amt / total_expenses * 100) if total_expenses > 0 else 0
                summary += f"• **{cat}:** ₹{amt:,.2f} ({pct:.1f}%) - {cnt} items\n"
                categories[cat] = amt
        else:
            summary += "No expense data available for this period.\n"
        
        return DataContext(
            intent=QueryIntent.EXPENSES,
            time_period=label,
            data={"total": total_expenses, "categories": categories},
            summary=summary,
            raw_numbers={"total_expenses": total_expenses, **categories}
        )
    
    def fetch_top_items(self, time_period: str) -> DataContext:
        """Fetch top selling items"""
        sales_filter, _, label = self._get_date_filter(time_period)
        
        top_items_sql = f"""
        SELECT 
            item_name,
            SUM(quantity) as total_qty,
            SUM(total_revenue) as total_revenue,
            COUNT(DISTINCT bill_no) as order_count
        FROM `{self.project_id}.{self.dataset_id}.sales_items_parsed`
        WHERE {sales_filter}
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 10
        """
        
        df = self._safe_query(top_items_sql)
        
        summary = f"""## {label} TOP SELLING ITEMS (ACTUAL NUMBERS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        items = []
        if df is not None and not df.empty:
            for i, row in df.iterrows():
                name = row['item_name']
                qty = int(row['total_qty'])
                rev = float(row['total_revenue'])
                orders = int(row['order_count'])
                summary += f"{i+1}. **{name}:** ₹{rev:,.2f} ({qty} sold, {orders} orders)\n"
                items.append({"name": name, "quantity": qty, "revenue": rev})
        else:
            summary += "No sales data available for this period.\n"
        
        return DataContext(
            intent=QueryIntent.TOP_ITEMS,
            time_period=label,
            data={"items": items},
            summary=summary,
            raw_numbers={item["name"]: item["revenue"] for item in items[:5]}
        )
    
    def fetch_profit_leaks(self, time_period: str) -> DataContext:
        """Analyze potential profit leaks"""
        sales_filter, expense_filter, label = self._get_date_filter(time_period)
        
        # Get profit data first
        profit_ctx = self.fetch_profit_data(time_period)
        
        # High expense categories
        high_expense_sql = f"""
        SELECT 
            category,
            SUM(amount) as total,
            COUNT(*) as count
        FROM `{self.project_id}.{self.dataset_id}.expenses_master`
        WHERE {expense_filter}
        GROUP BY category
        ORDER BY total DESC
        LIMIT 5
        """
        
        # Low margin items (if we have cost data)
        # For now, just identify items with high quantity but low revenue
        low_margin_sql = f"""
        SELECT 
            item_name,
            SUM(quantity) as qty,
            SUM(total_revenue) as revenue,
            SAFE_DIVIDE(SUM(total_revenue), SUM(quantity)) as avg_price
        FROM `{self.project_id}.{self.dataset_id}.sales_items_parsed`
        WHERE {sales_filter}
        GROUP BY item_name
        HAVING qty > 10
        ORDER BY avg_price ASC
        LIMIT 5
        """
        
        expenses_df = self._safe_query(high_expense_sql)
        low_margin_df = self._safe_query(low_margin_sql)
        
        summary = f"""## {label} PROFIT LEAK ANALYSIS (ACTUAL NUMBERS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**Current Status:**
• Revenue: ₹{profit_ctx.data['revenue']:,.2f}
• Expenses: ₹{profit_ctx.data['expenses']:,.2f}
• Net Profit: ₹{profit_ctx.data['profit']:,.2f}
• Margin: {profit_ctx.data['margin']:.1f}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**TOP EXPENSE CATEGORIES (Potential Leaks):**
"""
        
        if expenses_df is not None and not expenses_df.empty:
            total_exp = profit_ctx.data['expenses']
            for _, row in expenses_df.iterrows():
                cat = row['category']
                amt = float(row['total'])
                pct = (amt / total_exp * 100) if total_exp > 0 else 0
                summary += f"• {cat}: ₹{amt:,.2f} ({pct:.1f}% of expenses)\n"
        
        summary += "\n**LOW-MARGIN ITEMS (Volume vs Value):**\n"
        if low_margin_df is not None and not low_margin_df.empty:
            for _, row in low_margin_df.iterrows():
                name = row['item_name']
                qty = int(row['qty'])
                rev = float(row['revenue'])
                avg = float(row['avg_price'])
                summary += f"• {name}: {qty} sold @ ₹{avg:.2f} avg (₹{rev:,.2f} total)\n"
        
        return DataContext(
            intent=QueryIntent.PROFIT_LEAKS,
            time_period=label,
            data={
                "profit_data": profit_ctx.data,
                "expense_categories": expenses_df.to_dict('records') if expenses_df is not None else [],
                "low_margin_items": low_margin_df.to_dict('records') if low_margin_df is not None else []
            },
            summary=summary,
            raw_numbers=profit_ctx.raw_numbers
        )
    
    def fetch_trends(self, time_period: str) -> DataContext:
        """Fetch trend data comparing periods"""
        # Current period
        current = self.fetch_profit_data(time_period)
        
        # Previous period for comparison
        prev_map = {
            "today": "yesterday",
            "this_week": "last_week",
            "this_month": "last_month",
            "last_7_days": "last_7_days",  # Will compare to 7 days before
            "last_30_days": "last_30_days",
        }
        prev_period = prev_map.get(time_period, "last_week")
        previous = self.fetch_profit_data(prev_period)
        
        # Calculate changes
        rev_change = current.data['revenue'] - previous.data['revenue']
        rev_pct = (rev_change / previous.data['revenue'] * 100) if previous.data['revenue'] > 0 else 0
        exp_change = current.data['expenses'] - previous.data['expenses']
        exp_pct = (exp_change / previous.data['expenses'] * 100) if previous.data['expenses'] > 0 else 0
        profit_change = current.data['profit'] - previous.data['profit']
        
        summary = f"""## TREND ANALYSIS: {current.time_period} vs {previous.time_period}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**REVENUE:**
• Current: ₹{current.data['revenue']:,.2f}
• Previous: ₹{previous.data['revenue']:,.2f}
• Change: ₹{rev_change:+,.2f} ({rev_pct:+.1f}%)

**EXPENSES:**
• Current: ₹{current.data['expenses']:,.2f}
• Previous: ₹{previous.data['expenses']:,.2f}
• Change: ₹{exp_change:+,.2f} ({exp_pct:+.1f}%)

**PROFIT:**
• Current: ₹{current.data['profit']:,.2f}
• Previous: ₹{previous.data['profit']:,.2f}
• Change: ₹{profit_change:+,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return DataContext(
            intent=QueryIntent.TRENDS,
            time_period=f"{current.time_period} vs {previous.time_period}",
            data={
                "current": current.data,
                "previous": previous.data,
                "changes": {
                    "revenue": rev_change,
                    "revenue_pct": rev_pct,
                    "expenses": exp_change,
                    "expenses_pct": exp_pct,
                    "profit": profit_change
                }
            },
            summary=summary,
            raw_numbers={
                "current_revenue": current.data['revenue'],
                "current_expenses": current.data['expenses'],
                "current_profit": current.data['profit'],
                "revenue_change": rev_change,
                "expense_change": exp_change
            }
        )
    
    def get_data_context(self, message: str) -> DataContext:
        """Main entry point - detect intent and fetch relevant data"""
        intent, time_period = self.detect_intent(message)

        return self.get_context(intent, time_period)

    def get_context(self, intent: QueryIntent, time_period: str) -> DataContext:
        if intent == QueryIntent.PROFIT or intent == QueryIntent.UNKNOWN:
            return self.fetch_profit_data(time_period)
        if intent == QueryIntent.REVENUE:
            return self.fetch_profit_data(time_period)
        if intent == QueryIntent.EXPENSES:
            return self.fetch_expense_breakdown(time_period)
        if intent == QueryIntent.TOP_ITEMS:
            return self.fetch_top_items(time_period)
        if intent == QueryIntent.PROFIT_LEAKS:
            return self.fetch_profit_leaks(time_period)
        if intent == QueryIntent.TRENDS or intent == QueryIntent.COMPARISON:
            return self.fetch_trends(time_period)
        if intent == QueryIntent.STAFF:
            ctx = self.fetch_profit_data(time_period)
            ctx.summary += "\n⚠️ **Staff performance data not available.** Need POS integration to track individual staff sales."
            return ctx

        return self.fetch_profit_data(time_period)


def get_smart_data_context(client, settings, message: str) -> str:
    """
    Convenience function to get formatted data context for AI prompt.
    This is the function the chat system should call.
    """
    try:
        di = DataIntelligence(client, settings)
        ctx = di.get_data_context(message)
        return ctx.summary
    except Exception as e:
        return f"⚠️ Data fetch error: {str(e)}. Proceeding with limited context."


def get_smart_data_payload(client, settings, message: str) -> Dict[str, Any]:
    try:
        di = DataIntelligence(client, settings)
        ctx = di.get_data_context(message)
        return {
            "ok": True,
            "intent": ctx.intent.value,
            "time_period": ctx.time_period,
            "summary": ctx.summary,
            "has_zero_data": bool(ctx.has_zero_data),
            "system_hint": ctx.system_hint,
            "visual_data": ctx.visual_data,
            "raw_numbers": ctx.raw_numbers,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "summary": f"⚠️ Data fetch error: {str(e)}. Proceeding with limited context.",
            "has_zero_data": False,
            "system_hint": None,
            "visual_data": None,
        }
