"""
TITAN Expense Analysis Engine: Trend tables, exclude ledgers, Employee & Paid From,
3-month trend, CRITICAL ANOMALY, and Ledger misspelling detection (IOT).
"""
import re
import difflib
from datetime import date, timedelta

# Canonical ledger names for misspelling detection (IOT / Ledger Normalization)
CANONICAL_LEDGERS = [
    "Electricity", "Rent", "Salary", "House Keeping", "Housekeeping",
    "Repairs", "Maintenance", "Staff", "Office", "Miscellaneous", "Uncategorized",
]


def detect_ledger_misspellings(ledger_names):
    """
    If a ledger is not in CANONICAL_LEDGERS but is similar (e.g. "Electrisity" ~ "Electricity"),
    return [(raw, suggested_canonical), ...]. Uses difflib.get_close_matches (cutoff=0.8).
    """
    if not ledger_names:
        return []
    out = []
    seen = set()
    for n in ledger_names:
        n = (n or "").strip()
        if not n or n in CANONICAL_LEDGERS:
            continue
        if n in seen:
            continue
        matches = difflib.get_close_matches(n, CANONICAL_LEDGERS, n=1, cutoff=0.8)
        if matches:
            out.append((n, matches[0]))
            seen.add(n)
    return out


def parse_excluded_ledgers(prompt: str):
    """
    Extract ledger/expense names to exclude from prompt. Heuristic for:
    "ignore X, Y and Z", "exclude A and B", "without P, Q", "except X".
    Returns list of strings (lowercase for matching).
    """
    if not prompt or not isinstance(prompt, str):
        return []
    out = []
    t = prompt.lower()
    # (?:ignore|exclude|without|except)\s+([^.?!?]+?)(?:\s+and\s+|\s*,\s*|\s+for\s+|\s+to\s+calculate|\.|$)
    for m in re.finditer(r"(?:ignore|exclude|without|except)\s+([^.?!?\n]+?)(?:\s+and\s+calculate|\s+for\s+(?:p&l|pl|profit|loss)|\s+to\s+calc|\.|\?|$)", t, re.I):
        chunk = m.group(1)
        for part in re.split(r"\s+and\s+|\s*,\s*", chunk):
            p = part.strip().strip(".,")
            if p and len(p) > 1:
                out.append(p)
    return list(dict.fromkeys(out))  # dedup


def _table(client, settings):
    pid = getattr(settings, "PROJECT_ID", "")
    ds = getattr(settings, "DATASET_ID", "")
    return f"`{pid}.{ds}.{getattr(settings, 'TABLE_EXPENSES', 'expenses_master')}`"


def _sales_table(client, settings):
    pid = getattr(settings, "PROJECT_ID", "")
    ds = getattr(settings, "DATASET_ID", "")
    return f"`{pid}.{ds}.{getattr(settings, 'TABLE_SALES_PARSED', 'sales_items_parsed')}`"


def calculate_discretionary_spend(client, settings, expense_amount: float, days_available: int = None):
    """
    Budget/Trip Strategy Engine: compute the "Sales Push" (extra revenue) required to cover
    the given expense, based on the last 7 days' profit margin.
    Profit margin = (Revenue - Expenses) / Revenue. Sales Push = expense_amount / profit_margin.
    If days_available is set, also returns sales_push_per_day = sales_push / days_available.
    Returns: { "sales_push", "sales_push_per_day", "profit_margin_pct", "revenue_7d", "expenses_7d", "net_7d", "error" }.
    """
    out = {"sales_push": None, "sales_push_per_day": None, "profit_margin_pct": None, "revenue_7d": 0.0, "expenses_7d": 0.0, "net_7d": 0.0, "error": None}
    if not client or not settings or expense_amount is None or (isinstance(expense_amount, (int, float)) and expense_amount <= 0):
        out["error"] = "Invalid expense_amount (must be > 0)."
        return out
    expense_amount = float(expense_amount)
    try:
        tbl = _table(client, settings)
        sales_tbl = _sales_table(client, settings)
        q = f"""
        SELECT
          (SELECT COALESCE(SUM(total_revenue), 0) FROM {sales_tbl} WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) AS rev,
          (SELECT COALESCE(SUM(amount), 0) FROM {tbl} WHERE expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) AS exp
        """
        df = client.query(q).to_dataframe()
        if df.empty:
            out["error"] = "No data for last 7 days."
            return out
        rev = float(df.iloc[0].get("rev") or 0)
        exp = float(df.iloc[0].get("exp") or 0)
        out["revenue_7d"], out["expenses_7d"] = rev, exp
        out["net_7d"] = rev - exp
        if rev <= 0:
            out["error"] = "No revenue in last 7 days; cannot compute profit margin."
            return out
        margin = (rev - exp) / rev
        out["profit_margin_pct"] = round(margin * 100, 2)
        if margin <= 0:
            out["error"] = "Profit margin is zero or negative; Sales Push would be infinite. Control costs first."
            return out
        out["sales_push"] = round(expense_amount / margin, 2)
        if isinstance(days_available, int) and days_available > 0:
            out["sales_push_per_day"] = round(out["sales_push"] / days_available, 2)
    except Exception as e:
        out["error"] = str(e)
    return out


# --- Power: Contingency vs EB (last N days) ---
_CONTINGENCY_P = re.compile(r"\b(diesel|diesal|disal|generator|gen\b|motor|eb man)\b", re.I)
_EB_ONLY_P = re.compile(r"\b(eb|electric|electricity)\b", re.I)


def _power_tag(item_name: str, ledger_name: str, main_category: str) -> str:
    text = " ".join([str(x or "") for x in [item_name, ledger_name, main_category]]).lower()
    if _CONTINGENCY_P.search(text):
        return "Contingency"
    if _EB_ONLY_P.search(text):
        return "EB_Bill"
    return "Other"


def get_power_contingency_vs_eb(client, settings, days: int = 30):
    """Last N days: contingency (diesel/generator/motor) vs EB. Returns { contingency_total, eb_total, contingency_entries, eb_entries, error }."""
    out = {"contingency_total": 0.0, "eb_total": 0.0, "contingency_entries": [], "eb_entries": [], "error": None}
    if not client or not settings:
        out["error"] = "Missing client or settings."
        return out
    days = max(1, int(days))
    try:
        tbl = _table(client, settings)
        w = (
            "expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL %d DAY) AND ("
            "  LOWER(COALESCE(CAST(item_name AS STRING),'')) LIKE '%%eb%%' OR LOWER(COALESCE(CAST(item_name AS STRING),'')) LIKE '%%electric%%'"
            "  OR LOWER(COALESCE(CAST(item_name AS STRING),'')) LIKE '%%diesel%%' OR LOWER(COALESCE(CAST(item_name AS STRING),'')) LIKE '%%diesal%%'"
            "  OR LOWER(COALESCE(CAST(item_name AS STRING),'')) LIKE '%%generator%%' OR LOWER(COALESCE(CAST(item_name AS STRING),'')) LIKE '%%motor%%'"
            "  OR LOWER(COALESCE(CAST(ledger_name AS STRING),'')) LIKE '%%electric%%' OR LOWER(COALESCE(CAST(ledger_name AS STRING),'')) LIKE '%%diesel%%'"
            "  OR LOWER(COALESCE(CAST(ledger_name AS STRING),'')) LIKE '%%generator%%' OR LOWER(COALESCE(CAST(category AS STRING),'')) LIKE '%%electric%%'"
            "  OR LOWER(COALESCE(CAST(category AS STRING),'')) LIKE '%%diesel%%' OR LOWER(COALESCE(CAST(category AS STRING),'')) LIKE '%%generator%%' )"
        ) % days
        q = "SELECT item_name, amount, expense_date, COALESCE(ledger_name, category) AS ledger_name, COALESCE(main_category, '') AS main_category FROM %s WHERE %s ORDER BY expense_date DESC" % (tbl, w)
        df = client.query(q).to_dataframe()
    except Exception as e:
        out["error"] = str(e)
        return out
    if df.empty:
        return out
    for _, r in df.iterrows():
        item = str(r.get("item_name") or "")
        ledger = str(r.get("ledger_name") or "")
        main = str(r.get("main_category") or "")
        amt = float(r.get("amount") or 0)
        dt = str(r.get("expense_date") or "")
        tag = _power_tag(item, ledger, main)
        rec = {"item_name": item, "amount": amt, "expense_date": dt, "ledger_name": ledger}
        if tag == "Contingency":
            out["contingency_entries"].append(rec)
            out["contingency_total"] += amt
        elif tag == "EB_Bill":
            out["eb_entries"].append(rec)
            out["eb_total"] += amt
    out["contingency_total"] = round(out["contingency_total"], 2)
    out["eb_total"] = round(out["eb_total"], 2)
    return out


def _ledger_col(use_legacy: bool):
    if use_legacy:
        return "COALESCE(CAST(category AS STRING),'')"
    return "COALESCE(CAST(ledger_name AS STRING), CAST(category AS STRING),'')"


def run_expense_trend_analysis(client, settings, exclude_ledgers=None, ledger_focus=None, months=2):
    """
    Trend: current vs last month by ledger, expense/revenue ratio.
    exclude_ledgers: list of substrings to exclude (case-insensitive).
    ledger_focus: e.g. "Electricity" to emphasize one ledger.
    Returns: { by_ledger, total_curr, total_last, revenue_curr, revenue_last, curr_ratio, last_ratio, excluded_note }
    Never raises; returns empty dict or partial on error.
    """
    out = {"by_ledger": [], "total_curr": 0.0, "total_last": 0.0, "total_m2": 0.0,
           "revenue_curr": 0.0, "revenue_last": 0.0, "revenue_m2": 0.0, "revenue_pct_change": 0.0,
           "curr_ratio": 0.0, "last_ratio": 0.0, "excluded_note": ""}
    exclude_ledgers = exclude_ledgers or []
    try:
        tbl = _table(client, settings)
        sales_tbl = _sales_table(client, settings)
        use_legacy = False

        # Build exclude condition for ledger
        exclude_cond = ""
        if exclude_ledgers:
            conds = []
            for ex in exclude_ledgers:
                esc = str(ex).replace("'", "''")
                conds.append(f"LOWER(COALESCE(CAST(ledger_name AS STRING), CAST(category AS STRING),'')) NOT LIKE '%{esc}%' AND LOWER(COALESCE(CAST(main_category AS STRING),'')) NOT LIKE '%{esc}%'")
            if conds:
                exclude_cond = " AND " + " AND ".join(conds)
                out["excluded_note"] = f"Excluded ledgers: {', '.join(exclude_ledgers)}."

        # 3-month: current, m1 (last), m2 (2 months ago)
        cur_from = "DATE_TRUNC(CURRENT_DATE(), MONTH)"
        cur_to   = "DATE_ADD(DATE_TRUNC(CURRENT_DATE(), MONTH), INTERVAL 1 MONTH)"
        m1_from  = "DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH), MONTH)"
        m1_to    = "DATE_TRUNC(CURRENT_DATE(), MONTH)"
        m2_from  = "DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH), MONTH)"
        m2_to    = "DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH), MONTH)"
        try:
            ledger_expr = _ledger_col(False)
            q = f"""
            WITH cur AS (SELECT {ledger_expr} AS ledger, SUM(amount) AS s FROM {tbl} WHERE expense_date >= {cur_from} AND expense_date < {cur_to} {exclude_cond} GROUP BY 1),
                 m1  AS (SELECT {ledger_expr} AS ledger, SUM(amount) AS s FROM {tbl} WHERE expense_date >= {m1_from} AND expense_date < {m1_to} {exclude_cond} GROUP BY 1),
                 m2  AS (SELECT {ledger_expr} AS ledger, SUM(amount) AS s FROM {tbl} WHERE expense_date >= {m2_from} AND expense_date < {m2_to} {exclude_cond} GROUP BY 1)
            SELECT COALESCE(cur.ledger, m1.ledger, m2.ledger) AS ledger_name,
                   COALESCE(cur.s, 0) AS curr_spend, COALESCE(m1.s, 0) AS last_spend, COALESCE(m2.s, 0) AS m2_spend
            FROM cur FULL OUTER JOIN m1 ON cur.ledger = m1.ledger
            FULL OUTER JOIN m2 ON COALESCE(cur.ledger, m1.ledger) = m2.ledger
            WHERE COALESCE(cur.ledger, m1.ledger, m2.ledger) IS NOT NULL AND COALESCE(cur.ledger, m1.ledger, m2.ledger) != ''
            ORDER BY curr_spend DESC LIMIT 30
            """
            df = client.query(q).to_dataframe()
        except Exception:
            ledger_expr = _ledger_col(True)
            exclude_cond = ""
            if exclude_ledgers:
                conds = [f"LOWER(COALESCE(CAST(category AS STRING),'')) NOT LIKE '%{str(ex).replace(chr(39), chr(39)+chr(39))}%'" for ex in exclude_ledgers]
                exclude_cond = " AND " + " AND ".join(conds)
            q = f"""
            WITH cur AS (SELECT {ledger_expr} AS ledger, SUM(amount) AS s FROM {tbl} WHERE expense_date >= {cur_from} AND expense_date < {cur_to} {exclude_cond} GROUP BY 1),
                 m1  AS (SELECT {ledger_expr} AS ledger, SUM(amount) AS s FROM {tbl} WHERE expense_date >= {m1_from} AND expense_date < {m1_to} {exclude_cond} GROUP BY 1),
                 m2  AS (SELECT {ledger_expr} AS ledger, SUM(amount) AS s FROM {tbl} WHERE expense_date >= {m2_from} AND expense_date < {m2_to} {exclude_cond} GROUP BY 1)
            SELECT COALESCE(cur.ledger, m1.ledger, m2.ledger) AS ledger_name, COALESCE(cur.s, 0) AS curr_spend, COALESCE(m1.s, 0) AS last_spend, COALESCE(m2.s, 0) AS m2_spend
            FROM cur FULL OUTER JOIN m1 ON cur.ledger = m1.ledger
            FULL OUTER JOIN m2 ON COALESCE(cur.ledger, m1.ledger) = m2.ledger
            WHERE COALESCE(cur.ledger, m1.ledger, m2.ledger) IS NOT NULL AND COALESCE(cur.ledger, m1.ledger, m2.ledger) != ''
            ORDER BY curr_spend DESC LIMIT 30
            """
            df = client.query(q).to_dataframe()

        try:
            qtot = f"""
            SELECT
              SUM(CASE WHEN expense_date >= {cur_from} AND expense_date < {cur_to} THEN amount ELSE 0 END) AS total_curr,
              SUM(CASE WHEN expense_date >= {m1_from} AND expense_date < {m1_to} THEN amount ELSE 0 END) AS total_last,
              SUM(CASE WHEN expense_date >= {m2_from} AND expense_date < {m2_to} THEN amount ELSE 0 END) AS total_m2
            FROM {tbl} WHERE 1=1 {exclude_cond}
            """
            tot = client.query(qtot).to_dataframe()
            if not tot.empty:
                out["total_curr"] = float(tot.iloc[0].get("total_curr") or 0)
                out["total_last"] = float(tot.iloc[0].get("total_last") or 0)
                out["total_m2"]   = float(tot.iloc[0].get("total_m2") or 0)
        except Exception:
            pass

        try:
            qrev = f"""
            SELECT
              SUM(CASE WHEN bill_date >= {cur_from} AND bill_date < {cur_to} THEN total_revenue ELSE 0 END) AS rev_cur,
              SUM(CASE WHEN bill_date >= {m1_from} AND bill_date < {m1_to} THEN total_revenue ELSE 0 END) AS rev_last,
              SUM(CASE WHEN bill_date >= {m2_from} AND bill_date < {m2_to} THEN total_revenue ELSE 0 END) AS rev_m2
            FROM {sales_tbl}
            """
            rev = client.query(qrev).to_dataframe()
            if not rev.empty:
                out["revenue_curr"] = float(rev.iloc[0].get("rev_cur") or 0)
                out["revenue_last"] = float(rev.iloc[0].get("rev_last") or 0)
                out["revenue_m2"]   = float(rev.iloc[0].get("rev_m2") or 0)
        except Exception:
            pass

        rev_last = out["revenue_last"] or 0
        out["revenue_pct_change"] = ((out["revenue_curr"] - rev_last) / rev_last * 100) if rev_last and rev_last != 0 else 0.0

        if out["revenue_curr"] and out["revenue_curr"] > 0:
            out["curr_ratio"] = (out["total_curr"] / out["revenue_curr"]) * 100
        if out["revenue_last"] and out["revenue_last"] > 0:
            out["last_ratio"] = (out["total_last"] / out["revenue_last"]) * 100

        rev_pct = out["revenue_pct_change"]
        for _, r in df.iterrows():
            ln = str(r.get("ledger_name", "") or "")
            cur_s = float(r.get("curr_spend", 0) or 0)
            lst_s = float(r.get("last_spend", 0) or 0)
            m2_s  = float(r.get("m2_spend", 0) or 0)
            pct_chg = ((cur_s - lst_s) / lst_s * 100) if lst_s and lst_s != 0 else (100.0 if cur_s else 0.0)
            cur_pct = (cur_s / out["revenue_curr"] * 100) if out["revenue_curr"] and out["revenue_curr"] > 0 else 0.0
            lst_pct = (lst_s / out["revenue_last"] * 100) if out["revenue_last"] and out["revenue_last"] > 0 else 0.0
            anomaly = ""
            if rev_pct <= -10 and pct_chg >= 10:
                anomaly = "CRITICAL ANOMALY"
            out["by_ledger"].append({
                "ledger_name": ln, "curr_spend": cur_s, "last_spend": lst_s, "m2_spend": m2_s,
                "pct_change": round(pct_chg, 1), "curr_pct_rev": round(cur_pct, 2), "last_pct_rev": round(lst_pct, 2),
                "anomaly": anomaly,
            })
    except Exception:
        pass
    return out


def run_employee_payment_analysis(client, settings, days=7):
    """
    Who (staff_name) and How (payment_mode): sum(amount), pct of total.
    Returns: [ {staff_name, payment_mode, amount, pct_of_total}, ... ]
    """
    out = []
    try:
        tbl = _table(client, settings)
        try:
            q = f"""
            WITH t AS (
              SELECT COALESCE(CAST(staff_name AS STRING), 'Unknown') AS staff_name,
                     COALESCE(CAST(payment_mode AS STRING), 'Unknown') AS payment_mode,
                     SUM(amount) AS amount
              FROM {tbl}
              WHERE expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {int(days)} DAY)
              GROUP BY 1, 2
            ),
            tot AS (SELECT SUM(amount) AS s FROM t)
            SELECT t.staff_name, t.payment_mode, t.amount, ROUND(100.0 * t.amount / NULLIF(tot.s, 0), 1) AS pct_of_total
            FROM t, tot
            ORDER BY t.amount DESC
            LIMIT 50
            """
            df = client.query(q).to_dataframe()
        except Exception:
            # staff_name may not exist
            q = f"""
            WITH t AS (
              SELECT COALESCE(CAST(payment_mode AS STRING), 'Unknown') AS payment_mode, SUM(amount) AS amount
              FROM {tbl}
              WHERE expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {int(days)} DAY)
              GROUP BY 1
            ),
            tot AS (SELECT SUM(amount) AS s FROM t)
            SELECT 'Unknown' AS staff_name, t.payment_mode, t.amount, ROUND(100.0 * t.amount / NULLIF(tot.s, 0), 1) AS pct_of_total
            FROM t, tot ORDER BY t.amount DESC LIMIT 50
            """
            df = client.query(q).to_dataframe()

        for _, r in df.iterrows():
            out.append({
                "staff_name": str(r.get("staff_name", "") or "Unknown"),
                "payment_mode": str(r.get("payment_mode", "") or "Unknown"),
                "amount": float(r.get("amount", 0) or 0),
                "pct_of_total": float(r.get("pct_of_total", 0) or 0),
            })
    except Exception:
        pass
    return out


def format_trend_markdown(d, ledger_focus=None):
    """3-month markdown: Ledger | This Month | Last Month | 2 Mo Ago | % Change | % Rev (This) | % Rev (Last) | Flag (CRITICAL ANOMALY)."""
    if not d or not d.get("by_ledger"):
        return ""
    lines = ["| Ledger | This Month (₹) | Last Month (₹) | 2 Mo Ago (₹) | % Change | % Rev (This) | % Rev (Last) | Flag |",
             "|--------|----------------|----------------|--------------|----------|--------------|--------------|------|"]
    for r in d["by_ledger"]:
        ln = (r.get("ledger_name") or "").replace("|", "\\|")
        cur = r.get("curr_spend", 0) or 0
        lst = r.get("last_spend", 0) or 0
        m2 = r.get("m2_spend", 0) or 0
        chg = r.get("pct_change", 0) or 0
        cp = r.get("curr_pct_rev", 0) or 0
        lp = r.get("last_pct_rev", 0) or 0
        anom = r.get("anomaly") or ""
        lines.append(f"| {ln} | {cur:,.2f} | {lst:,.2f} | {m2:,.2f} | {chg:+.1f}% | {cp}% | {lp}% | {anom} |")
    tot_cur = d.get("total_curr", 0) or 0
    tot_last = d.get("total_last", 0) or 0
    tot_m2 = d.get("total_m2", 0) or 0
    rev_cur = d.get("revenue_curr", 0) or 0
    rev_last = d.get("revenue_last", 0) or 0
    rev_m2 = d.get("revenue_m2", 0) or 0
    rat_cur = d.get("curr_ratio", 0) or 0
    rat_last = d.get("last_ratio", 0) or 0
    rev_chg = d.get("revenue_pct_change", 0) or 0
    lines.append(f"| **Total** | **{tot_cur:,.2f}** | **{tot_last:,.2f}** | **{tot_m2:,.2f}** | | **{rat_cur:.2f}%** | **{rat_last:.2f}%** | |")
    header = "### Trend: Expense by Ledger (3 Months)\n"
    if d.get("excluded_note"):
        header += f"{d['excluded_note']}\n"
    header += f"Revenue: This ₹{rev_cur:,.2f} | Last ₹{rev_last:,.2f} | 2 Mo Ago ₹{rev_m2:,.2f}. Revenue Δ: {rev_chg:+.1f}%. Expense/Revenue: {rat_cur:.2f}% (this) vs {rat_last:.2f}% (last).\n"
    return header + "\n".join(lines)


def format_employee_payment_markdown(rows, days=7):
    """| Employee | Paid From | Amount (₹) | % of Total |"""
    if not rows:
        return ""
    lines = ["### Who & How: Employee and Paid From\n", "| Employee | Paid From | Amount (₹) | % of Total |", "|----------|-----------|------------|------------|"]
    for r in rows:
        s = (r.get("staff_name") or "Unknown").replace("|", "\\|")
        p = (r.get("payment_mode") or "Unknown").replace("|", "\\|")
        a = r.get("amount", 0) or 0
        pc = r.get("pct_of_total", 0) or 0
        lines.append(f"| {s} | {p} | {a:,.2f} | {pc}% |")
    return "\n".join(lines) + f"\n*Last {days} days.*"
