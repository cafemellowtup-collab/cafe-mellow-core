"""
Titan Cortex - The Adaptive Digital CFO Brain
==============================================
Phase 4A: Context-aware query engine that adapts to user's data maturity.

Features:
- Loads and manages user preferences
- Scans ledger to understand data profile
- Builds dynamic persona based on available data
- Handles simulation questions without DB corruption
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Windows encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from google import genai
from dotenv import load_dotenv

load_dotenv()

from backend.core.master_config import get_master_config


# =============================================================================
# Configuration
# =============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
_genai_client = None
if GEMINI_API_KEY:
    _genai_client = genai.Client(api_key=GEMINI_API_KEY)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PREFERENCES_FILE = DATA_DIR / "user_preferences.json"
BRAIN_CACHE_FILE = DATA_DIR / "brain_cache.json"


# =============================================================================
# Titan Cortex
# =============================================================================

class TitanCortex:
    """
    The adaptive brain of the Digital CFO.
    
    Responsibilities:
    - Load/save user preferences (rules, exclusions)
    - Scan ledger to understand data profile
    - Build context-aware prompts based on data maturity
    - Detect simulation parameters in questions
    """
    
    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self._preferences: Dict[str, Any] = {}
        self._brain_cache: Dict[str, Any] = {}
        self._data_profile: Dict[str, Any] = {}
        
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load preferences and brain cache
        self._load_preferences()
        self._load_brain_cache()
        
        # Initialize Gemini client (new google.genai library)
        self._client = _genai_client
        
        print(f"[CORTEX] Initialized for tenant: {tenant_id}")
    
    # =========================================================================
    # Preferences Management
    # =========================================================================
    
    def _load_preferences(self):
        """Load user preferences from JSON file."""
        if PREFERENCES_FILE.exists():
            try:
                with open(PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                    self._preferences = json.load(f)
                print(f"[CORTEX] Loaded {len(self._preferences)} preferences")
            except Exception as e:
                print(f"[CORTEX] Error loading preferences: {e}")
                self._preferences = {}
        else:
            # Create default preferences file
            self._preferences = {
                "created_at": datetime.now().isoformat(),
                "rules": [],
                "exclusions": [],
                "custom_categories": {},
                "display_currency": "INR",
                "fiscal_year_start": "April"
            }
            self._save_preferences()
            print("[CORTEX] Created default preferences file")
    
    def _save_preferences(self):
        """Save preferences to JSON file."""
        try:
            self._preferences["updated_at"] = datetime.now().isoformat()
            with open(PREFERENCES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._preferences, f, indent=2, ensure_ascii=False)
            print("[CORTEX] Saved preferences")
        except Exception as e:
            print(f"[CORTEX] Error saving preferences: {e}")
    
    def _load_brain_cache(self):
        """Load brain cache (knowledge base) from JSON file."""
        if BRAIN_CACHE_FILE.exists():
            try:
                with open(BRAIN_CACHE_FILE, 'r', encoding='utf-8') as f:
                    self._brain_cache = json.load(f)
                print(f"[CORTEX] Loaded brain cache with {len(self._brain_cache)} entries")
            except Exception as e:
                print(f"[CORTEX] Error loading brain cache: {e}")
                self._brain_cache = {}
        else:
            self._brain_cache = {}
    
    def update_preference(self, instruction: str) -> Dict[str, Any]:
        """
        Use AI to extract rules from natural language instruction.
        
        Examples:
        - "Don't count personal expenses" -> {"exclude_category": "PERSONAL"}
        - "My fiscal year starts in April" -> {"fiscal_year_start": "April"}
        - "Show amounts in USD" -> {"display_currency": "USD"}
        
        Returns:
            Dict with extracted rule and status
        """
        prompt = f"""You are a preference extraction AI. Extract structured rules from the user's instruction.

User Instruction: "{instruction}"

Extract ANY of these rule types if present:
1. exclude_category: Category to exclude (e.g., "PERSONAL", "LOAN_REPAYMENT")
2. include_only_category: Only include this category
3. fiscal_year_start: Month name (e.g., "April", "January")
4. display_currency: Currency code (e.g., "INR", "USD", "EUR")
5. custom_rule: Any other business rule as a string

Return ONLY valid JSON with the extracted rules. If no rule can be extracted, return {{"error": "Could not extract rule"}}.

Examples:
- "Don't include personal spending" -> {{"exclude_category": "PERSONAL"}}
- "My financial year starts in April" -> {{"fiscal_year_start": "April"}}
- "Only show me sales data" -> {{"include_only_category": "SALES"}}
- "Use dollars for display" -> {{"display_currency": "USD"}}

JSON Response:"""

        try:
            response = self._client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            text = response.text.strip()
            
            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            extracted = json.loads(text)
            
            if "error" in extracted:
                return {"ok": False, "message": extracted["error"]}
            
            # Apply extracted rules to preferences
            for key, value in extracted.items():
                if key == "exclude_category":
                    if "exclusions" not in self._preferences:
                        self._preferences["exclusions"] = []
                    if value not in self._preferences["exclusions"]:
                        self._preferences["exclusions"].append(value)
                elif key == "include_only_category":
                    self._preferences["include_only"] = value
                elif key in ["fiscal_year_start", "display_currency"]:
                    self._preferences[key] = value
                elif key == "custom_rule":
                    if "rules" not in self._preferences:
                        self._preferences["rules"] = []
                    self._preferences["rules"].append({
                        "text": instruction,
                        "extracted": value,
                        "added_at": datetime.now().isoformat()
                    })
            
            self._save_preferences()
            
            print(f"[CORTEX] Extracted preference: {extracted}")
            return {"ok": True, "extracted": extracted, "instruction": instruction}
            
        except Exception as e:
            print(f"[CORTEX] Preference extraction failed: {e}")
            return {"ok": False, "message": str(e)}
    
    def get_preferences(self) -> Dict[str, Any]:
        """Return current preferences."""
        return self._preferences.copy()
    
    # =========================================================================
    # Data Profile Scanning
    # =========================================================================
    
    def _scan_ledger_profile(self, tenant_id: str) -> Dict[str, Any]:
        """
        Scan the ledger to understand what data is available.
        
        Returns profile with:
        - has_sales: bool
        - has_inventory: bool
        - has_expenses: bool
        - last_upload: datetime or None
        - total_events: int
        - categories_present: list
        - date_range: (start, end)
        """
        profile = {
            "has_sales": False,
            "has_inventory": False,
            "has_expenses": False,
            "has_overhead": False,
            "last_upload": None,
            "total_events": 0,
            "categories_present": [],
            "date_range": None,
            "data_maturity": "empty"  # empty, minimal, partial, full
        }
        
        try:
            # Try BigQuery first
            from google.cloud import bigquery
            client = bigquery.Client()
            
            query = f"""
            SELECT 
                category,
                COUNT(*) as count,
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest
            FROM `cafe-mellow-core-2026.cafe_operations.universal_ledger`
            WHERE tenant_id = @tenant_id
            GROUP BY category
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("tenant_id", "STRING", tenant_id)
                ]
            )
            
            result = client.query(query, job_config=job_config).result()
            
            categories = []
            total = 0
            earliest = None
            latest = None
            
            for row in result:
                cat = row.category
                categories.append(cat)
                total += row.count
                
                if cat == "SALES":
                    profile["has_sales"] = True
                elif cat == "INVENTORY":
                    profile["has_inventory"] = True
                elif cat in ["EXPENSE", "EXPENSES", "OVERHEAD"]:
                    profile["has_expenses"] = True
                elif cat == "OVERHEAD":
                    profile["has_overhead"] = True
                
                if earliest is None or row.earliest < earliest:
                    earliest = row.earliest
                if latest is None or row.latest > latest:
                    latest = row.latest
            
            profile["categories_present"] = categories
            profile["total_events"] = total
            profile["last_upload"] = latest.isoformat() if latest else None
            profile["date_range"] = (
                earliest.isoformat() if earliest else None,
                latest.isoformat() if latest else None
            )
            
            # Determine data maturity
            if total == 0:
                profile["data_maturity"] = "empty"
            elif len(categories) == 1:
                profile["data_maturity"] = "minimal"
            elif len(categories) <= 3:
                profile["data_maturity"] = "partial"
            else:
                profile["data_maturity"] = "full"
                
        except Exception as e:
            print(f"[CORTEX] BigQuery scan failed, trying local: {e}")
            
            # Fallback to local JSONL
            try:
                ledger_file = DATA_DIR / "ledger" / f"{tenant_id}_ledger.jsonl"
                if ledger_file.exists():
                    categories = set()
                    total = 0
                    
                    with open(ledger_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                event = json.loads(line)
                                cat = event.get("category", "UNKNOWN")
                                categories.add(cat)
                                total += 1
                                
                                if cat == "SALES":
                                    profile["has_sales"] = True
                                elif cat == "INVENTORY":
                                    profile["has_inventory"] = True
                                elif cat in ["EXPENSE", "EXPENSES"]:
                                    profile["has_expenses"] = True
                    
                    profile["categories_present"] = list(categories)
                    profile["total_events"] = total
                    
                    if total == 0:
                        profile["data_maturity"] = "empty"
                    elif len(categories) == 1:
                        profile["data_maturity"] = "minimal"
                    elif len(categories) <= 3:
                        profile["data_maturity"] = "partial"
                    else:
                        profile["data_maturity"] = "full"
                        
            except Exception as e2:
                print(f"[CORTEX] Local scan also failed: {e2}")
        
        self._data_profile = profile
        return profile
    
    # =========================================================================
    # Deep History Analysis (Phase 4B)
    # =========================================================================
    
    def analyze_data_timeline(self, tenant_id: str) -> Dict[str, Any]:
        """
        Deep scan of data across 5 years to understand user habits.
        
        Returns:
            history_profile with:
            - monthly_density: dict of YYYY-MM -> {categories, count, density_score}
            - operating_mode: "Monthly Batcher", "Daily Diligent", "Chaos User", etc.
            - discipline_eras: periods of good vs poor data tracking
            - benchmark_period: best period to use for estimations
            - data_gaps: list of missing months/categories
        """
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        history = {
            "monthly_density": {},
            "operating_mode": "Unknown",
            "discipline_eras": [],
            "benchmark_period": None,
            "benchmark_margins": {},
            "data_gaps": [],
            "total_months_with_data": 0,
            "category_coverage": {},
            "user_habits": [],
            "scan_date": datetime.now().isoformat()
        }
        
        try:
            from google.cloud import bigquery
            client = bigquery.Client()
            
            # Deep scan: Get monthly breakdown for last 5 years
            query = f"""
            WITH monthly_stats AS (
                SELECT 
                    FORMAT_TIMESTAMP('%Y-%m', timestamp) as month,
                    category,
                    COUNT(*) as event_count,
                    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_positive,
                    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_negative
                FROM `cafe-mellow-core-2026.cafe_operations.universal_ledger`
                WHERE tenant_id = @tenant_id
                  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1825 DAY)
                GROUP BY month, category
            )
            SELECT 
                month,
                ARRAY_AGG(STRUCT(category, event_count, total_positive, total_negative)) as categories,
                SUM(event_count) as total_events
            FROM monthly_stats
            GROUP BY month
            ORDER BY month
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("tenant_id", "STRING", tenant_id)
                ]
            )
            
            result = client.query(query, job_config=job_config).result()
            
            months_with_sales = 0
            months_with_expenses = 0
            months_with_both = 0
            total_months = 0
            
            diligent_months = []
            lazy_months = []
            
            for row in result:
                month = row.month
                total_events = row.total_events
                categories_data = row.categories
                
                # Parse categories
                cats = [c['category'] for c in categories_data]
                has_sales = 'SALES' in cats
                has_expenses = any(c in cats for c in ['EXPENSE', 'EXPENSES', 'OVERHEAD'])
                
                # Calculate density score (0-100)
                density_score = min(100, total_events / 10 * 10)  # 100 events = 100 score
                if has_sales and has_expenses:
                    density_score = min(100, density_score + 30)  # Bonus for completeness
                
                # Determine month quality
                if has_sales and has_expenses and total_events >= 20:
                    quality = "Diligent"
                    diligent_months.append(month)
                elif has_sales or has_expenses:
                    quality = "Partial"
                else:
                    quality = "Lazy"
                    lazy_months.append(month)
                
                history["monthly_density"][month] = {
                    "categories": cats,
                    "event_count": total_events,
                    "density_score": density_score,
                    "has_sales": has_sales,
                    "has_expenses": has_expenses,
                    "quality": quality
                }
                
                if has_sales:
                    months_with_sales += 1
                if has_expenses:
                    months_with_expenses += 1
                if has_sales and has_expenses:
                    months_with_both += 1
                total_months += 1
            
            history["total_months_with_data"] = total_months
            
            # Determine operating mode
            if total_months == 0:
                history["operating_mode"] = "New User"
            elif len(diligent_months) > total_months * 0.7:
                history["operating_mode"] = "The Daily Diligent"
                history["user_habits"].append("Consistently tracks both sales and expenses")
            elif len(diligent_months) > total_months * 0.3:
                history["operating_mode"] = "The Monthly Batcher"
                history["user_habits"].append("Uploads data periodically, some gaps exist")
            elif months_with_sales > months_with_expenses * 2:
                history["operating_mode"] = "The Sales Tracker"
                history["user_habits"].append("Strong on sales tracking, expenses often missing")
            elif months_with_expenses > months_with_sales * 2:
                history["operating_mode"] = "The Bill Keeper"
                history["user_habits"].append("Tracks expenses well, sales data incomplete")
            else:
                history["operating_mode"] = "The Chaos User"
                history["user_habits"].append("Inconsistent data uploads, many gaps")
            
            # Find benchmark period (best consecutive months with complete data)
            if diligent_months:
                history["benchmark_period"] = {
                    "months": diligent_months[-3:] if len(diligent_months) >= 3 else diligent_months,
                    "quality": "High",
                    "use_for_estimation": True
                }
                
                # Calculate benchmark margins from diligent period
                benchmark_query = f"""
                SELECT 
                    SUM(CASE WHEN category = 'SALES' THEN amount ELSE 0 END) as revenue,
                    SUM(CASE WHEN category IN ('EXPENSE', 'EXPENSES', 'OVERHEAD') THEN ABS(amount) ELSE 0 END) as costs
                FROM `cafe-mellow-core-2026.cafe_operations.universal_ledger`
                WHERE tenant_id = @tenant_id
                  AND FORMAT_TIMESTAMP('%Y-%m', timestamp) IN UNNEST(@months)
                """
                
                margin_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("tenant_id", "STRING", tenant_id),
                        bigquery.ArrayQueryParameter("months", "STRING", history["benchmark_period"]["months"])
                    ]
                )
                
                try:
                    margin_result = list(client.query(benchmark_query, job_config=margin_config).result())
                    if margin_result:
                        row = margin_result[0]
                        revenue = float(row.revenue or 0)
                        costs = float(row.costs or 0)
                        if revenue > 0:
                            margin = ((revenue - costs) / revenue) * 100
                            history["benchmark_margins"] = {
                                "revenue": revenue,
                                "costs": costs,
                                "profit_margin_pct": round(margin, 1),
                                "period": history["benchmark_period"]["months"]
                            }
                except Exception as e:
                    print(f"[CORTEX] Benchmark margin calc failed: {e}")
            
            # Identify data gaps (lazy eras)
            history["discipline_eras"] = [
                {"type": "Diligent", "months": diligent_months},
                {"type": "Lazy", "months": lazy_months}
            ]
            history["data_gaps"] = lazy_months
            
            # Category coverage
            history["category_coverage"] = {
                "sales_coverage_pct": round(months_with_sales / max(total_months, 1) * 100, 1),
                "expense_coverage_pct": round(months_with_expenses / max(total_months, 1) * 100, 1),
                "complete_coverage_pct": round(months_with_both / max(total_months, 1) * 100, 1)
            }
            
        except Exception as e:
            print(f"[CORTEX] Timeline analysis failed: {e}")
            history["error"] = str(e)
            history["operating_mode"] = "Unknown (Analysis Failed)"
        
        self._history_profile = history
        return history
    
    def generate_system_persona(self, profile: Dict[str, Any], 
                                 history_profile: Dict[str, Any]) -> str:
        """
        Generate a living persona that adapts based on data timeline.
        
        Rules:
        1. HONESTY: Never sugar-coat. State missing data and limitations clearly.
        2. CONTEXT: Reference user's history and patterns.
        3. ADAPTABILITY: Treat users with rich history as experienced businesses.
        """
        operating_mode = history_profile.get("operating_mode", "Unknown")
        benchmark = history_profile.get("benchmark_margins", {})
        gaps = history_profile.get("data_gaps", [])
        coverage = history_profile.get("category_coverage", {})
        habits = history_profile.get("user_habits", [])
        total_months = history_profile.get("total_months_with_data", 0)
        
        # Base persona based on data richness
        if total_months >= 24:
            base = """You are the PERFECT HUMAN CFO - a seasoned financial advisor who has been with this business for years.
You have deep knowledge of their history, patterns, and habits. Speak with authority."""
        elif total_months >= 6:
            base = """You are a SHARP FINANCIAL ANALYST getting to know this business.
You've seen enough to identify patterns but acknowledge gaps in the historical record."""
        else:
            base = """You are a BUSINESS CONSULTANT just starting to understand this company.
Be helpful but honest about limited historical context."""
        
        # Add operating mode context
        mode_context = f"""
## USER OPERATING MODE: {operating_mode}
{chr(10).join('- ' + h for h in habits) if habits else '- No specific habits identified yet'}"""
        
        # Add honesty rules
        honesty_rules = """
## HONESTY PROTOCOL (NEVER VIOLATE)
1. **Never hallucinate success.** If profit is down or data is missing, state it directly.
2. **Never hide bad news.** Users deserve the truth, even when uncomfortable.
3. **Never fill gaps with optimism.** If expenses are missing, say "I cannot calculate true profit without expense data."
4. **Always show your reasoning.** Explain what data you used and what you assumed."""
        
        # Add historical context instructions
        if gaps:
            gap_str = ', '.join(gaps[:6]) + ('...' if len(gaps) > 6 else '')
            gap_context = f"""
## DATA GAPS DETECTED
Missing/incomplete months: {gap_str}
When user asks about these periods:
- State clearly: "Your {gap_str} data is incomplete."
- Offer estimation: "Based on your {benchmark.get('period', ['good months'])}, I can estimate..."
- Request action: "Upload your bills/invoices for accurate numbers." """
        else:
            gap_context = """
## DATA QUALITY: EXCELLENT
No significant gaps detected. Provide full analysis with confidence."""
        
        # Add benchmark context
        if benchmark:
            margin = benchmark.get('profit_margin_pct', 0)
            benchmark_context = f"""
## BENCHMARK AVAILABLE
From your best data period ({', '.join(benchmark.get('period', []))}):
- Profit Margin: {margin}%
- Revenue: ₹{benchmark.get('revenue', 0):,.0f}
- Costs: ₹{benchmark.get('costs', 0):,.0f}

USE THIS FOR ESTIMATIONS during lazy periods. Always disclose when using estimates."""
        else:
            benchmark_context = """
## NO BENCHMARK AVAILABLE
Cannot provide margin estimates. Encourage user to upload complete data for at least 2-3 months."""
        
        # Combine into full persona
        persona = f"""{base}
{mode_context}
{honesty_rules}
{gap_context}
{benchmark_context}

## RESPONSE STYLE
- Be direct and factual
- Reference specific periods when relevant ("In March 2024, you...")
- Acknowledge patterns ("I notice you typically upload bills at month-end...")
- Suggest improvements without being preachy
- If asked about a 'Lazy Era', use benchmarks but ALWAYS disclose the estimation"""
        
        return persona
    
    # =========================================================================
    # Simulation Detection
    # =========================================================================
    
    def _detect_simulation_params(self, question: str) -> Dict[str, Any]:
        """
        Detect simulation parameters in the question.
        
        Examples:
        - "If I sell 5kg of coffee at Rs 500/kg" -> {quantity: 5, unit: "kg", price: 500}
        - "What if revenue increases by 20%" -> {percentage_change: 20, metric: "revenue"}
        - "Calculate profit for 100 orders" -> {order_count: 100}
        """
        simulation = {
            "is_simulation": False,
            "params": {},
            "type": None  # "what_if", "projection", "calculation"
        }
        
        # Detect simulation keywords
        sim_keywords = ["if i", "what if", "suppose", "assume", "calculate for", 
                        "project", "forecast", "estimate", "hypothetically"]
        
        question_lower = question.lower()
        for keyword in sim_keywords:
            if keyword in question_lower:
                simulation["is_simulation"] = True
                break
        
        # Extract numeric parameters
        # Pattern: number + unit (kg, units, orders, %, rupees, etc.)
        patterns = [
            (r'(\d+(?:\.\d+)?)\s*kg', 'quantity_kg'),
            (r'(\d+(?:\.\d+)?)\s*units?', 'quantity_units'),
            (r'(\d+(?:\.\d+)?)\s*orders?', 'order_count'),
            (r'(\d+(?:\.\d+)?)\s*%', 'percentage'),
            (r'(?:rs|₹|inr)\s*(\d+(?:,\d+)*(?:\.\d+)?)', 'amount_inr'),
            (r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rs|₹|rupees?)', 'amount_inr'),
            (r'\$\s*(\d+(?:,\d+)*(?:\.\d+)?)', 'amount_usd'),
            (r'(\d+(?:\.\d+)?)\s*(?:per|/)\s*kg', 'price_per_kg'),
            (r'(\d+(?:\.\d+)?)\s*(?:per|/)\s*unit', 'price_per_unit'),
        ]
        
        for pattern, param_name in patterns:
            match = re.search(pattern, question_lower)
            if match:
                value = match.group(1).replace(',', '')
                simulation["params"][param_name] = float(value)
                simulation["is_simulation"] = True
        
        # Determine simulation type
        if simulation["is_simulation"]:
            if "what if" in question_lower or "if i" in question_lower:
                simulation["type"] = "what_if"
            elif "project" in question_lower or "forecast" in question_lower:
                simulation["type"] = "projection"
            else:
                simulation["type"] = "calculation"
        
        return simulation
    
    # =========================================================================
    # Context Prompt Building
    # =========================================================================
    
    def build_context_prompt(self, question: str, tenant_id: str, 
                              include_history: bool = True) -> str:
        """
        Build a robust context prompt for the Query Engine.
        
        Steps:
        1. Scan data profile (what data is available?)
        2. Analyze data timeline (Deep History - Phase 4B)
        3. Check user preferences (exclusions, rules)
        4. Generate adaptive persona based on history
        5. Detect simulation parameters
        6. Build final system prompt
        """
        # Step 1: Scan data profile
        profile = self._scan_ledger_profile(tenant_id)
        print(f"[CORTEX] Data profile: {profile['data_maturity']}, categories: {profile['categories_present']}")
        
        # Step 2: Analyze Deep History (Phase 4B)
        history_profile = {}
        if include_history:
            history_profile = self.analyze_data_timeline(tenant_id)
            print(f"[CORTEX] Operating mode: {history_profile.get('operating_mode')}, " +
                  f"Months: {history_profile.get('total_months_with_data')}")
        
        # Step 3: Check preferences
        exclusions = self._preferences.get("exclusions", [])
        rules = self._preferences.get("rules", [])
        include_only = self._preferences.get("include_only")
        currency = self._preferences.get("display_currency", "INR")
        fiscal_start = self._preferences.get("fiscal_year_start", "April")
        
        # Step 4: Generate adaptive persona (Phase 4B upgrade)
        if include_history and history_profile.get("total_months_with_data", 0) > 0:
            # Use the new Deep History persona generator
            persona = self.generate_system_persona(profile, history_profile)
        else:
            # Fallback to basic persona for new users
            if profile["data_maturity"] == "empty":
                persona = """You are a helpful Business Setup Assistant. 
The user hasn't uploaded any data yet. Guide them on what data to upload first.
Suggest starting with sales data or expense reports."""
                
            elif profile["has_sales"] and not profile["has_expenses"]:
                persona = """You are a Revenue Strategist specializing in sales optimization.
Focus on: Revenue trends, top products, sales velocity, customer patterns.
Note: Expense data not available yet - recommend uploading for profit analysis."""
                
            elif profile["has_expenses"] and not profile["has_sales"]:
                persona = """You are a Cost Controller specializing in expense management.
Focus on: Spending patterns, cost categories, budget analysis.
Note: Sales data not available yet - recommend uploading for margin analysis."""
                
            elif profile["has_sales"] and profile["has_expenses"] and profile["has_inventory"]:
                persona = """You are a Full-Stack CFO with complete visibility into the business.
You can analyze: Revenue, Expenses, Inventory, Margins, Cash Flow, P&L.
Provide holistic business insights connecting all data points."""
                
            elif profile["has_sales"] and profile["has_expenses"]:
                persona = """You are a Digital CFO focused on profitability.
You can analyze: Revenue, Expenses, Gross Margins, Operating Costs.
Note: Inventory data not available - some COGS calculations may be limited."""
                
            else:
                persona = f"""You are an Adaptive Business Analyst.
Available data categories: {', '.join(profile['categories_present']) or 'None'}.
Provide insights based on available data and note any limitations."""
        
        # Step 5: Detect simulation parameters
        simulation = self._detect_simulation_params(question)
        
        # Step 6: Get Master Config (God Mode - Phase 6)
        master_config = get_master_config()
        disabled_features = master_config.get_disabled_features(tenant_id)
        feature_restrictions = master_config.get_feature_restrictions_prompt(tenant_id)
        global_rules = master_config.get_rules_text()
        
        # Check if simulation is disabled for this tenant
        sim_instructions = ""
        if simulation["is_simulation"] and "simulation_mode" in disabled_features:
            # Simulation is disabled - inject restriction
            sim_instructions = """
## FEATURE RESTRICTION: SIMULATION MODE DISABLED
The user is asking a simulation/what-if question, but Simulation Mode is DISABLED for their plan.
You MUST politely decline and explain:
- "Simulation mode is not available on your current plan."
- "Please contact support to upgrade and access what-if analysis features."
Do NOT attempt to answer the simulation question."""
        elif simulation["is_simulation"]:
            params_str = json.dumps(simulation["params"])
            sim_instructions = f"""
## SIMULATION MODE ACTIVE
The user is asking a hypothetical/simulation question.
Detected parameters: {params_str}
Simulation type: {simulation["type"]}

IMPORTANT:
- Use a WITH clause or inline calculations for simulation numbers
- DO NOT modify or insert into the database
- Clearly label results as "Simulated" or "Projected"
- Show the calculation methodology"""
        
        # Step 7: Build exclusion rules
        exclusion_text = ""
        if exclusions:
            exclusion_text = f"""
## EXCLUSION RULES
The user has configured these exclusions - ALWAYS filter them out:
- Excluded categories: {', '.join(exclusions)}
Add WHERE clauses to exclude these categories from all queries."""
        
        # Step 8: Build Master's rules injection
        master_rules_text = ""
        if global_rules:
            master_rules_text = f"\n{global_rules}\n"
        
        if feature_restrictions:
            master_rules_text += f"\n{feature_restrictions}\n"
        
        if include_only:
            exclusion_text += f"""
- Include ONLY: {include_only} category
Filter all queries to only this category."""
        
        # Build final context prompt
        context = f"""# TITAN CORTEX - Digital CFO System Prompt

## YOUR PERSONA
{persona}

## TENANT CONTEXT
- Tenant ID: {tenant_id}
- Data Maturity: {profile['data_maturity']}
- Total Events: {profile['total_events']}
- Categories Available: {', '.join(profile['categories_present']) or 'None'}
- Date Range: {profile['date_range'][0] if profile['date_range'] else 'N/A'} to {profile['date_range'][1] if profile['date_range'] else 'N/A'}

## USER PREFERENCES
- Display Currency: {currency}
- Fiscal Year Start: {fiscal_start}
{exclusion_text}
{sim_instructions}
{master_rules_text}
## BIGQUERY SCHEMA
Table: `cafe-mellow-core-2026.cafe_operations.universal_ledger`
Columns:
- event_id (STRING): Unique event identifier
- tenant_id (STRING): Tenant identifier (ALWAYS filter by this)
- timestamp (TIMESTAMP): Event date/time
- source_system (STRING): Data source
- category (STRING): SALES, INVENTORY, EXPENSE, OVERHEAD, etc.
- sub_category (STRING): Detailed category
- amount (FLOAT): Monetary value
- entity_name (STRING): Item/product/vendor name
- reference_id (STRING): Invoice/order number
- rich_data (STRING): JSON with additional details
- confidence_score (FLOAT): AI classification confidence
- verified (BOOL): Human-verified flag

## RESPONSE FORMAT
You MUST respond with valid JSON:
{{
    "sql": "SELECT ... FROM ... WHERE tenant_id = '{tenant_id}' ...",
    "answer_text": "Human-readable answer explaining the results",
    "visualization_hint": "table|bar_chart|line_chart|pie_chart|number",
    "confidence": 0.0-1.0
}}

If the question cannot be answered with data:
{{
    "sql": null,
    "answer_text": "Explanation of why and what data is needed",
    "visualization_hint": null,
    "confidence": 0.0
}}

## USER QUESTION
{question}
"""
        
        return context
    
    def get_data_profile(self, tenant_id: str) -> Dict[str, Any]:
        """Get or refresh data profile for a tenant."""
        return self._scan_ledger_profile(tenant_id)


# =============================================================================
# Global Instance
# =============================================================================

_cortex: Optional[TitanCortex] = None


def get_cortex(tenant_id: Optional[str] = None) -> TitanCortex:
    """Get or create global TitanCortex instance."""
    global _cortex
    if _cortex is None or (tenant_id and _cortex.tenant_id != tenant_id):
        _cortex = TitanCortex(tenant_id)
    return _cortex
