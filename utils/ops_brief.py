import json
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from google.cloud import bigquery
from google.cloud.exceptions import NotFound


def _table_id(cfg) -> str:
    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    return f"{pid}.{ds}.ops_daily_briefs"


def ensure_table(client: bigquery.Client, cfg) -> None:
    table_id = _table_id(cfg)
    try:
        client.get_table(table_id)
        return
    except NotFound:
        schema = [
            bigquery.SchemaField("brief_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("version", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("payload_json", "STRING", mode="REQUIRED"),
        ]
        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(type_=bigquery.TimePartitioningType.DAY, field="brief_date")
        client.create_table(table)


def _table_exists(client: bigquery.Client, pid: str, ds: str, table: str) -> bool:
    try:
        q = f"SELECT 1 FROM `{pid}.{ds}.INFORMATION_SCHEMA.TABLES` WHERE table_name = '{table}' LIMIT 1"
        rows = list(client.query(q).result())
        return bool(rows)
    except Exception:
        return False


def _sales_table(cfg, client: bigquery.Client) -> str:
    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    if pid and ds and _table_exists(client, pid, ds, "sales_enhanced"):
        return "sales_enhanced"
    return getattr(cfg, "TABLE_SALES_PARSED", "sales_items_parsed")


def generate_brief(client: bigquery.Client, cfg, brief_date: Optional[date] = None) -> Dict[str, Any]:
    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    if not pid or not ds:
        raise ValueError("PROJECT_ID/DATASET_ID not configured")

    d = brief_date or (date.today() - timedelta(days=1))
    sales_table = _sales_table(cfg, client)

    last_week = d - timedelta(days=7)

    # -----------------
    # Data freshness
    # -----------------
    # We compute latest available dates so the brief can explain when data is missing/stale.
    latest_sales_date: Optional[str]
    latest_expenses_date: Optional[str]
    try:
        q = f"SELECT CAST(MAX(bill_date) AS STRING) AS d FROM `{pid}.{ds}.{sales_table}`"
        df = client.query(q).to_dataframe()
        latest_sales_date = str(df.iloc[0].get("d")) if (not df.empty and df.iloc[0].get("d")) else None
    except Exception:
        latest_sales_date = None

    try:
        q = f"SELECT CAST(MAX(expense_date) AS STRING) AS d FROM `{pid}.{ds}.expenses_master`"
        df = client.query(q).to_dataframe()
        latest_expenses_date = str(df.iloc[0].get("d")) if (not df.empty and df.iloc[0].get("d")) else None
    except Exception:
        latest_expenses_date = None

    if sales_table == "sales_enhanced":
        rev_q = f"""
        SELECT
          COALESCE(SUM(order_total),0) AS revenue,
          COUNT(DISTINCT CAST(order_id AS STRING)) AS orders
        FROM (
          SELECT CAST(order_id AS STRING) AS order_id, ANY_VALUE(order_total) AS order_total
          FROM `{pid}.{ds}.{sales_table}`
          WHERE bill_date = DATE('{d}')
          GROUP BY CAST(order_id AS STRING)
        )
        """
    else:
        rev_q = f"""
        SELECT
          COALESCE(SUM(total_revenue),0) AS revenue,
          COUNT(DISTINCT CAST(order_id AS STRING)) AS orders
        FROM `{pid}.{ds}.{sales_table}`
        WHERE bill_date = DATE('{d}')
        """
    try:
        rev_df = client.query(rev_q).to_dataframe()
        revenue = float(rev_df.iloc[0].get("revenue") or 0) if not rev_df.empty else 0.0
        orders = int(rev_df.iloc[0].get("orders") or 0) if not rev_df.empty else 0
    except Exception:
        revenue, orders = 0.0, 0

    # If you have historical sales but yesterday is empty, we flag it as a data issue.
    try:
        if sales_table == "sales_enhanced":
            q = f"""
            SELECT COALESCE(SUM(order_total),0) AS revenue
            FROM (
              SELECT bill_date, CAST(order_id AS STRING) AS order_id, ANY_VALUE(order_total) AS order_total
              FROM `{pid}.{ds}.{sales_table}`
              WHERE bill_date BETWEEN DATE_SUB(DATE('{d}'), INTERVAL 6 DAY) AND DATE('{d}')
              GROUP BY bill_date, CAST(order_id AS STRING)
            )
            """
        else:
            q = f"""
            SELECT COALESCE(SUM(total_revenue),0) AS revenue
            FROM `{pid}.{ds}.{sales_table}`
            WHERE bill_date BETWEEN DATE_SUB(DATE('{d}'), INTERVAL 6 DAY) AND DATE('{d}')
            """
        df = client.query(q).to_dataframe()
        revenue_7d = float(df.iloc[0].get("revenue") or 0) if not df.empty else 0.0
    except Exception:
        revenue_7d = 0.0

    if sales_table == "sales_enhanced":
        rev_lw_q = f"""
        SELECT
          COALESCE(SUM(order_total),0) AS revenue,
          COUNT(DISTINCT CAST(order_id AS STRING)) AS orders
        FROM (
          SELECT CAST(order_id AS STRING) AS order_id, ANY_VALUE(order_total) AS order_total
          FROM `{pid}.{ds}.{sales_table}`
          WHERE bill_date = DATE('{last_week}')
          GROUP BY CAST(order_id AS STRING)
        )
        """
    else:
        rev_lw_q = f"""
        SELECT
          COALESCE(SUM(total_revenue),0) AS revenue,
          COUNT(DISTINCT CAST(order_id AS STRING)) AS orders
        FROM `{pid}.{ds}.{sales_table}`
        WHERE bill_date = DATE('{last_week}')
        """
    try:
        rev_lw_df = client.query(rev_lw_q).to_dataframe()
        revenue_lw = float(rev_lw_df.iloc[0].get("revenue") or 0) if not rev_lw_df.empty else 0.0
        orders_lw = int(rev_lw_df.iloc[0].get("orders") or 0) if not rev_lw_df.empty else 0
    except Exception:
        revenue_lw, orders_lw = 0.0, 0

    exp_q = f"""
    SELECT
      COALESCE(SUM(SAFE_CAST(amount AS FLOAT64)),0) AS expenses
    FROM `{pid}.{ds}.expenses_master`
    WHERE expense_date = DATE('{d}')
    """
    try:
        exp_df = client.query(exp_q).to_dataframe()
        expenses = float(exp_df.iloc[0].get("expenses") or 0) if not exp_df.empty else 0.0
    except Exception:
        expenses = 0.0

    try:
        q = f"""
        SELECT COALESCE(SUM(SAFE_CAST(amount AS FLOAT64)),0) AS expenses
        FROM `{pid}.{ds}.expenses_master`
        WHERE expense_date BETWEEN DATE_SUB(DATE('{d}'), INTERVAL 6 DAY) AND DATE('{d}')
        """
        df = client.query(q).to_dataframe()
        expenses_7d = float(df.iloc[0].get("expenses") or 0) if not df.empty else 0.0
    except Exception:
        expenses_7d = 0.0

    exp_lw_q = f"""
    SELECT
      COALESCE(SUM(SAFE_CAST(amount AS FLOAT64)),0) AS expenses
    FROM `{pid}.{ds}.expenses_master`
    WHERE expense_date = DATE('{last_week}')
    """
    try:
        exp_lw_df = client.query(exp_lw_q).to_dataframe()
        expenses_lw = float(exp_lw_df.iloc[0].get("expenses") or 0) if not exp_lw_df.empty else 0.0
    except Exception:
        expenses_lw = 0.0

    top_items_q = f"""
    SELECT
      COALESCE(CAST(item_name AS STRING), '') AS item_name,
      COALESCE(SUM(total_revenue),0) AS revenue
    FROM `{pid}.{ds}.{sales_table}`
    WHERE bill_date BETWEEN DATE_SUB(DATE('{d}'), INTERVAL 6 DAY) AND DATE('{d}')
    GROUP BY item_name
    HAVING item_name != ''
    ORDER BY revenue DESC
    LIMIT 5
    """
    try:
        top_items_df = client.query(top_items_q).to_dataframe()
        top_items = top_items_df.to_dict("records") if not top_items_df.empty else []
    except Exception:
        top_items = []

    exp_spike_q = f"""
    WITH daily AS (
      SELECT
        expense_date AS dt,
        COALESCE(SUM(SAFE_CAST(amount AS FLOAT64)),0) AS total
      FROM `{pid}.{ds}.expenses_master`
      WHERE expense_date BETWEEN DATE_SUB(DATE('{d}'), INTERVAL 7 DAY) AND DATE('{d}')
      GROUP BY expense_date
    )
    SELECT
      (SELECT total FROM daily WHERE dt = DATE('{d}')) AS today,
      (SELECT AVG(total) FROM daily WHERE dt < DATE('{d}')) AS prev_avg
    """
    try:
        spike_df = client.query(exp_spike_q).to_dataframe()
        today_exp = float(spike_df.iloc[0].get("today") or 0) if not spike_df.empty else expenses
        prev_avg = float(spike_df.iloc[0].get("prev_avg") or 0) if not spike_df.empty else 0.0
        spike_ratio = (today_exp / prev_avg) if prev_avg > 0 else None
    except Exception:
        spike_ratio = None
        prev_avg = 0.0

    alerts_q = f"""
    SELECT task_type, item_involved, description, priority
    FROM `{pid}.{ds}.ai_task_queue`
    WHERE status = 'Pending'
    ORDER BY created_at DESC
    LIMIT 10
    """
    try:
        alerts_df = client.query(alerts_q).to_dataframe()
        alerts = alerts_df.to_dict("records") if not alerts_df.empty else []
        # Deduplicate while preserving order (queue often contains repeated items).
        seen = set()
        deduped: List[Dict[str, Any]] = []
        for a in alerts:
            k = (
                str(a.get("task_type") or ""),
                str(a.get("item_involved") or ""),
                str(a.get("description") or ""),
                str(a.get("priority") or ""),
            )
            if k in seen:
                continue
            seen.add(k)
            # Normalize to UI-friendly alert fields while preserving original columns.
            task_type = str(a.get("task_type") or "").strip()
            item = str(a.get("item_involved") or "").strip()
            desc = str(a.get("description") or "").strip()
            priority = str(a.get("priority") or "").strip()

            sev = ""
            p = priority.lower()
            if p in {"high", "urgent", "critical"}:
                sev = "high"
            elif p in {"medium"}:
                sev = "medium"
            elif p:
                sev = "low"

            title = task_type or (f"{item}" if item else "Alert")
            message = desc or (item if item else "")

            a2 = dict(a)
            a2.setdefault("title", title)
            a2.setdefault("message", message)
            a2.setdefault("severity", sev)
            deduped.append(a2)
        alerts = deduped
    except Exception:
        alerts = []

    # -----------------
    # System alerts (data freshness + sanity)
    # -----------------
    sys_alerts: List[Dict[str, Any]] = []

    def _add_sys_alert(title: str, message: str, severity: str = "high") -> None:
        sys_alerts.append(
            {
                "title": title,
                "message": message,
                "severity": severity,
                "task_type": "System",
                "item_involved": "",
                "description": message,
                "priority": severity.title(),
            }
        )

    if latest_sales_date and latest_sales_date < str(d):
        _add_sys_alert(
            "Sales data not up to date",
            f"Latest sales date is {latest_sales_date}, but brief date is {d}. Run sync / verify POS export.",
            "high",
        )
    if latest_expenses_date and latest_expenses_date < str(d):
        _add_sys_alert(
            "Expenses data not up to date",
            f"Latest expenses date is {latest_expenses_date}, but brief date is {d}. Verify expense entry/import.",
            "high",
        )

    if revenue == 0.0 and orders == 0 and revenue_7d > 0:
        _add_sys_alert(
            "Missing sales for yesterday",
            "Yesterday sales are zero, but there were sales in the last 7 days. Run sync and check POS export for missing day.",
            "high",
        )
    if expenses == 0.0 and expenses_7d > 0:
        _add_sys_alert(
            "Missing expenses for yesterday",
            "Yesterday expenses are zero, but there were expenses in the last 7 days. Verify expense capture/import.",
            "medium",
        )

    # Place system alerts at the top so they are seen first.
    alerts = sys_alerts + alerts

    def _pct_delta(cur: float, prev: float) -> Optional[float]:
        if prev == 0:
            return None
        return ((cur - prev) / prev) * 100.0

    kpis_last_week = {
        "revenue": revenue_lw,
        "expenses": expenses_lw,
        "net": revenue_lw - expenses_lw,
        "orders": orders_lw,
        "date": str(last_week),
    }
    kpis_delta_pct = {
        "revenue": _pct_delta(revenue, revenue_lw),
        "expenses": _pct_delta(expenses, expenses_lw),
        "net": _pct_delta(revenue - expenses, revenue_lw - expenses_lw),
        "orders": _pct_delta(float(orders), float(orders_lw)),
    }

    insights: List[str] = []
    if spike_ratio is not None and spike_ratio >= 1.5:
        insights.append(f"Expenses spike: {today_exp:.0f} vs avg {prev_avg:.0f} (last 7 days)")
    if orders == 0 and revenue == 0:
        insights.append("No sales recorded for yesterday. Check sync / POS export.")

    brief = {
        "ok": True,
        "brief_date": str(d),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "version": "v2",
        "kpis": {
            "revenue": revenue,
            "expenses": expenses,
            "net": revenue - expenses,
            "orders": orders,
        },
        # Keep legacy key + add UI-friendly alias.
        "top_items_last_7_days": top_items,
        "top_items_7d": top_items,
        "alerts": alerts,
        "insights": insights,
        "data_freshness": {
            "brief_date": str(d),
            "sales_table": sales_table,
            "latest_sales_date": latest_sales_date,
            "latest_expenses_date": latest_expenses_date,
            "revenue_7d": revenue_7d,
            "expenses_7d": expenses_7d,
        },
        "comparisons": {
            "last_week_same_day": {
                "kpis": kpis_last_week,
                "delta_pct": kpis_delta_pct,
            }
        },
    }
    return brief


def store_brief(client: bigquery.Client, cfg, brief: Dict[str, Any], version: str = "v1") -> None:
    ensure_table(client, cfg)
    table_id = _table_id(cfg)
    brief_date = brief.get("brief_date")
    if not brief_date:
        raise ValueError("brief_date missing")

    payload_json = json.dumps(brief, ensure_ascii=False)
    row = {
        "brief_date": brief_date,
        "created_at": datetime.utcnow().isoformat(),
        "version": version,
        "payload_json": payload_json,
    }
    errors = client.insert_rows_json(table_id, [row])
    if errors:
        raise RuntimeError(str(errors))


def get_latest_brief(client: bigquery.Client, cfg, brief_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
    table_id = _table_id(cfg)
    try:
        client.get_table(table_id)
    except NotFound:
        return None

    where = ""
    if brief_date:
        where = f"WHERE brief_date = DATE('{brief_date}')"

    q = f"""
    SELECT payload_json
    FROM `{table_id}`
    {where}
    ORDER BY brief_date DESC, created_at DESC
    LIMIT 1
    """
    df = client.query(q).to_dataframe()
    if df.empty:
        return None
    raw = df.iloc[0].get("payload_json")
    try:
        return json.loads(raw) if raw else None
    except Exception:
        return None


def generate_and_store(client: bigquery.Client, cfg, brief_date: Optional[date] = None) -> Dict[str, Any]:
    brief = generate_brief(client, cfg, brief_date=brief_date)
    store_brief(client, cfg, brief, version=str(brief.get("version") or "v1"))
    return brief
