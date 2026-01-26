from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from google.cloud import bigquery
from google.cloud.exceptions import NotFound


def _table_id(cfg) -> str:
    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    return f"{pid}.{ds}.ai_task_queue"


def ensure_table(client: bigquery.Client, cfg) -> None:
    table_id = _table_id(cfg)
    try:
        client.get_table(table_id)
        return
    except NotFound:
        schema = [
            bigquery.SchemaField("created_at", "DATETIME", mode="NULLABLE"),
            bigquery.SchemaField("target_date", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("department", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("task_type", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("item_involved", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("status", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("priority", "STRING", mode="NULLABLE"),
        ]
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)


def _priority_from_severity(sev: str) -> str:
    s = (sev or "").strip().lower()
    if s in {"high", "urgent", "critical"}:
        return "High"
    if s == "medium":
        return "Medium"
    if s == "low":
        return "Low"
    return "Medium"


def _existing_keys(client: bigquery.Client, cfg, target_date: str) -> Set[Tuple[str, str, str, str]]:
    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    if not pid or not ds:
        return set()

    q = f"""
    SELECT
      COALESCE(CAST(target_date AS STRING), '') AS target_date,
      COALESCE(CAST(task_type AS STRING), '') AS task_type,
      COALESCE(CAST(item_involved AS STRING), '') AS item_involved,
      COALESCE(CAST(description AS STRING), '') AS description
    FROM `{pid}.{ds}.ai_task_queue`
    WHERE COALESCE(CAST(target_date AS STRING), '') = '{target_date}'
    AND COALESCE(CAST(status AS STRING), '') = 'Pending'
    """
    out: Set[Tuple[str, str, str, str]] = set()
    try:
        df = client.query(q).to_dataframe()
        if df.empty:
            return out
        for _, r in df.iterrows():
            out.add(
                (
                    str(r.get("target_date") or ""),
                    str(r.get("task_type") or ""),
                    str(r.get("item_involved") or ""),
                    str(r.get("description") or ""),
                )
            )
    except Exception:
        return out
    return out


def insert_tasks(client: bigquery.Client, cfg, tasks: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    ensure_table(client, cfg)
    table_id = _table_id(cfg)
    rows = list(tasks)
    if not rows:
        return {"ok": True, "inserted": 0}

    errors = client.insert_rows_json(table_id, rows)
    if errors:
        raise RuntimeError(str(errors))
    return {"ok": True, "inserted": len(rows)}


def generate_tasks_from_ops_brief(brief: Dict[str, Any]) -> List[Dict[str, Any]]:
    target_date = str(brief.get("brief_date") or "").strip()
    if not target_date:
        return []

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    tasks: List[Dict[str, Any]] = []

    for a in (brief.get("alerts") or []):
        if not isinstance(a, dict):
            continue
        task_type = str(a.get("task_type") or a.get("title") or "Alert").strip() or "Alert"
        item = str(a.get("item_involved") or "").strip()
        desc = str(a.get("message") or a.get("description") or "").strip() or task_type
        severity = str(a.get("severity") or a.get("priority") or "").strip()

        tasks.append(
            {
                "created_at": now,
                "target_date": target_date,
                "department": "Operations",
                "task_type": task_type,
                "item_involved": item,
                "description": desc,
                "status": "Pending",
                "priority": _priority_from_severity(severity),
            }
        )

    delta = (
        (((brief.get("comparisons") or {}).get("last_week_same_day") or {}).get("delta_pct"))
        if isinstance(brief.get("comparisons"), dict)
        else None
    )
    if isinstance(delta, dict):
        rev = delta.get("revenue")
        exp = delta.get("expenses")
        net = delta.get("net")

        def _add(title: str, pct: Any, priority: str, message: str) -> None:
            tasks.append(
                {
                    "created_at": now,
                    "target_date": target_date,
                    "department": "Operations",
                    "task_type": title,
                    "item_involved": "",
                    "description": message.format(pct=pct),
                    "status": "Pending",
                    "priority": priority,
                }
            )

        try:
            if isinstance(rev, (int, float)) and rev <= -30:
                _add(
                    "Revenue Drop",
                    rev,
                    "High",
                    "Revenue dropped {pct:.1f}% vs last week same day. Investigate POS sync, stock-outs, offers, and demand.",
                )
            if isinstance(exp, (int, float)) and exp >= 30:
                _add(
                    "Expense Spike",
                    exp,
                    "High",
                    "Expenses increased {pct:.1f}% vs last week same day. Review ledgers/categories for unusual spend.",
                )
            if isinstance(net, (int, float)) and net <= -40:
                _add(
                    "Profit Drop",
                    net,
                    "High",
                    "Net/profit dropped {pct:.1f}% vs last week same day. Check revenue drop and expense spike drivers.",
                )
        except Exception:
            pass

    return tasks


def generate_and_write_ops_tasks(
    client: bigquery.Client,
    cfg,
    brief: Dict[str, Any],
    allow_duplicates: bool = False,
) -> Dict[str, Any]:
    target_date = str(brief.get("brief_date") or "").strip()
    if not target_date:
        return {"ok": True, "inserted": 0, "skipped": 0}

    candidates = generate_tasks_from_ops_brief(brief)

    batch_seen: Set[Tuple[str, str, str, str]] = set()
    existing = set() if allow_duplicates else _existing_keys(client, cfg, target_date)

    final: List[Dict[str, Any]] = []
    skipped = 0
    for t in candidates:
        k = (
            str(t.get("target_date") or ""),
            str(t.get("task_type") or ""),
            str(t.get("item_involved") or ""),
            str(t.get("description") or ""),
        )
        if (not allow_duplicates) and (k in existing or k in batch_seen):
            skipped += 1
            continue
        batch_seen.add(k)
        final.append(t)

    res = insert_tasks(client, cfg, final)
    return {"ok": True, "inserted": int(res.get("inserted") or 0), "skipped": skipped}
