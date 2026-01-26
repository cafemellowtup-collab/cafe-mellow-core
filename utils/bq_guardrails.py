import os
import threading
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound


_TL = threading.local()


class QueryMetaCollector:
    def __init__(self):
        self.items = []

    def __enter__(self):
        _TL.collector = self
        return self

    def __exit__(self, exc_type, exc, tb):
        _TL.collector = None
        return False


def _get_collector():
    return getattr(_TL, "collector", None)


def _cost_config():
    usd_per_tb = float(os.getenv("BIGQUERY_USD_PER_TB", "5"))
    usd_to_inr = float(os.getenv("USD_TO_INR", "83"))
    return usd_per_tb, usd_to_inr


def estimate_query_cost(client: bigquery.Client, query: str, location: Optional[str] = None):
    """Alias for estimate_query function for backward compatibility"""
    return estimate_query(client, query, location)


def ensure_cost_log_table(client: bigquery.Client, settings_mod):
    table = getattr(settings_mod, "TABLE_SYSTEM_COST_LOG", "system_cost_log")
    table_id = f"{settings_mod.PROJECT_ID}.{settings_mod.DATASET_ID}.{table}"
    try:
        client.get_table(table_id)
        return table_id
    except NotFound:
        schema = [
            bigquery.SchemaField("ts", "TIMESTAMP"),
            bigquery.SchemaField("purpose", "STRING"),
            bigquery.SchemaField("bytes_processed", "INT64"),
            bigquery.SchemaField("estimated_cost_usd", "FLOAT64"),
            bigquery.SchemaField("estimated_cost_inr", "FLOAT64"),
        ]
        t = bigquery.Table(table_id, schema=schema)
        client.create_table(t)
        return table_id


def log_query_cost(client: bigquery.Client, settings_mod, purpose: str, estimate: dict):
    if not purpose:
        purpose = "unknown"
    try:
        table_id = ensure_cost_log_table(client, settings_mod)
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "purpose": str(purpose)[:120],
            "bytes_processed": int(estimate.get("bytes") or 0),
            "estimated_cost_usd": float(estimate.get("cost_usd") or 0.0),
            "estimated_cost_inr": float(estimate.get("cost_inr") or 0.0),
        }
        df = pd.DataFrame([row])
        df["ts"] = pd.to_datetime(df["ts"], utc=True)
        client.load_table_from_dataframe(df, table_id).result()
    except Exception:
        return


def query_to_df(client: bigquery.Client, settings_mod, query: str, purpose: str, location: Optional[str] = None, log_cost: bool = True):
    est = None
    if log_cost:
        try:
            est = estimate_query(client, query, location=location)
            c = _get_collector()
            if c is not None:
                c.items.append(
                    {
                        "purpose": str(purpose or "unknown")[:200],
                        "bytes": int(est.get("bytes") or 0),
                        "cost_usd": float(est.get("cost_usd") or 0.0),
                        "cost_inr": float(est.get("cost_inr") or 0.0),
                    }
                )
            try:
                max_inr = float(getattr(settings_mod, "MAX_QUERY_COST_INR", 0) or 0)
                disable = bool(getattr(settings_mod, "DISABLE_BUDGET_BREAKER", False))
                if (not disable) and max_inr > 0 and float(est.get("cost_inr") or 0) > max_inr:
                    raise RuntimeError(
                        f"Budget breaker: estimated query cost ₹{float(est.get('cost_inr') or 0):.2f} exceeds MAX_QUERY_COST_INR ₹{max_inr:.2f} (purpose='{purpose}')."
                    )
            except RuntimeError:
                raise
            except Exception:
                pass
            log_query_cost(client, settings_mod, purpose, est)
        except RuntimeError:
            raise
        except Exception:
            est = None
    df = client.query(query, location=location).to_dataframe()
    return df, est
