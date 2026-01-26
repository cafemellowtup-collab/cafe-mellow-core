"""
TITAN Dashboard Pillar: Executive metrics, Revenue vs Expenses, Sentinel health, AI Observations.
"""
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
from utils.bq_guardrails import query_to_df


def get_revenue_expenses_data(client, s, days=30):
    """
    Returns dict: { dates: [], revenue: [], expenses: [], net: [] } for Plotly.
    Uses sales_items_parsed and expenses_master.
    """
    s = s or settings
    pid, ds = s.PROJECT_ID, s.DATASET_ID
    try:
        qr = f"""
        SELECT bill_date AS dt, SUM(total_revenue) AS val FROM `{pid}.{ds}.sales_items_parsed`
        WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {int(days)} DAY)
        GROUP BY bill_date
        """
        qe = f"""
        SELECT expense_date AS dt, SUM(amount) AS val FROM `{pid}.{ds}.expenses_master`
        WHERE expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {int(days)} DAY)
        GROUP BY expense_date
        """
        dr, _ = query_to_df(client, s, qr, purpose=f"dashboard.revenue_last_{int(days)}d")
        de, _ = query_to_df(client, s, qe, purpose=f"dashboard.expenses_last_{int(days)}d")
        d1 = dr[["dt"]].copy() if not dr.empty and "dt" in dr.columns else pd.DataFrame(columns=["dt"])
        d2 = de[["dt"]].copy() if not de.empty and "dt" in de.columns else pd.DataFrame(columns=["dt"])
        all_d = pd.concat([d1, d2]).drop_duplicates().sort_values("dt").reset_index(drop=True)
        if all_d.empty:
            return {"dates": [], "revenue": [], "expenses": [], "net": []}
        rev_map = dict(zip(dr["dt"].astype(str), dr["val"])) if not dr.empty and "dt" in dr.columns and "val" in dr.columns else {}
        exp_map = dict(zip(de["dt"].astype(str), de["val"])) if not de.empty and "dt" in de.columns and "val" in de.columns else {}
        dates = []
        revenue = []
        expenses = []
        for _, r in all_d.iterrows():
            d = r["dt"]
            ds = str(d)
            dates.append(ds)
            revenue.append(float(rev_map.get(ds, 0)))
            expenses.append(float(exp_map.get(ds, 0)))
        net = [r - e for r, e in zip(revenue, expenses)]
        return {"dates": dates, "revenue": revenue, "expenses": expenses, "net": net}
    except Exception as e:
        raise RuntimeError(f"get_revenue_expenses_data failed: {e}") from e


def get_sentinel_health(client, s, limit=20):
    """
    Returns list of task dicts from ai_task_queue (Pending) for Sentinel health.
    Keys: created_at, task_type, item_involved, description, priority, department, status.
    """
    s = s or settings
    pid, ds = s.PROJECT_ID, s.DATASET_ID
    try:
        q = f"""
        SELECT created_at, task_type, item_involved, description, priority, department, status
        FROM `{pid}.{ds}.ai_task_queue`
        WHERE status = 'Pending'
        ORDER BY created_at DESC
        LIMIT {int(limit)}
        """
        df, _ = query_to_df(client, s, q, purpose=f"dashboard.sentinel_health_limit_{int(limit)}")
        return df.to_dict("records") if not df.empty else []
    except Exception as e:
        return []


def get_sync_freshness(client, s):
    """
    Returns dict: { "expenses": { "last_sync": datetime|None, "stale": bool }, "recipes": {...}, "purchases": {...}, "cash_ops": {...}, "wastage": {...} }.
    stale = True if last_sync is None or older than 24 hours.
    """
    s = s or settings
    pid, ds = s.PROJECT_ID, s.DATASET_ID
    sync_table = getattr(s, "TABLE_SYSTEM_SYNC_LOG", "system_sync_log")
    out = {}
    for sync_type in ("expenses", "recipes", "purchases", "cash_ops", "wastage"):
        out[sync_type] = {"last_sync": None, "stale": True}
    try:
        q = f"""
        SELECT sync_type, MAX(last_sync_ts) AS last_sync_ts
        FROM `{pid}.{ds}.{sync_table}`
        WHERE sync_type IN ('expenses','recipes','purchases','cash_ops','wastage') AND status = 'success'
        GROUP BY sync_type
        """
        df, _ = query_to_df(client, s, q, purpose="dashboard.sync_freshness")
        if df.empty:
            return out
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        for _, r in df.iterrows():
            st = str(r.get("sync_type", ""))
            if st not in out:
                continue
            ts = r.get("last_sync_ts")
            if ts is None:
                out[st] = {"last_sync": None, "stale": True}
            else:
                # ts may be timezone-aware or naive
                if hasattr(ts, "tzinfo") and ts.tzinfo:
                    pass
                else:
                    ts = ts.replace(tzinfo=timezone.utc) if hasattr(ts, "replace") else ts
                out[st] = {"last_sync": ts, "stale": ts < cutoff if ts else True}
    except Exception:
        pass
    return out


def get_anomaly_status(client, s, days=7):
    """
    Anomaly: Revenue down ≥10% AND Expense up ≥10% (vs prior period).
    Returns { "detected": bool, "rev_pct": float, "exp_pct": float, "msg": str }.
    """
    s = s or settings
    pid, ds = s.PROJECT_ID, s.DATASET_ID
    out = {"detected": False, "rev_pct": None, "exp_pct": None, "msg": ""}
    try:
        # Current period (last `days`) vs prior period
        q = f"""
        WITH curr AS (
          SELECT
            (SELECT COALESCE(SUM(total_revenue),0) FROM `{pid}.{ds}.sales_items_parsed` WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {int(days)} DAY)) AS rev,
            (SELECT COALESCE(SUM(amount),0) FROM `{pid}.{ds}.expenses_master` WHERE expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {int(days)} DAY)) AS exp
        ),
        prev AS (
          SELECT
            (SELECT COALESCE(SUM(total_revenue),0) FROM `{pid}.{ds}.sales_items_parsed` WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {int(days)*2} DAY) AND bill_date < DATE_SUB(CURRENT_DATE(), INTERVAL {int(days)} DAY)) AS rev,
            (SELECT COALESCE(SUM(amount),0) FROM `{pid}.{ds}.expenses_master` WHERE expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {int(days)*2} DAY) AND expense_date < DATE_SUB(CURRENT_DATE(), INTERVAL {int(days)} DAY)) AS exp
        )
        SELECT c.rev AS c_rev, c.exp AS c_exp, p.rev AS p_rev, p.exp AS p_exp
        FROM curr c, prev p
        """
        df, _ = query_to_df(client, s, q, purpose=f"dashboard.anomaly_status_{int(days)}d")
        if df.empty or (df["p_rev"].iloc[0] or 0) == 0 or (df["p_exp"].iloc[0] or 0) == 0:
            return out
        c_rev, c_exp = float(df["c_rev"].iloc[0] or 0), float(df["c_exp"].iloc[0] or 0)
        p_rev, p_exp = float(df["p_rev"].iloc[0] or 0), float(df["p_exp"].iloc[0] or 0)
        rev_pct = ((c_rev - p_rev) / p_rev * 100) if p_rev else 0
        exp_pct = ((c_exp - p_exp) / p_exp * 100) if p_exp else 0
        out["rev_pct"], out["exp_pct"] = round(rev_pct, 1), round(exp_pct, 1)
        if rev_pct <= -10 and exp_pct >= 10:
            out["detected"] = True
            out["msg"] = f"Revenue down {abs(rev_pct):.1f}% and Expenses up {exp_pct:.1f}% vs prior {int(days)} days."
    except Exception:
        pass
    return out


def _format_data_freshness(d):
    """Format date as 'Data available up to Jan 19' or '—' if None."""
    if d is None:
        return "—"
    try:
        if hasattr(d, "strftime"):
            return f"Data available up to {d.strftime('%b %d')}"
        s = str(d)[:10]
        if len(s) >= 10:
            from datetime import datetime
            dt = datetime.strptime(s, "%Y-%m-%d")
            return f"Data available up to {dt.strftime('%b %d')}"
    except Exception:
        pass
    return str(d)[:20] if d else "—"


def get_sync_status_matrix(client, s):
    """
    Returns list of { module, last_sync_time, data_freshness_date, data_freshness_label, triggered_by }.
    data_freshness_label: e.g. "Data available up to Jan 19".
    """
    s = s or settings
    pid, ds = s.PROJECT_ID, s.DATASET_ID
    sync_table = getattr(s, "TABLE_SYSTEM_SYNC_LOG", "system_sync_log")
    # Map sync_type -> (table, date_column) for freshness
    mod_map = {
        "expenses": (getattr(s, "TABLE_EXPENSES", "expenses_master"), "expense_date"),
        "recipes": (getattr(s, "TABLE_RECIPES", "recipes_sales_master"), None),
        "purchases": (getattr(s, "TABLE_PURCHASES", "purchases_master"), "invoice_date"),
        "cash_ops": (getattr(s, "TABLE_CASH", "cash_flow_master"), "entry_date"),
        "wastage": (getattr(s, "TABLE_WASTAGE", "wastage_log"), "wastage_date"),
    }
    out = []
    try:
        q = f"""
        SELECT sync_type, MAX(last_sync_ts) AS last_sync_ts,
               MAX(triggered_by) AS triggered_by
        FROM `{pid}.{ds}.{sync_table}`
        WHERE sync_type IN ('expenses','recipes','purchases','cash_ops','wastage') AND status = 'success'
        GROUP BY sync_type
        """
        df, _ = query_to_df(client, s, q, purpose="dashboard.sync_status_matrix")
        for _, r in df.iterrows():
            stype = str(r.get("sync_type", ""))
            tbl, date_col = mod_map.get(stype, (None, None))
            fresh = None
            if tbl and date_col:
                try:
                    q2 = f"SELECT MAX({date_col}) AS d FROM `{pid}.{ds}.{tbl}`"
                    df2, _ = query_to_df(client, s, q2, purpose=f"dashboard.data_freshness.{stype}")
                    if not df2.empty and df2["d"].iloc[0] is not None:
                        fresh = df2["d"].iloc[0]
                except Exception:
                    pass
            _tb = r.get("triggered_by")
            _triggered = str(_tb)[:50] if _tb else "—"
            out.append({
                "module": stype.replace("_", " ").title(),
                "last_sync_time": r.get("last_sync_ts"),
                "data_freshness_date": fresh,
                "data_freshness_label": _format_data_freshness(fresh),
                "triggered_by": _triggered,
            })
        # Ensure all modules appear
        for k in mod_map:
            if not any(x["module"].lower().replace(" ", "_") == k for x in out):
                out.append({"module": k.replace("_", " ").title(), "last_sync_time": None, "data_freshness_date": None, "data_freshness_label": "—", "triggered_by": "—"})
        out.sort(key=lambda x: (x["last_sync_time"] or datetime.min).__str__(), reverse=True)
    except Exception:
        for k, (_, _) in mod_map.items():
            out.append({"module": k.replace("_", " ").title(), "last_sync_time": None, "data_freshness_date": None, "data_freshness_label": "—", "triggered_by": "—"})
    return out


def get_ai_observations(client, s, limit=15):
    """
    Proactively analyze ai_task_queue and return "AI Observations" for the main dashboard.
    Returns list of { priority, title, description, count?, task_type? }.
    """
    s = s or settings
    pid, ds = s.PROJECT_ID, s.DATASET_ID
    obs = []
    try:
        # Summary by priority
        q = f"""
        SELECT priority, task_type, COUNT(*) AS cnt
        FROM `{pid}.{ds}.ai_task_queue`
        WHERE status = 'Pending'
        GROUP BY priority, task_type
        ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, cnt DESC
        LIMIT 10
        """
        df, _ = query_to_df(client, s, q, purpose="dashboard.ai_observations")
        for _, r in df.iterrows():
            obs.append({
                "priority": str(r.get("priority", "Medium")),
                "title": f"{r.get('task_type', 'Alert')} ({r.get('cnt', 0)})",
                "description": f"{int(r.get('cnt', 0))} pending {r.get('task_type', '')} — {r.get('priority', '')}",
                "count": int(r.get("cnt", 0)),
                "task_type": str(r.get("task_type", "")),
            })
        # If no tasks, add a healthy observation
        if not obs:
            obs.append({
                "priority": "Low",
                "title": "Sentinel healthy",
                "description": "No pending items in ai_task_queue.",
                "count": 0,
                "task_type": "health",
            })
    except Exception as e:
        raise RuntimeError(f"get_ai_observations failed: {e}") from e
    return obs[: int(limit)]
