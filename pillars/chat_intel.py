"""
TITAN Intelligence Chat: Detect "I cannot answer", log to dev_evolution_log,
Deep Context Injection: Expense Investigator pre-query, exclude-ledgers parsing,
Heuristic Filter (Explanation/Reason), and Categorized Table (Core Bill vs Contingency).
"""
import re
from datetime import date
from .evolution import log_logic_gap
from .expense_analysis_engine import parse_excluded_ledgers

# --- Expense Investigator: keywords that trigger BigQuery pre-query ---
EXPENSE_INVESTIGATOR_KEYWORDS = [
    "electricity", "electric", "rent", "salary", "salaries", "advance", "advances",
    "spend", "spending", "ledger", "p&l", "profit", "loss", "expense", "expenses",
    "house keeping", "housekeeping", "all", "categories", "analyse", "analysis", "each", "every",
]


def parse_time_window(prompt: str):
    """
    Parse natural-language time windows from the user prompt. Order: most specific first.
    Returns (date_and_sql: str|None, label: str, days: int|None).
    - date_and_sql: SQL fragment to AND to WHERE (e.g. expense_date >= DATE_SUB(...)); None = no filter.
    - label: human label for the window (e.g. "last 30 days", "this month").
    - days: number of days (for get_power_contingency_vs_eb); None if not applicable (e.g. yesterday=1, this month=days in month).
    """
    t = (prompt or "").lower()
    if re.search(r"\b(?:last|past)\s+2\s+years?\b", t):
        return ("expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 730 DAY)", "last 2 years", 730)
    if re.search(r"\b(?:last|past)\s+(?:1\s+)?years?\b", t) or "last year" in t or "past year" in t:
        return ("expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)", "last year", 365)
    if re.search(r"\b(?:last|past)\s+90\s+days?\b", t) or re.search(r"\b(?:last|past)\s+3\s+months?\b", t):
        return ("expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)", "last 90 days", 90)
    if "this month" in t:
        d = (date.today() - date.today().replace(day=1)).days + 1
        return ("expense_date >= DATE_TRUNC(CURRENT_DATE(), MONTH)", "this month", max(1, d))
    if re.search(r"\b(?:last|past)\s+30\s+days?\b", t) or re.search(r"\b(?:last|past)\s+1\s+months?\b", t) or re.search(r"\b(?:last|past)\s+months?\b", t):
        return ("expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)", "last 30 days", 30)
    if re.search(r"\b(?:last|past)\s+15\s+days?\b", t):
        return ("expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 15 DAY)", "last 15 days", 15)
    if re.search(r"\b(?:last|past|this)\s+weeks?\b", t):
        return ("expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)", "last 7 days", 7)
    if "yesterday" in t:
        return ("expense_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)", "yesterday", 1)
    return (None, "", None)

# --- Heuristic Filter: forensic keywords in Explanation (item_name) and Reason (category) ---
HEURISTIC_FILTER_KEYWORDS = ["eb", "motor", "diesel", "generator", "gen ", "diesal", "disal", "eb man", "electric", "rent", "salary"]

# --- Category mapping: Core Bill vs Contingency ---
# Core Bill = main utility (EB, electricity), rent, salary
CORE_BILL_PATTERNS = re.compile(r"\b(eb|electric|electricity|rent|salary|salaries)\b", re.I)
# Contingency = diesel, generator, motor (backup power)
CONTINGENCY_PATTERNS = re.compile(r"\b(diesel|diesal|disal|generator|gen\b|motor|eb man)\b", re.I)
# Maintenance = service, tips, repair
MAINTENANCE_PATTERNS = re.compile(r"\b(service|tip|repair|maintenance)\b", re.I)


def expense_investigator_prequery(client, settings, user_prompt: str, exclude_ledgers=None):
    """
    Deep Context Injection: If the prompt contains expense-related keywords, run a BigQuery
    pre-query and return matching rows from expenses_master for injection into the Gemini prompt.
    Uses ledger_name when available, else category. exclude_ledgers: from parse_excluded_ledgers(prompt).
    Returns (list[dict]|None, list[str]): rows (item_name, amount, expense_date, ledger_name, main_category) and matched keywords.
    """
    if not client or not settings or not user_prompt or not isinstance(user_prompt, str):
        return None, []
    prompt_lower = user_prompt.lower().strip()
    matched = [kw for kw in EXPENSE_INVESTIGATOR_KEYWORDS if kw in prompt_lower]
    if not matched:
        return None, []
    excl = exclude_ledgers if exclude_ledgers is not None else parse_excluded_ledgers(user_prompt)
    try:
        pid = getattr(settings, "PROJECT_ID", "")
        ds = getattr(settings, "DATASET_ID", "")
        table = getattr(settings, "TABLE_EXPENSES", "expenses_master")
        if not pid or not ds:
            return None, matched
        conditions = []
        for kw in matched:
            esc = str(kw).replace("'", "''")
            pct = f"%{esc}%"
            conditions.append(f"(LOWER(COALESCE(CAST(item_name AS STRING),'')) LIKE '{pct}' OR LOWER(COALESCE(CAST(category AS STRING),'')) LIKE '{pct}' OR LOWER(COALESCE(CAST(ledger_name AS STRING),'')) LIKE '{pct}' OR LOWER(COALESCE(CAST(main_category AS STRING),'')) LIKE '{pct}')")
        where_clause = " OR ".join(conditions)
        tw = parse_time_window(user_prompt)
        if tw[0]:
            where_clause = f"({where_clause}) AND {tw[0]}"
        exclude_cond = ""
        for ex in excl:
            e = str(ex).replace("'", "''")
            exclude_cond += f" AND LOWER(COALESCE(CAST(ledger_name AS STRING), CAST(category AS STRING),'')) NOT LIKE '%{e}%' AND LOWER(COALESCE(CAST(main_category AS STRING),'')) NOT LIKE '%{e}%'"
        limit = 30 if any(x in prompt_lower for x in ["all", "every", "each"]) else 10
        q = f"""
        SELECT item_name, amount, expense_date, COALESCE(ledger_name, category) AS ledger_name, COALESCE(main_category, '') AS main_category
        FROM `{pid}.{ds}.{table}`
        WHERE {where_clause} {exclude_cond}
        ORDER BY expense_date DESC
        LIMIT {limit}
        """
        df = client.query(q).to_dataframe()
    except Exception:
        try:
            exclude_cond = ""
            for ex in excl:
                e = str(ex).replace("'", "''")
                exclude_cond += f" AND LOWER(COALESCE(CAST(category AS STRING),'')) NOT LIKE '%{e}%'"
            conditions = []
            for kw in matched:
                esc = str(kw).replace("'", "''")
                pct = f"%{esc}%"
                conditions.append(f"(LOWER(COALESCE(CAST(item_name AS STRING),'')) LIKE '{pct}' OR LOWER(COALESCE(CAST(category AS STRING),'')) LIKE '{pct}')")
            where_clause = " OR ".join(conditions)
            tw = parse_time_window(user_prompt)
            if tw[0]:
                where_clause = f"({where_clause}) AND {tw[0]}"
            limit = 30 if any(x in prompt_lower for x in ["all", "every", "each"]) else 10
            q = f"""
            SELECT item_name, amount, expense_date, category AS ledger_name, '' AS main_category
            FROM `{pid}.{ds}.{table}`
            WHERE {where_clause} {exclude_cond}
            ORDER BY expense_date DESC LIMIT {limit}
            """
            df = client.query(q).to_dataframe()
        except Exception:
            return None, matched
    if df.empty:
        return [], matched
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "item_name": str(r.get("item_name", "") or ""),
            "amount": float(r.get("amount", 0) or 0),
            "expense_date": str(r.get("expense_date", "")),
            "ledger_name": str(r.get("ledger_name", "") or ""),
            "main_category": str(r.get("main_category", "") or ""),
        })
    return rows, matched


def _tag_category(item_name: str, ledger_name: str, main_category: str) -> str:
    """Tag as Core_Bill, Contingency, or Maintenance from Explanation (item_name) and Reason (ledger/category)."""
    text = " ".join([str(x or "") for x in [item_name, ledger_name, main_category]]).lower()
    if CONTINGENCY_PATTERNS.search(text):
        return "Contingency"
    if MAINTENANCE_PATTERNS.search(text):
        return "Maintenance"
    if CORE_BILL_PATTERNS.search(text):
        return "Core_Bill"
    return "Other"


def heuristic_filter_expenses(client, settings, user_prompt: str, exclude_ledgers=None):
    """
    Heuristic Filter: reads Explanation (item_name) and Reason (category/ledger_name) for
    HEURISTIC_FILTER_KEYWORDS. Returns (list[dict], list[str]): rows with "category_tag"
    (Core_Bill, Contingency, Maintenance, Other) and matched keywords.
    """
    if not client or not settings or not user_prompt or not isinstance(user_prompt, str):
        return [], []
    prompt_lower = user_prompt.lower().strip()
    matched = [kw for kw in HEURISTIC_FILTER_KEYWORDS if kw in prompt_lower]
    # Also match if user asks about "electricity", "power", "category", "core", "contingency"
    if any(x in prompt_lower for x in ["electricity", "electric", "power", "diesel", "generator", "eb", "category", "core bill", "contingency", "main utility"]):
        matched = matched or ["eb", "electric", "diesel", "generator"]  # default forensic set
    if not matched:
        return [], []
    excl = exclude_ledgers if exclude_ledgers is not None else parse_excluded_ledgers(user_prompt)
    try:
        pid = getattr(settings, "PROJECT_ID", "")
        ds = getattr(settings, "DATASET_ID", "")
        table = getattr(settings, "TABLE_EXPENSES", "expenses_master")
        if not pid or not ds:
            return [], matched
        # Search in item_name (Explanation) and category/ledger_name (Reason)
        conditions = []
        for kw in matched:
            esc = str(kw).replace("'", "''")
            pct = f"%{esc}%"
            conditions.append(f"(LOWER(COALESCE(CAST(item_name AS STRING),'')) LIKE '{pct}' OR LOWER(COALESCE(CAST(category AS STRING),'')) LIKE '{pct}' OR LOWER(COALESCE(CAST(ledger_name AS STRING),'')) LIKE '{pct}' OR LOWER(COALESCE(CAST(main_category AS STRING),'')) LIKE '{pct}')")
        base = " OR ".join(conditions)
        tw = parse_time_window(user_prompt)
        where_clause = f"({base}) AND {tw[0]}" if tw[0] else f"({base})"
        exclude_cond = ""
        for ex in excl:
            e = str(ex).replace("'", "''")
            exclude_cond += f" AND LOWER(COALESCE(CAST(ledger_name AS STRING), CAST(category AS STRING),'')) NOT LIKE '%{e}%' AND LOWER(COALESCE(CAST(main_category AS STRING),'')) NOT LIKE '%{e}%'"
        q = f"""
        SELECT item_name, amount, expense_date, COALESCE(ledger_name, category) AS ledger_name, COALESCE(main_category, '') AS main_category
        FROM `{pid}.{ds}.{table}`
        WHERE {where_clause} {exclude_cond}
        ORDER BY expense_date DESC
        LIMIT 100
        """
        df = client.query(q).to_dataframe()
    except Exception:
        return [], matched
    if df.empty:
        return [], matched
    rows = []
    for _, r in df.iterrows():
        item_name = str(r.get("item_name", "") or "")
        ledger = str(r.get("ledger_name", "") or "")
        main = str(r.get("main_category", "") or "")
        tag = _tag_category(item_name, ledger, main)
        rows.append({
            "item_name": item_name,
            "amount": float(r.get("amount", 0) or 0),
            "expense_date": str(r.get("expense_date", "")),
            "ledger_name": ledger,
            "main_category": main,
            "category_tag": tag,
        })
    return rows, matched


def get_categorized_table(rows_with_tag, format_as="md"):
    """
    Build Categorized Table: Core Bill vs Contingency vs Maintenance.
    rows_with_tag: list of dicts with category_tag. format_as: "md" | "dict".
    Returns markdown string or dict { "core_bill": [], "contingency": [], "maintenance": [], "other": [] }.
    """
    core, cont, maint, other = [], [], [], []
    for r in rows_with_tag:
        t = (r.get("category_tag") or "Other").strip()
        if t == "Core_Bill":
            core.append(r)
        elif t == "Contingency":
            cont.append(r)
        elif t == "Maintenance":
            maint.append(r)
        else:
            other.append(r)
    if format_as == "dict":
        return {"core_bill": core, "contingency": cont, "maintenance": maint, "other": other}
    lines = ["### Categorized Table (Core Bill vs Contingency vs Maintenance)", ""]
    for label, rs in [("**Group A (Main Utility / Core Bill)**", core), ("**Group B (Power Contingency)**", cont), ("**Group C (Maintenance)**", maint)]:
        if not rs:
            continue
        lines.append(f"{label}")
        lines.append("| Item | Amount | Date | Ledger |")
        lines.append("|------|--------|------|--------|")
        for r in rs:
            iname = (r.get("item_name") or "").replace("|", "\\|")
            ledger = (r.get('ledger_name') or '').replace('|', '\\|')
            lines.append(f"| {iname} | {r.get('amount',0):,.2f} | {r.get('expense_date','')} | {ledger} |")
        lines.append("")
    if other and len(other) <= 20:
        lines.append("**Other**")
        lines.append("| Item | Amount | Date | Ledger |")
        lines.append("|------|--------|------|--------|")
        for r in other[:20]:
            iname = (r.get("item_name") or "").replace("|", "\\|")
            ledger = (r.get('ledger_name') or '').replace('|', '\\|')
            lines.append(f"| {iname} | {r.get('amount',0):,.2f} | {r.get('expense_date','')} | {ledger} |")
    return "\n".join(lines).strip()


_CANNOT_PATTERNS = [
    r"i (?:don't|do not) know",
    r"i (?:can't|cannot) (?:answer|provide|find|determine|access)",
    r"i(?:'m| am) (?:unable|not able) to",
    r"i (?:do not|don't) have (?:access|data|information|the)",
    r"missing data",
    r"no data (?:available|found)",
    r"could not find",
    r"(?:data|information) (?:is )?not available",
    r"don't have access",
    r"logic gap",
    r"cannot answer",
    r"limited information",
    r"can't (?:determine|find|answer|provide)",
    r"cannot (?:determine|find|answer|provide)",
    r"not able to (?:find|determine|answer|provide)",
    r"i have no (?:data|information|access)",
    r"no information (?:available|in)",
    r"unable to (?:find|determine|answer|retrieve)",
    r"i(?:'m| am) (?:sorry|unable).*(?:don't|do not|cannot|can't)",
    r"not (?:enough|sufficient) data",
]


def is_cannot_answer_response(text: str) -> bool:
    if not text or not isinstance(text, str):
        return False
    t = text.lower().strip()
    for p in _CANNOT_PATTERNS:
        if re.search(p, t, re.I):
            return True
    return False


def maybe_log_logic_gap(client, s, user_query: str, response: str) -> None:
    """
    If the response indicates the AI could not answer, log to dev_evolution_log.
    No-op otherwise. Safe to call every time (no duplicate detection).
    """
    if not client or not s or not user_query or not response:
        return
    if not is_cannot_answer_response(response):
        return
    logic_gap = "AI responded with inability to answer or missing data/logic."
    spec = (
        f"Support for: {user_query[:500]}. "
        "Suggested: add schema/tables, extend query engine, or enhance AI context."
    )
    log_logic_gap(client, s, user_query[:8000], logic_gap, spec)
