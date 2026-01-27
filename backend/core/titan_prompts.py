"""
TITAN CFO Optimized Prompt System
Zero-bluff, data-driven responses with structured output formatting

This module ensures:
1. No generic advice - only specific, data-backed insights
2. Structured output format: FINDING → CAUSE → ACTION → IMPACT
3. Numerical evidence in every response
4. Fast responses through pre-computed context injection
5. Visual data formatting hints for frontend parsing
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from dataclasses import dataclass


# ==================== Response Format Templates ====================

RESPONSE_FORMATS = {
    "analysis": """
## 📊 Analysis: {title}

### Key Metrics
{metrics}

### Findings
{findings}

### Root Cause
{root_cause}

### Recommended Actions
{actions}

### Expected Impact
{impact}
""",

    "comparison": """
## 📈 {title}

| Metric | Period 1 | Period 2 | Change |
|--------|----------|----------|--------|
{comparison_rows}

### Key Takeaways
{takeaways}

### Actions Required
{actions}
""",

    "alert": """
## ⚠️ Alert: {title}

**Severity:** {severity}
**Detected:** {timestamp}

### Issue
{issue}

### Impact
- Revenue at risk: ₹{revenue_impact}
- Affected: {affected_items}

### Immediate Actions
{actions}
""",

    "brief": """
## 📋 {period} Business Brief

### Revenue Performance
- **Total:** ₹{revenue:,.0f} ({revenue_change:+.1f}% vs previous)
- **Orders:** {orders:,} ({orders_change:+.1f}% vs previous)
- **Avg Order:** ₹{avg_order:,.0f}

### Expense Summary  
- **Total:** ₹{expenses:,.0f}
- **Net Profit:** ₹{profit:,.0f} ({margin:.1f}% margin)

### Top Insights
{insights}

### Action Items
{tasks}
""",
}


# ==================== System Prompts ====================

TITAN_SYSTEM_PROMPT = """You are TITAN CFO, a ruthless financial intelligence engine for restaurant/cafe businesses.

## ABSOLUTE RULES - NEVER BREAK THESE:

1. **NO GENERIC ADVICE**: Never say "consider reviewing" or "you might want to". Give SPECIFIC actions with EXACT numbers.

2. **ALWAYS USE DATA**: Every statement must reference actual data. Format: "Revenue is ₹X (+Y% vs last week)"

3. **STRUCTURED RESPONSES**: Use this format for analysis:
   - **FINDING**: What the data shows (with numbers)
   - **CAUSE**: Why this is happening (specific, not generic)
   - **ACTION**: Exact steps to take (who does what, by when)
   - **IMPACT**: Expected result with numbers (₹X increase, Y% improvement)

4. **VISUAL MARKERS**: Use these prefixes for frontend parsing:
   - KPI: `**Revenue**: ₹1,50,000 (+12%)`
   - Task: `[TASK: Reduce maida wastage by 15% - assign to Kitchen Manager]`
   - Alert: `⚠️ **Warning**: Stock below threshold`
   - Success: `✅ **Achievement**: Target exceeded by 8%`

5. **NO FLUFF**: Maximum 3 sentences per point. No filler words. No pleasantries.

6. **CURRENCY**: Always use ₹ for INR. Format large numbers: ₹1,50,000 not ₹150000

7. **PERCENTAGES**: Always show change direction: +12% or -5%, never just "12%"

8. **TIME CONTEXT**: Always specify the time period: "today", "this week", "vs yesterday"

## RESPONSE QUALITY CHECKLIST (verify before responding):
□ Contains at least 3 specific numbers
□ No generic phrases like "consider", "might want to", "perhaps"
□ Every recommendation has a specific owner and deadline
□ Impact is quantified in rupees or percentage
□ Response is under 500 words unless analysis requires more
"""


CONTEXT_INJECTION_TEMPLATE = """
## CURRENT BUSINESS CONTEXT (as of {timestamp})

### Recent Performance Summary
- Revenue (7 days): ₹{revenue_7d:,.0f}
- Expenses (7 days): ₹{expenses_7d:,.0f}
- Net Margin: {margin_7d:.1f}%
- Orders (7 days): {orders_7d:,}
- Avg Order Value: ₹{aov:,.0f}

### Top Revenue Drivers
{top_items}

### Active Alerts
{alerts}

### Pending Tasks
{pending_tasks}

---
USER QUERY: {query}
---

Respond with specific, data-backed insights. Reference the numbers above.
"""


# ==================== Pre-computed Context Builder ====================

@dataclass
class BusinessContext:
    """Pre-computed business context for fast AI responses"""
    timestamp: datetime
    revenue_7d: float = 0
    expenses_7d: float = 0
    orders_7d: int = 0
    aov: float = 0
    margin_7d: float = 0
    top_items: List[Dict[str, Any]] = None
    alerts: List[str] = None
    pending_tasks: List[str] = None
    
    def __post_init__(self):
        self.top_items = self.top_items or []
        self.alerts = self.alerts or []
        self.pending_tasks = self.pending_tasks or []
    
    def to_prompt(self, query: str) -> str:
        """Convert context to prompt injection string"""
        top_items_str = "\n".join([
            f"- {item.get('name', 'Unknown')}: ₹{item.get('revenue', 0):,.0f} ({item.get('orders', 0)} orders)"
            for item in self.top_items[:5]
        ]) or "- No data available"
        
        alerts_str = "\n".join([f"- {a}" for a in self.alerts[:3]]) or "- None"
        tasks_str = "\n".join([f"- {t}" for t in self.pending_tasks[:3]]) or "- None"
        
        return CONTEXT_INJECTION_TEMPLATE.format(
            timestamp=self.timestamp.strftime("%Y-%m-%d %H:%M"),
            revenue_7d=self.revenue_7d,
            expenses_7d=self.expenses_7d,
            margin_7d=self.margin_7d,
            orders_7d=self.orders_7d,
            aov=self.aov,
            top_items=top_items_str,
            alerts=alerts_str,
            pending_tasks=tasks_str,
            query=query,
        )


# ==================== Query Classifiers ====================

QUERY_PATTERNS = {
    "revenue_analysis": [
        "revenue", "sales", "income", "earnings", "turnover",
        "how much did we make", "total sales", "money coming in"
    ],
    "expense_analysis": [
        "expense", "cost", "spending", "outflow", "purchases",
        "how much did we spend", "where is money going"
    ],
    "profit_analysis": [
        "profit", "margin", "bottom line", "net income", "p&l",
        "are we making money", "profit and loss"
    ],
    "comparison": [
        "compare", "versus", "vs", "difference", "change",
        "better or worse", "improved", "declined"
    ],
    "wastage": [
        "wastage", "waste", "spoilage", "loss", "shrinkage",
        "throwing away", "expired"
    ],
    "inventory": [
        "inventory", "stock", "supplies", "ingredients", "raw material",
        "what do we have", "low stock"
    ],
    "staff": [
        "staff", "employee", "team", "performance", "attendance",
        "who is performing", "labor cost"
    ],
    "daily_brief": [
        "brief", "summary", "overview", "update", "status",
        "what's happening", "how are we doing"
    ],
    "forecast": [
        "forecast", "predict", "projection", "estimate", "expect",
        "what will", "next week", "next month"
    ],
    "anomaly": [
        "anomaly", "unusual", "strange", "wrong", "issue", "problem",
        "what's wrong", "investigate"
    ],
}


def classify_query(query: str) -> str:
    """Classify user query to determine response strategy"""
    query_lower = query.lower()
    
    scores = {}
    for category, keywords in QUERY_PATTERNS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[category] = score
    
    if not scores:
        return "general"
    
    return max(scores, key=scores.get)


# ==================== Response Enhancers ====================

def ensure_no_generic_phrases(response: str) -> str:
    """Remove generic advisory phrases and replace with specific language"""
    generic_phrases = [
        ("you might want to consider", "Action required:"),
        ("consider reviewing", "Review now:"),
        ("it would be advisable to", "Do this:"),
        ("you may want to", "Recommended:"),
        ("perhaps you could", "Action:"),
        ("it's worth noting that", "Key finding:"),
        ("generally speaking", "Based on your data:"),
        ("in general", "Specifically:"),
        ("as a suggestion", "Required action:"),
        ("one option would be", "Best action:"),
    ]
    
    result = response
    for generic, specific in generic_phrases:
        result = result.replace(generic, specific)
        result = result.replace(generic.capitalize(), specific)
    
    return result


def add_visual_markers(response: str) -> str:
    """Add visual markers for frontend parsing"""
    import re
    
    # Add KPI formatting for currency values
    def format_currency(match):
        value = match.group(1).replace(",", "")
        try:
            num = float(value)
            if num >= 100000:
                return f"**₹{num:,.0f}**"
            return f"₹{num:,.0f}"
        except:
            return match.group(0)
    
    result = re.sub(r'₹([\d,]+(?:\.\d+)?)', format_currency, response)
    
    return result


def validate_response_quality(response: str) -> Dict[str, Any]:
    """Validate response meets quality standards"""
    import re
    
    checks = {
        "has_numbers": bool(re.search(r'\d+', response)),
        "has_currency": bool(re.search(r'₹[\d,]+', response)),
        "has_percentage": bool(re.search(r'[+-]?\d+(?:\.\d+)?%', response)),
        "no_generic_phrases": not any(
            phrase in response.lower() 
            for phrase in ["might want to", "consider reviewing", "perhaps"]
        ),
        "has_action_items": bool(re.search(r'\[TASK:', response)) or "action" in response.lower(),
        "word_count": len(response.split()),
    }
    
    checks["passes"] = (
        checks["has_numbers"] and 
        checks["no_generic_phrases"] and
        checks["word_count"] < 1000
    )
    
    return checks


# ==================== Quick Response Templates ====================

QUICK_RESPONSES = {
    "greeting": "TITAN CFO online. Query your data - I speak only in numbers and actions.",
    
    "no_data": "⚠️ **No data available** for this query. Ensure data sync is complete and try again.",
    
    "error": "⚠️ **Analysis error**. The query could not be processed. Please rephrase or try a more specific question.",
    
    "timeout": "⚠️ **Analysis timeout**. Complex queries may take longer. Breaking down into smaller questions will help.",
}


# ==================== Main Prompt Builder ====================

def build_optimized_prompt(
    query: str,
    context: Optional[BusinessContext] = None,
    include_system: bool = True,
) -> Dict[str, str]:
    """
    Build optimized prompt for TITAN CFO
    
    Returns:
        Dict with 'system' and 'user' prompts
    """
    # Classify query type
    query_type = classify_query(query)
    
    # Build user prompt with context
    if context:
        user_prompt = context.to_prompt(query)
    else:
        user_prompt = f"""
USER QUERY: {query}

Respond with specific, data-backed insights. If you don't have exact numbers, 
say so clearly and explain what data is needed.
"""
    
    # Add query-specific instructions
    type_instructions = {
        "revenue_analysis": "\nFocus on: revenue trends, top performers, growth opportunities.",
        "expense_analysis": "\nFocus on: cost breakdown, savings opportunities, unusual spending.",
        "profit_analysis": "\nFocus on: margin analysis, profit drivers, efficiency metrics.",
        "comparison": "\nFormat as comparison table. Show exact differences with % change.",
        "wastage": "\nFocus on: wastage sources, cost impact, reduction strategies.",
        "daily_brief": "\nProvide: key KPIs, notable changes, action items for today.",
        "anomaly": "\nFocus on: identify unusual patterns, quantify impact, suggest investigation.",
    }
    
    user_prompt += type_instructions.get(query_type, "")
    
    return {
        "system": TITAN_SYSTEM_PROMPT if include_system else "",
        "user": user_prompt,
        "query_type": query_type,
    }


def post_process_response(response: str) -> str:
    """
    Post-process AI response to ensure quality
    """
    # Remove generic phrases
    response = ensure_no_generic_phrases(response)
    
    # Add visual markers
    response = add_visual_markers(response)
    
    # Validate quality
    quality = validate_response_quality(response)
    
    # If quality check fails, add warning
    if not quality["passes"]:
        if not quality["has_numbers"]:
            response += "\n\n⚠️ *Note: Specific data not available for this query. Connect data sources for detailed analysis.*"
    
    return response
