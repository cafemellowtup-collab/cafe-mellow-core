import os
import json
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pillars.config_vault import EffectiveSettings, save_config_override
from utils.ops_brief import generate_and_store as _generate_and_store_brief
from utils.ops_brief import get_latest_brief as _get_latest_brief
from utils.ai_task_queue import generate_and_write_ops_tasks as _generate_and_write_ops_tasks

from api.routers import cron, ledger, analytics, hr, ceo_brief, upload, chat, sync, oracle, forecast, ingester, users, notifications, auth, universal_adapter, semantic_brain, master
from backend.universal_adapter.airlock import router as airlock_router


app = FastAPI(
    title="TITAN ERP API", 
    version="4.0.0-SEMANTIC-BRAIN",
    description="Universal Semantic Brain - AGI for Data Engineering | Multi-Tenant SaaS"
)


@app.get("/")
async def root():
    """Root endpoint with system info"""
    return {
        "name": "TITAN ERP",
        "version": "4.0.0",
        "edition": "Universal Semantic Brain",
        "status": "operational",
        "capabilities": [
            "semantic-classification",
            "multi-tenant-isolation",
            "immutable-event-ledger",
            "ai-cfo-chat",
            "360-analysis"
        ]
    }


@app.get("/health")
async def global_health():
    """Global health check"""
    return {"ok": True, "status": "healthy", "version": "4.0.0"}

# Auto-Pilot: Background cron scheduler
@app.on_event("startup")
async def startup_cron():
    """Initialize background tasks for automated daily sync"""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        import asyncio
        
        scheduler = AsyncIOScheduler()
        
        # Daily sync at 2 AM
        scheduler.add_job(
            _run_daily_sync,
            CronTrigger(hour=2, minute=0),
            id="daily_sync",
            replace_existing=True
        )
        
        # Brief generation at 6 AM
        scheduler.add_job(
            _run_daily_brief,
            CronTrigger(hour=6, minute=0),
            id="daily_brief",
            replace_existing=True
        )
        
        scheduler.start()
        print("✅ Auto-Pilot cron scheduler initialized")
    except Exception as e:
        print(f"⚠️ Cron scheduler failed to start: {e}")

async def _run_daily_sync():
    """Background task: Run all data syncs"""
    try:
        import subprocess
        import sys
        project_root = os.path.abspath(os.path.dirname(__file__) + "/../")
        
        scripts = [
            "01_Data_Sync/sync_sales_raw.py",
            "01_Data_Sync/titan_sales_parser.py",
            "01_Data_Sync/sync_expenses.py",
            "01_Data_Sync/sync_recipes.py",
        ]
        
        for script in scripts:
            script_path = os.path.join(project_root, script)
            if os.path.exists(script_path):
                subprocess.run([sys.executable, script_path], cwd=project_root, timeout=300)
        
        print(f"✅ Daily sync completed at {datetime.now()}")
    except Exception as e:
        print(f"❌ Daily sync failed: {e}")

async def _run_daily_brief():
    """Background task: Generate daily operational brief"""
    try:
        _generate_and_store_brief()
        print(f"✅ Daily brief generated at {datetime.now()}")
    except Exception as e:
        print(f"❌ Daily brief failed: {e}")

app.include_router(cron.router)
app.include_router(ledger.router)
app.include_router(analytics.router)
app.include_router(hr.router)
app.include_router(ceo_brief.router)
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(sync.router)
app.include_router(oracle.router)
app.include_router(forecast.router)
app.include_router(ingester.router)
app.include_router(users.router)
app.include_router(notifications.router)
app.include_router(auth.router)
app.include_router(universal_adapter.router)
app.include_router(airlock_router)
app.include_router(semantic_brain.router)
app.include_router(master.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://cafe-mellow-core.vercel.app",
        "https://cafe-mellow-core-git-main-gokul-rajs-projects-99d7ad96.vercel.app",
    ],
    allow_origin_regex=r"^https?:\/\/(localhost|127\.0\.0\.1|\d{1,3}(?:\.\d{1,3}){3}):30\d{2}$|^https:\/\/cafe-mellow-core.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    org_id: Optional[str] = None
    location_id: Optional[str] = None


class ConfigUpdate(BaseModel):
    PROJECT_ID: Optional[str] = None
    DATASET_ID: Optional[str] = None
    KEY_FILE: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    PP_APP_KEY: Optional[str] = None
    PP_APP_SECRET: Optional[str] = None
    PP_ACCESS_TOKEN: Optional[str] = None
    PP_MAPPING_CODE: Optional[str] = None
    FOLDER_ID_EXPENSES: Optional[str] = None
    FOLDER_ID_PURCHASES: Optional[str] = None
    FOLDER_ID_INVENTORY: Optional[str] = None
    FOLDER_ID_RECIPES: Optional[str] = None
    FOLDER_ID_WASTAGE: Optional[str] = None


def _settings():
    return EffectiveSettings()


def _get_bq_client():
    try:
        from google.cloud import bigquery

        cfg = _settings()
        key_file = getattr(cfg, "KEY_FILE", "service-key.json")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
        
        # Try service account key file first (local development)
        if os.path.exists(key_path):
            return bigquery.Client.from_service_account_json(key_path)
        
        # Fall back to Application Default Credentials (Cloud Run)
        project_id = getattr(cfg, "PROJECT_ID", None) or os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if project_id:
            return bigquery.Client(project=project_id)
        
        # Last resort: let BigQuery auto-detect project
        return bigquery.Client()
    except Exception:
        return None


def _validate_chat_request(req: ChatRequest):
    cfg = _settings()
    msg = (req.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="message is required")

    if not getattr(cfg, "GEMINI_API_KEY", ""):
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY is missing")

    client = _get_bq_client()
    if not client:
        raise HTTPException(
            status_code=400,
            detail="BigQuery not connected (missing/invalid service-key.json or dataset)",
        )

    return cfg, client, msg


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def _date_range(start: Optional[str], end: Optional[str], default_days: int = 30):
    e = _parse_date(end) or date.today()
    s = _parse_date(start) or (e - timedelta(days=int(default_days)))
    if s > e:
        s, e = e, s
    return s, e


@app.get("/health")
def health() -> Dict[str, Any]:
    cfg = _settings()
    client = _get_bq_client()
    return {
        "ok": True,
        "bq_connected": bool(client),
        "project_id": getattr(cfg, "PROJECT_ID", ""),
        "dataset_id": getattr(cfg, "DATASET_ID", ""),
        "gemini_key_set": bool(getattr(cfg, "GEMINI_API_KEY", "")),
    }


@app.get("/config")
def get_config() -> Dict[str, Any]:
    cfg = _settings()
    # Never return secrets; only return set/missing.
    return {
        "ok": True,
        "PROJECT_ID": getattr(cfg, "PROJECT_ID", ""),
        "DATASET_ID": getattr(cfg, "DATASET_ID", ""),
        "KEY_FILE": getattr(cfg, "KEY_FILE", "service-key.json"),
        "GEMINI_API_KEY_set": bool(getattr(cfg, "GEMINI_API_KEY", "")),
        "PP_APP_KEY_set": bool(getattr(cfg, "PP_APP_KEY", "")),
        "PP_APP_SECRET_set": bool(getattr(cfg, "PP_APP_SECRET", "")),
        "PP_ACCESS_TOKEN_set": bool(getattr(cfg, "PP_ACCESS_TOKEN", "")),
        "PP_MAPPING_CODE_set": bool(getattr(cfg, "PP_MAPPING_CODE", "")),
        "FOLDER_ID_EXPENSES_set": bool(getattr(cfg, "FOLDER_ID_EXPENSES", "")),
        "FOLDER_ID_PURCHASES_set": bool(getattr(cfg, "FOLDER_ID_PURCHASES", "")),
        "FOLDER_ID_INVENTORY_set": bool(getattr(cfg, "FOLDER_ID_INVENTORY", "")),
        "FOLDER_ID_RECIPES_set": bool(getattr(cfg, "FOLDER_ID_RECIPES", "")),
        "FOLDER_ID_WASTAGE_set": bool(getattr(cfg, "FOLDER_ID_WASTAGE", "")),
    }


@app.post("/config")
def update_config(payload: ConfigUpdate) -> Dict[str, Any]:
    # DEPRECATED: Use PATCH /config instead for merge updates
    # This writes to config_override.json. In cloud deployments, this will move to Secret Manager.
    overrides = payload.dict(exclude_unset=True)
    saved = save_config_override(overrides, merge=False)  # POST = full replace
    cfg = _settings()
    return {
        "ok": True,
        "saved_keys": list(saved.keys()),
        "PROJECT_ID": getattr(cfg, "PROJECT_ID", ""),
        "DATASET_ID": getattr(cfg, "DATASET_ID", ""),
        "KEY_FILE": getattr(cfg, "KEY_FILE", "service-key.json"),
        "GEMINI_API_KEY_set": bool(getattr(cfg, "GEMINI_API_KEY", "")),
        "PP_APP_KEY_set": bool(getattr(cfg, "PP_APP_KEY", "")),
        "PP_APP_SECRET_set": bool(getattr(cfg, "PP_APP_SECRET", "")),
        "PP_ACCESS_TOKEN_set": bool(getattr(cfg, "PP_ACCESS_TOKEN", "")),
        "PP_MAPPING_CODE_set": bool(getattr(cfg, "PP_MAPPING_CODE", "")),
        "FOLDER_ID_EXPENSES_set": bool(getattr(cfg, "FOLDER_ID_EXPENSES", "")),
        "FOLDER_ID_PURCHASES_set": bool(getattr(cfg, "FOLDER_ID_PURCHASES", "")),
        "FOLDER_ID_INVENTORY_set": bool(getattr(cfg, "FOLDER_ID_INVENTORY", "")),
        "FOLDER_ID_RECIPES_set": bool(getattr(cfg, "FOLDER_ID_RECIPES", "")),
        "FOLDER_ID_WASTAGE_set": bool(getattr(cfg, "FOLDER_ID_WASTAGE", "")),
    }


@app.patch("/config")
def patch_config(payload: ConfigUpdate) -> Dict[str, Any]:
    """
    PATCH endpoint: Merges new settings with existing, preventing credential overwrites.
    When updating Petpooja credentials, Gemini/Drive keys persist.
    """
    overrides = payload.dict(exclude_unset=True)
    saved = save_config_override(overrides, merge=True)  # PATCH = merge
    cfg = _settings()
    return {
        "ok": True,
        "saved_keys": list(saved.keys()),
        "merge": True,
        "PROJECT_ID": getattr(cfg, "PROJECT_ID", ""),
        "DATASET_ID": getattr(cfg, "DATASET_ID", ""),
        "KEY_FILE": getattr(cfg, "KEY_FILE", "service-key.json"),
        "GEMINI_API_KEY_set": bool(getattr(cfg, "GEMINI_API_KEY", "")),
        "PP_APP_KEY_set": bool(getattr(cfg, "PP_APP_KEY", "")),
        "PP_APP_SECRET_set": bool(getattr(cfg, "PP_APP_SECRET", "")),
        "PP_ACCESS_TOKEN_set": bool(getattr(cfg, "PP_ACCESS_TOKEN", "")),
        "PP_MAPPING_CODE_set": bool(getattr(cfg, "PP_MAPPING_CODE", "")),
        "FOLDER_ID_EXPENSES_set": bool(getattr(cfg, "FOLDER_ID_EXPENSES", "")),
        "FOLDER_ID_PURCHASES_set": bool(getattr(cfg, "FOLDER_ID_PURCHASES", "")),
        "FOLDER_ID_INVENTORY_set": bool(getattr(cfg, "FOLDER_ID_INVENTORY", "")),
        "FOLDER_ID_RECIPES_set": bool(getattr(cfg, "FOLDER_ID_RECIPES", "")),
        "FOLDER_ID_WASTAGE_set": bool(getattr(cfg, "FOLDER_ID_WASTAGE", "")),
    }


@app.post("/chat")
def chat(req: ChatRequest) -> Dict[str, Any]:
    cfg, client, msg = _validate_chat_request(req)

    try:
        from utils.gemini_chat import chat_with_gemini

        response = chat_with_gemini(client, cfg, msg, conversation_history=None)
        return {"ok": True, "answer": response}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    cfg, client, msg = _validate_chat_request(req)

    try:
        from utils.gemini_chat import chat_with_gemini_stream, get_conversation_history
        from utils.bq_guardrails import QueryMetaCollector
        from pillars.chat_intel import parse_time_window
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    def _sse():
        # Establish the stream immediately so the browser doesn't look "stuck".
        yield ": stream-open\n\n"

        try:
            streamed_any = False
            tw_sql, tw_label, _tw_days = parse_time_window(msg)
            
            # MEMORY OPTIMIZATION: Fetch conversation history and limit to last 10 messages
            conversation_history = get_conversation_history(client, cfg, limit=10)
            
            with QueryMetaCollector() as qc:
                for chunk in chat_with_gemini_stream(client, cfg, msg, conversation_history=conversation_history):
                    streamed_any = True
                    safe = str(chunk).replace("\r", "").replace("\n", "\\n")
                    if safe:
                        yield f"data:{safe}\n\n"

            items = list(getattr(qc, "items", []) or [])
            total_inr = float(sum(float(x.get("cost_inr") or 0.0) for x in items))
            sources_payload = {
                "time_window": tw_label or "",
                "queries": items,
                "total_cost_inr": total_inr,
            }
            sources_json = json.dumps(sources_payload, ensure_ascii=False)
            sources_json = sources_json.replace("\r", "").replace("\n", "")
            yield f"event: sources\ndata:{sources_json}\n\n"

            if not streamed_any:
                yield "event: done\ndata: {}\n\n"
                return

            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            err = str(e).replace("\r", "").replace("\n", "\\n")
            yield f"event: error\ndata:{err}\n\n"

    return StreamingResponse(
        _sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/metrics/overview")
def metrics_overview(
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    debug: bool = Query(default=False),
) -> Dict[str, Any]:
    cfg = _settings()
    client = _get_bq_client()
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected (missing/invalid service-key.json or dataset)")

    s, e = _date_range(start, end, default_days=30)
    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    if not pid or not ds:
        raise HTTPException(status_code=400, detail="PROJECT_ID/DATASET_ID not configured")

    try:
        from utils.bq_guardrails import query_to_df

        # Revenue must match POS: compute order-level totals and exclude cancelled.
        # Prefer enhanced only if it actually has rows for the requested range.
        has_enhanced = _table_exists(client, pid, ds, "sales_enhanced")
        has_raw = _table_exists(client, pid, ds, "sales_raw_layer")

        enhanced_orders = 0
        enhanced_revenue = 0.0
        raw_orders = 0
        raw_revenue = 0.0

        if has_enhanced:
            q_enh = f"""
            SELECT
              COUNT(1) AS orders,
              COALESCE(SUM(order_total),0) AS revenue
            FROM (
              SELECT
                SAFE_CAST(bill_date AS DATE) AS dt,
                CAST(order_id AS STRING) AS order_id,
                ANY_VALUE(SAFE_CAST(order_total AS FLOAT64)) AS order_total,
                ANY_VALUE(CAST(order_status AS STRING)) AS order_status
              FROM `{pid}.{ds}.sales_enhanced`
              WHERE SAFE_CAST(bill_date AS DATE) BETWEEN DATE('{s}') AND DATE('{e}')
              GROUP BY SAFE_CAST(bill_date AS DATE), CAST(order_id AS STRING)
            )
            WHERE NOT REGEXP_CONTAINS(LOWER(COALESCE(order_status, '')), r"cancel")
            """
            df_e, _ = query_to_df(client, cfg, q_enh, purpose="api.metrics.overview.revenue.enhanced")
            if not df_e.empty:
                enhanced_orders = int(df_e["orders"].iloc[0] or 0)
                enhanced_revenue = float(df_e["revenue"].iloc[0] or 0.0)

        if has_raw:
            # Robust JSON paths: Petpooja payloads vary across endpoints/versions.
            q_raw = f"""
            SELECT
              COUNT(1) AS orders,
              COALESCE(SUM(order_total),0) AS revenue
            FROM (
              SELECT
                bill_date AS dt,
                CAST(order_id AS STRING) AS order_id,
                ANY_VALUE(
                  COALESCE(
                    SAFE_CAST(JSON_VALUE(full_json, '$.Order.order_total') AS FLOAT64),
                    SAFE_CAST(JSON_VALUE(full_json, '$.Order.total') AS FLOAT64),
                    SAFE_CAST(JSON_VALUE(full_json, '$.Order.grand_total') AS FLOAT64),
                    SAFE_CAST(JSON_VALUE(full_json, '$.Order.orderTotal') AS FLOAT64)
                  )
                ) AS order_total,
                ANY_VALUE(
                  COALESCE(
                    CAST(JSON_VALUE(full_json, '$.Order.status') AS STRING),
                    CAST(JSON_VALUE(full_json, '$.Order.order_status') AS STRING),
                    CAST(JSON_VALUE(full_json, '$.Order.orderStatus') AS STRING)
                  )
                ) AS order_status
              FROM `{pid}.{ds}.sales_raw_layer`
              WHERE bill_date BETWEEN DATE('{s}') AND DATE('{e}')
              GROUP BY bill_date, CAST(order_id AS STRING)
            )
            WHERE NOT REGEXP_CONTAINS(LOWER(COALESCE(order_status, '')), r"cancel")
            """
            df_r, _ = query_to_df(client, cfg, q_raw, purpose="api.metrics.overview.revenue.raw")
            if not df_r.empty:
                raw_orders = int(df_r["orders"].iloc[0] or 0)
                raw_revenue = float(df_r["revenue"].iloc[0] or 0.0)

        if has_enhanced and enhanced_orders > 0:
            revenue = enhanced_revenue
            revenue_source = "sales_enhanced"
        elif has_raw and raw_orders > 0:
            revenue = raw_revenue
            revenue_source = "sales_raw_layer"
        else:
            q_items = f"""
            SELECT COALESCE(SUM(SAFE_CAST(total_revenue AS FLOAT64)),0) AS revenue
            FROM `{pid}.{ds}.sales_items_parsed`
            WHERE bill_date BETWEEN DATE('{s}') AND DATE('{e}')
            """
            df_i, _ = query_to_df(client, cfg, q_items, purpose="api.metrics.overview.revenue.items")
            revenue = float(df_i["revenue"].iloc[0] or 0.0) if not df_i.empty and "revenue" in df_i.columns else 0.0
            revenue_source = "sales_items_parsed"

        q_exp = f"""
        SELECT COALESCE(SUM(SAFE_CAST(amount AS FLOAT64)),0) AS expenses
        FROM `{pid}.{ds}.expenses_master`
        WHERE expense_date BETWEEN DATE('{s}') AND DATE('{e}')
        """
        df_x, _ = query_to_df(client, cfg, q_exp, purpose="api.metrics.overview.expenses")
        expenses = float(df_x["expenses"].iloc[0] or 0.0) if not df_x.empty and "expenses" in df_x.columns else 0.0

        days = max(1, int((e - s).days) + 1)
        resp = {
            "ok": True,
            "start": str(s),
            "end": str(e),
            "days": days,
            "revenue": revenue,
            "expenses": expenses,
            "net": revenue - expenses,
            "avg_daily_revenue": revenue / float(days),
        }
        if debug:
            resp["debug"] = {
                "project_id": pid,
                "dataset_id": ds,
                "source": revenue_source,
                "has_enhanced": bool(has_enhanced),
                "has_raw": bool(has_raw),
                "enhanced": {"orders": enhanced_orders, "revenue": enhanced_revenue},
                "raw": {"orders": raw_orders, "revenue": raw_revenue},
            }
        return resp
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/debug/sales/day")
def debug_sales_day(
    d: str = Query(..., description="YYYY-MM-DD"),
) -> Dict[str, Any]:
    cfg = _settings()
    client = _get_bq_client()
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected (missing/invalid service-key.json or dataset)")

    dt = _parse_date(d)
    if not dt:
        raise HTTPException(status_code=400, detail="d must be YYYY-MM-DD")

    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    if not pid or not ds:
        raise HTTPException(status_code=400, detail="PROJECT_ID/DATASET_ID not configured")

    try:
        from utils.bq_guardrails import query_to_df

        out: Dict[str, Any] = {"ok": True, "date": str(dt)}

        if _table_exists(client, pid, ds, "sales_raw_layer"):
            q = f"""
            SELECT
              COUNT(1) AS row_count,
              COUNT(DISTINCT CAST(order_id AS STRING)) AS orders,
              CAST(MIN(bill_date) AS STRING) AS min_bill_date,
              CAST(MAX(bill_date) AS STRING) AS max_bill_date
            FROM `{pid}.{ds}.sales_raw_layer`
            WHERE bill_date = DATE('{dt}')
            """
            df, _ = query_to_df(client, cfg, q, purpose=f"api.debug.sales_raw_layer.{dt}")
            out["sales_raw_layer"] = df.to_dict("records")[0] if not df.empty else {}
        else:
            out["sales_raw_layer"] = {"exists": False}

        if _table_exists(client, pid, ds, "sales_items_parsed"):
            q = f"""
            SELECT
              COUNT(1) AS row_count,
              COUNT(DISTINCT CAST(order_id AS STRING)) AS orders,
              COALESCE(SUM(SAFE_CAST(total_revenue AS FLOAT64)),0) AS revenue
            FROM `{pid}.{ds}.sales_items_parsed`
            WHERE bill_date = DATE('{dt}')
            """
            df, _ = query_to_df(client, cfg, q, purpose=f"api.debug.sales_items_parsed.{dt}")
            out["sales_items_parsed"] = df.to_dict("records")[0] if not df.empty else {}
        else:
            out["sales_items_parsed"] = {"exists": False}

        if _table_exists(client, pid, ds, "sales_enhanced"):
            q = f"""
            SELECT
              COUNT(1) AS row_count,
              COUNT(DISTINCT CAST(order_id AS STRING)) AS orders,
              COALESCE(SUM(order_total),0) AS revenue
            FROM (
              SELECT
                SAFE_CAST(bill_date AS DATE) AS bill_date,
                CAST(order_id AS STRING) AS order_id,
                ANY_VALUE(SAFE_CAST(order_total AS FLOAT64)) AS order_total
              FROM `{pid}.{ds}.sales_enhanced`
              WHERE SAFE_CAST(bill_date AS DATE) = DATE('{dt}')
              GROUP BY SAFE_CAST(bill_date AS DATE), CAST(order_id AS STRING)
            )
            """
            df, _ = query_to_df(client, cfg, q, purpose=f"api.debug.sales_enhanced.{dt}")
            out["sales_enhanced"] = df.to_dict("records")[0] if not df.empty else {}
        else:
            out["sales_enhanced"] = {"exists": False}

        return out
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/tasks/generate")
@app.post("/tasks/generate")
def tasks_generate(
    brief_date: Optional[str] = Query(default=None),
    dry_run: bool = Query(default=False),
    allow_duplicates: bool = Query(default=False),
) -> Dict[str, Any]:
    cfg = _settings()
    client = _get_bq_client()
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected (missing/invalid service-key.json or dataset)")

    try:
        d = _parse_date(brief_date) if brief_date else (date.today() - timedelta(days=1))
        if not d:
            raise HTTPException(status_code=400, detail="brief_date must be YYYY-MM-DD")

        # Ensure we use the latest brief schema (today endpoint already self-heals).
        brief = _get_latest_brief(client, cfg, brief_date=d)
        if not brief:
            brief = _generate_and_store_brief(client, cfg, brief_date=d)

        if dry_run:
            from utils.ai_task_queue import generate_tasks_from_ops_brief

            tasks = generate_tasks_from_ops_brief(brief)
            return {"ok": True, "dry_run": True, "brief_date": str(d), "count": len(tasks), "tasks": tasks[:50]}

        res = _generate_and_write_ops_tasks(client, cfg, brief, allow_duplicates=allow_duplicates)
        return {"ok": True, "dry_run": False, "brief_date": str(d), **res}
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/ops/brief/today")
def ops_brief_today() -> Dict[str, Any]:
    cfg = _settings()
    client = _get_bq_client()
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected (missing/invalid service-key.json or dataset)")

    try:
        d = date.today() - timedelta(days=1)
        existing = _get_latest_brief(client, cfg, brief_date=d)
        if existing:
            # If schema is old/stale, regenerate. This avoids breaking clients when brief evolves.
            version = str(existing.get("version") or "") if isinstance(existing, dict) else ""
            has_v2_fields = (
                isinstance(existing, dict)
                and ("comparisons" in existing)
                and ("data_freshness" in existing)
                and ("top_items_7d" in existing or "top_items_last_7_days" in existing)
                and ("alerts" in existing)
            )
            if version.lower().startswith("v2") and has_v2_fields:
                return existing
            return _generate_and_store_brief(client, cfg, brief_date=d)
        return _generate_and_store_brief(client, cfg, brief_date=d)
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@app.post("/ops/brief/generate")
def ops_brief_generate(
    brief_date: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    cfg = _settings()
    client = _get_bq_client()
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected (missing/invalid service-key.json or dataset)")

    try:
        d = _parse_date(brief_date) if brief_date else (date.today() - timedelta(days=1))
        if not d:
            raise HTTPException(status_code=400, detail="brief_date must be YYYY-MM-DD")
        return _generate_and_store_brief(client, cfg, brief_date=d)
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/ops/brief/recent")
def ops_brief_recent(
    days: int = Query(default=7, ge=1, le=31),
) -> Dict[str, Any]:
    cfg = _settings()
    client = _get_bq_client()
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected (missing/invalid service-key.json or dataset)")

    try:
        pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
        if not pid or not ds:
            raise HTTPException(status_code=400, detail="PROJECT_ID/DATASET_ID not configured")

        table_id = f"{pid}.{ds}.ops_daily_briefs"
        q = f"""
        SELECT payload_json
        FROM `{table_id}`
        WHERE brief_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {int(days)} DAY)
        ORDER BY brief_date DESC, created_at DESC
        """
        df = client.query(q).to_dataframe()
        items: List[Dict[str, Any]] = []
        for raw in (df["payload_json"].tolist() if (not df.empty and "payload_json" in df.columns) else []):
            try:
                items.append(json.loads(raw) if raw else {})
            except Exception:
                continue
        return {"ok": True, "days": int(days), "items": items}
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/ops/sales/filters")
def ops_sales_filters() -> Dict[str, Any]:
    cfg = _settings()
    client = _get_bq_client()
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected (missing/invalid service-key.json or dataset)")

    info = _sales_table_info(client, cfg)
    pid, ds, table, cols = info["pid"], info["ds"], info["table"], info["cols"]
    if not pid or not ds:
        raise HTTPException(status_code=400, detail="PROJECT_ID/DATASET_ID not configured")

    order_type_col = "order_type" if "order_type" in cols else None
    delivery_col = "delivery_partner" if "delivery_partner" in cols else None
    payment_col = "payment_mode" if "payment_mode" in cols else None

    raw_info = _sales_raw_info(client, cfg)
    raw_pid, raw_ds, raw_table = raw_info.get("pid"), raw_info.get("ds"), raw_info.get("table")
    raw_json_col = raw_info.get("json_col")
    can_join_raw = bool(raw_info.get("exists") and raw_json_col and ("order_id" in cols) and ("bill_date" in cols))

    try:
        from utils.bq_guardrails import query_to_df

        order_expr = (
            f"ARRAY(SELECT DISTINCT COALESCE(CAST({order_type_col} AS STRING), '') FROM `{pid}.{ds}.{table}` WHERE COALESCE(CAST({order_type_col} AS STRING), '') != '' ORDER BY 1 LIMIT 50) AS order_types"
            if order_type_col
            else "ARRAY<STRING>[] AS order_types"
        )
        from_sql = f"`{pid}.{ds}.{table}` t"
        raw_json_expr = None
        if can_join_raw:
            from_sql = (
                f"`{pid}.{ds}.{table}` t "
                f"LEFT JOIN `{raw_pid}.{raw_ds}.{raw_table}` r "
                f"ON CAST(t.order_id AS STRING) = CAST(r.order_id AS STRING) "
                f"AND t.bill_date = r.bill_date"
            )
            raw_json_expr = f"r.{raw_json_col}"

        # Normalize platform/channel even if delivery_partner is blank by using JSON (raw table) when present.
        delivery_dim = _sales_delivery_dim(delivery_col and f"t.{delivery_col}", order_type_col and f"t.{order_type_col}", raw_json_expr)
        delivery_expr = (
            f"ARRAY(SELECT DISTINCT COALESCE(CAST(x AS STRING), '') FROM (SELECT {delivery_dim} AS x FROM {from_sql}) WHERE COALESCE(CAST(x AS STRING), '') != '' ORDER BY 1 LIMIT 50) AS delivery_partners"
            if (delivery_col or order_type_col or raw_json_expr)
            else "ARRAY<STRING>[] AS delivery_partners"
        )
        payment_expr = (
            f"ARRAY(SELECT DISTINCT COALESCE(CAST({payment_col} AS STRING), '') FROM `{pid}.{ds}.{table}` WHERE COALESCE(CAST({payment_col} AS STRING), '') != '' ORDER BY 1 LIMIT 50) AS payment_modes"
            if payment_col
            else "ARRAY<STRING>[] AS payment_modes"
        )

        q = f"""
        SELECT
          {order_expr},
          {delivery_expr},
          {payment_expr}
        """
        df, _ = query_to_df(client, cfg, q, purpose="api.ops.sales.filters")
        if df.empty:
            return {
                "ok": True,
                "table": table,
                "has_order_type": bool(order_type_col),
                "has_delivery_partner": bool(delivery_col or can_join_raw),
                "has_payment_mode": bool(payment_col),
                "order_types": [],
                "delivery_partners": [],
                "payment_modes": [],
            }

        ot = df.iloc[0].get("order_types")
        dp = df.iloc[0].get("delivery_partners")
        pm = df.iloc[0].get("payment_modes")
        return {
            "ok": True,
            "table": table,
            "has_order_type": bool(order_type_col),
            "has_delivery_partner": bool(delivery_col or can_join_raw),
            "has_payment_mode": bool(payment_col),
            "order_types": list(ot) if ot is not None else [],
            "delivery_partners": list(dp) if dp is not None else [],
            "payment_modes": list(pm) if pm is not None else [],
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/ops/sales/channels")
def ops_sales_channels(
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> Dict[str, Any]:
    cfg = _settings()
    client = _get_bq_client()
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected (missing/invalid service-key.json or dataset)")

    s, e = _date_range(start, end, default_days=30)
    info = _sales_table_info(client, cfg)
    pid, ds, table, cols = info["pid"], info["ds"], info["table"], info["cols"]
    if not pid or not ds:
        raise HTTPException(status_code=400, detail="PROJECT_ID/DATASET_ID not configured")

    order_type_col = "order_type" if "order_type" in cols else None
    delivery_col = "delivery_partner" if "delivery_partner" in cols else None
    order_id_col = "order_id" if "order_id" in cols else None

    raw_info = _sales_raw_info(client, cfg)
    raw_pid, raw_ds, raw_table = raw_info.get("pid"), raw_info.get("ds"), raw_info.get("table")
    raw_json_col = raw_info.get("json_col")
    can_join_raw = bool(raw_info.get("exists") and raw_json_col and order_id_col and ("bill_date" in cols))

    try:
        from utils.bq_guardrails import query_to_df

        raw_json_expr = f"r.{raw_json_col}" if can_join_raw else None
        delivery_dim = _sales_delivery_dim(delivery_col and f"t.{delivery_col}", order_type_col and f"t.{order_type_col}", raw_json_expr)

        def _channel_query(col: Optional[str], alias: str, is_expr: bool = False):
            if not col:
                return []
            oid = f"COUNT(DISTINCT t.{order_id_col})" if order_id_col else "COUNT(1)"
            dim = col if is_expr else f"COALESCE(CAST({col} AS STRING), '')"
            from_sql = f"`{pid}.{ds}.{table}` t"
            if can_join_raw:
                from_sql = (
                    f"`{pid}.{ds}.{table}` t "
                    f"LEFT JOIN `{raw_pid}.{raw_ds}.{raw_table}` r "
                    f"ON CAST(t.{order_id_col} AS STRING) = CAST(r.order_id AS STRING) "
                    f"AND t.bill_date = r.bill_date"
                )
            q = f"""
            SELECT
              {dim} AS channel,
              COALESCE(SUM(total_revenue),0) AS revenue,
              {oid} AS orders,
              COUNT(1) AS line_items
            FROM {from_sql}
            WHERE t.bill_date BETWEEN DATE('{s}') AND DATE('{e}')
            GROUP BY channel
            HAVING channel != ''
            ORDER BY revenue DESC
            LIMIT {int(limit)}
            """
            df, _ = query_to_df(client, cfg, q, purpose=f"api.ops.sales.channels.{alias}")
            return df.to_dict("records") if not df.empty else []

        return {
            "ok": True,
            "table": table,
            "start": str(s),
            "end": str(e),
            "order_types": _channel_query((f"t.{order_type_col}" if order_type_col else None), "order_type"),
            "delivery_partners": _channel_query(delivery_dim if (delivery_col or order_type_col or can_join_raw) else None, "delivery_partner", is_expr=True),
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/ops/sales/top-items")
def ops_sales_top_items(
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    order_type: Optional[str] = Query(default=None),
    delivery_partner: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> Dict[str, Any]:
    cfg = _settings()
    client = _get_bq_client()
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected (missing/invalid service-key.json or dataset)")

    s, e = _date_range(start, end, default_days=30)
    info = _sales_table_info(client, cfg)
    pid, ds, table, cols = info["pid"], info["ds"], info["table"], info["cols"]
    if not pid or not ds:
        raise HTTPException(status_code=400, detail="PROJECT_ID/DATASET_ID not configured")

    where = [f"t.bill_date BETWEEN DATE('{s}') AND DATE('{e}')"]
    if order_type and "order_type" in cols:
        where.append(f"LOWER(COALESCE(CAST(t.order_type AS STRING),'')) = LOWER('{_sql_escape(order_type)}')")
    if delivery_partner:
        delivery_col = "delivery_partner" if "delivery_partner" in cols else None
        order_type_col = "order_type" if "order_type" in cols else None

        raw_info = _sales_raw_info(client, cfg)
        raw_pid, raw_ds, raw_table = raw_info.get("pid"), raw_info.get("ds"), raw_info.get("table")
        raw_json_col = raw_info.get("json_col")
        can_join_raw = bool(raw_info.get("exists") and raw_json_col and ("order_id" in cols) and ("bill_date" in cols))
        raw_json_expr = f"r.{raw_json_col}" if can_join_raw else None

        delivery_dim = _sales_delivery_dim(delivery_col and f"t.{delivery_col}", order_type_col and f"t.{order_type_col}", raw_json_expr)
        where.append(f"LOWER(COALESCE(CAST({delivery_dim} AS STRING),'')) = LOWER('{_sql_escape(delivery_partner)}')")
    where_sql = " AND ".join(where)

    qty_expr = "COALESCE(SUM(quantity),0) AS qty" if "quantity" in cols else "COUNT(1) AS qty"
    try:
        from utils.bq_guardrails import query_to_df

        from_sql = f"`{pid}.{ds}.{table}` t"
        raw_info = _sales_raw_info(client, cfg)
        raw_pid, raw_ds, raw_table = raw_info.get("pid"), raw_info.get("ds"), raw_info.get("table")
        raw_json_col = raw_info.get("json_col")
        if bool(raw_info.get("exists") and raw_json_col and ("order_id" in cols) and ("bill_date" in cols)):
            from_sql = (
                f"`{pid}.{ds}.{table}` t "
                f"LEFT JOIN `{raw_pid}.{raw_ds}.{raw_table}` r "
                f"ON CAST(t.order_id AS STRING) = CAST(r.order_id AS STRING) "
                f"AND t.bill_date = r.bill_date"
            )

        q = f"""
        SELECT
          COALESCE(CAST(item_name AS STRING), '') AS item_name,
          {qty_expr},
          COALESCE(SUM(total_revenue),0) AS revenue
        FROM {from_sql}
        WHERE {where_sql}
        GROUP BY item_name
        HAVING item_name != ''
        ORDER BY revenue DESC
        LIMIT {int(limit)}
        """
        df, _ = query_to_df(client, cfg, q, purpose="api.ops.sales.top_items")
        items = df.to_dict("records") if not df.empty else []
        return {
            "ok": True,
            "table": table,
            "start": str(s),
            "end": str(e),
            "filters": {"order_type": order_type or "", "delivery_partner": delivery_partner or ""},
            "items": items,
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


def _sql_escape(s: str) -> str:
    return str(s).replace("'", "''")


_COL_CACHE: Dict[str, set] = {}
_TABLE_CACHE: Dict[str, bool] = {}


def _get_table_columns(client, pid: str, ds: str, table: str) -> set:
    key = f"{pid}.{ds}.{table}".lower()
    cached = _COL_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        from utils.bq_guardrails import query_to_df

        q_cols = f"""
        SELECT column_name
        FROM `{pid}.{ds}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{_sql_escape(table)}'
        """
        df, _ = query_to_df(client, _settings(), q_cols, purpose=f"api.schema.columns.{table}")
        cols = set(str(x).lower() for x in (df["column_name"].tolist() if not df.empty and "column_name" in df.columns else []))
        _COL_CACHE[key] = cols
        return cols
    except Exception:
        _COL_CACHE[key] = set()
        return set()


def _table_exists(client, pid: str, ds: str, table: str) -> bool:
    key = f"{pid}.{ds}.{table}".lower()
    cached = _TABLE_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        from utils.bq_guardrails import query_to_df

        q = f"""
        SELECT COUNT(1) AS c
        FROM `{pid}.{ds}.INFORMATION_SCHEMA.TABLES`
        WHERE table_name = '{_sql_escape(table)}'
        """
        df, _ = query_to_df(client, _settings(), q, purpose=f"api.schema.table_exists.{table}")
        ok = bool(int(df["c"].iloc[0] or 0)) if not df.empty and "c" in df.columns else False
        _TABLE_CACHE[key] = ok
        return ok
    except Exception:
        _TABLE_CACHE[key] = False
        return False


def _sales_table_info(client, cfg) -> Dict[str, Any]:
    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    # Prefer richer table if present
    if _table_exists(client, pid, ds, "sales_enhanced"):
        table = "sales_enhanced"
    else:
        table = getattr(cfg, "TABLE_SALES_PARSED", "sales_items_parsed")
    cols = _get_table_columns(client, pid, ds, table)
    return {"pid": pid, "ds": ds, "table": table, "cols": cols}


def _sales_raw_info(client, cfg) -> Dict[str, Any]:
    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    table = "sales_raw_layer"
    if not pid or not ds:
        return {"pid": pid, "ds": ds, "table": table, "exists": False, "cols": set(), "json_col": None}
    exists = _table_exists(client, pid, ds, table)
    cols = _get_table_columns(client, pid, ds, table) if exists else set()
    json_col = "full_json" if "full_json" in cols else ("item_details" if "item_details" in cols else None)
    return {"pid": pid, "ds": ds, "table": table, "exists": exists, "cols": cols, "json_col": json_col}


def _sales_delivery_dim(delivery_col: Optional[str], order_type_col: Optional[str], raw_json_expr: Optional[str]) -> str:
    # Try table delivery_partner first; if missing/blank, try JSON; finally infer from order_type.
    # JSON_VALUE paths are defensive: Petpooja keys vary across outlets/accounts.
    json_partner = (
        f"COALESCE(" 
        f"JSON_VALUE({raw_json_expr}, '$.Order.delivery_partner')," 
        f"JSON_VALUE({raw_json_expr}, '$.Order.deliveryPartner')," 
        f"JSON_VALUE({raw_json_expr}, '$.Order.partner')," 
        f"JSON_VALUE({raw_json_expr}, '$.Order.aggregator')," 
        f"JSON_VALUE({raw_json_expr}, '$.Order.order_from')," 
        f"JSON_VALUE({raw_json_expr}, '$.Order.source')," 
        f"JSON_VALUE({raw_json_expr}, '$.Order.channel')," 
        f"JSON_VALUE({raw_json_expr}, '$.Order.platform')" 
        f")"
        if raw_json_expr
        else None
    )

    case = "CASE\n"
    if delivery_col:
        case += f"  WHEN COALESCE(CAST({delivery_col} AS STRING),'') != '' THEN CAST({delivery_col} AS STRING)\n"
    if json_partner:
        case += f"  WHEN COALESCE(CAST({json_partner} AS STRING),'') != '' THEN CAST({json_partner} AS STRING)\n"

    # Normalize common platforms
    def _like(expr: str, pat: str, out: str) -> str:
        return f"  WHEN LOWER(COALESCE(CAST({expr} AS STRING),'')) LIKE '%{pat}%' THEN '{out}'\n"

    if delivery_col:
        case += _like(delivery_col, "zomato", "Zomato")
        case += _like(delivery_col, "swiggy", "Swiggy")
        case += _like(delivery_col, "website", "Website")
        case += _like(delivery_col, "magicpin", "Magicpin")
    if json_partner:
        case += _like(json_partner, "zomato", "Zomato")
        case += _like(json_partner, "swiggy", "Swiggy")
        case += _like(json_partner, "website", "Website")
        case += _like(json_partner, "magicpin", "Magicpin")
    if order_type_col:
        case += _like(order_type_col, "zomato", "Zomato")
        case += _like(order_type_col, "swiggy", "Swiggy")
        case += _like(order_type_col, "website", "Website")
        case += _like(order_type_col, "online", "Online")
        case += _like(order_type_col, "dine", "Dine In")
        case += _like(order_type_col, "pick", "Pick Up")
        case += _like(order_type_col, "delivery", "Direct Delivery")

    case += "  ELSE 'Unknown'\nEND"
    return case


@app.get("/ops/expenses/filters")
def ops_expense_filters() -> Dict[str, Any]:
    cfg = _settings()
    client = _get_bq_client()
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected (missing/invalid service-key.json or dataset)")

    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    if not pid or not ds:
        raise HTTPException(status_code=400, detail="PROJECT_ID/DATASET_ID not configured")

    try:
        from utils.bq_guardrails import query_to_df

        cols = _get_table_columns(client, pid, ds, "expenses_master")
        employee_col = "employee_name" if "employee_name" in cols else ("staff_name" if "staff_name" in cols else None)
        paid_from_col = "paid_from" if "paid_from" in cols else ("payment_mode" if "payment_mode" in cols else None)
        has_employee = employee_col is not None
        has_paid_from = paid_from_col is not None

        employee_expr = (
            f"ARRAY(SELECT DISTINCT COALESCE(CAST({employee_col} AS STRING), '') FROM `{pid}.{ds}.expenses_master` "
            f"WHERE COALESCE(CAST({employee_col} AS STRING), '') != '' ORDER BY 1 LIMIT 200) AS employees"
            if has_employee
            else "ARRAY<STRING>[] AS employees"
        )
        paid_from_expr = (
            f"ARRAY(SELECT DISTINCT COALESCE(CAST({paid_from_col} AS STRING), '') FROM `{pid}.{ds}.expenses_master` "
            f"WHERE COALESCE(CAST({paid_from_col} AS STRING), '') != '' ORDER BY 1 LIMIT 50) AS paid_froms"
            if has_paid_from
            else "ARRAY<STRING>[] AS paid_froms"
        )

        q = f"""
        SELECT
          ARRAY(SELECT DISTINCT COALESCE(CAST(ledger_name AS STRING), CAST(category AS STRING), '') FROM `{pid}.{ds}.expenses_master` WHERE COALESCE(CAST(ledger_name AS STRING), CAST(category AS STRING), '') != '' ORDER BY 1 LIMIT 200) AS ledgers,
          ARRAY(SELECT DISTINCT COALESCE(CAST(main_category AS STRING), '') FROM `{pid}.{ds}.expenses_master` WHERE COALESCE(CAST(main_category AS STRING), '') != '' ORDER BY 1 LIMIT 200) AS main_categories,
          ARRAY(SELECT DISTINCT COALESCE(CAST(category AS STRING), '') FROM `{pid}.{ds}.expenses_master` WHERE COALESCE(CAST(category AS STRING), '') != '' ORDER BY 1 LIMIT 200) AS categories,
          {employee_expr},
          {paid_from_expr}
        """
        df, _ = query_to_df(client, cfg, q, purpose="api.ops.expenses.filters")
        if df.empty:
            return {
                "ok": True,
                "ledgers": [],
                "main_categories": [],
                "categories": [],
                "employees": [],
                "paid_froms": [],
                "has_employee": has_employee,
                "has_paid_from": has_paid_from,
            }
        ledgers_val = df.iloc[0].get("ledgers")
        main_val = df.iloc[0].get("main_categories")
        cats_val = df.iloc[0].get("categories")
        employees_val = df.iloc[0].get("employees")
        paid_froms_val = df.iloc[0].get("paid_froms")
        return {
            "ok": True,
            "ledgers": list(ledgers_val) if ledgers_val is not None else [],
            "main_categories": list(main_val) if main_val is not None else [],
            "categories": list(cats_val) if cats_val is not None else [],
            "employees": list(employees_val) if employees_val is not None else [],
            "paid_froms": list(paid_froms_val) if paid_froms_val is not None else [],
            "has_employee": has_employee,
            "has_paid_from": has_paid_from,
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/ops/expenses")
def ops_expenses(
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    ledger: Optional[str] = Query(default=None),
    main_category: Optional[str] = Query(default=None),
    employee: Optional[str] = Query(default=None),
    paid_from: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    min_amount: Optional[float] = Query(default=None),
    max_amount: Optional[float] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
) -> Dict[str, Any]:
    cfg = _settings()
    client = _get_bq_client()
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected (missing/invalid service-key.json or dataset)")

    s, e = _date_range(start, end, default_days=30)
    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    if not pid or not ds:
        raise HTTPException(status_code=400, detail="PROJECT_ID/DATASET_ID not configured")

    cols = _get_table_columns(client, pid, ds, "expenses_master")
    employee_col = "employee_name" if "employee_name" in cols else ("staff_name" if "staff_name" in cols else None)
    paid_from_col = "paid_from" if "paid_from" in cols else ("payment_mode" if "payment_mode" in cols else None)

    where = [f"expense_date BETWEEN DATE('{s}') AND DATE('{e}')"]

    if ledger:
        esc = _sql_escape(ledger)
        where.append(
            f"LOWER(COALESCE(CAST(ledger_name AS STRING), CAST(category AS STRING), '')) = LOWER('{esc}')"
        )

    if main_category:
        esc = _sql_escape(main_category)
        where.append(f"LOWER(COALESCE(CAST(main_category AS STRING), '')) = LOWER('{esc}')")

    if employee and employee_col:
        esc = _sql_escape(employee)
        where.append(f"LOWER(COALESCE(CAST({employee_col} AS STRING), '')) = LOWER('{esc}')")

    if paid_from and paid_from_col:
        esc = _sql_escape(paid_from)
        where.append(f"LOWER(COALESCE(CAST({paid_from_col} AS STRING), '')) = LOWER('{esc}')")

    if q:
        esc = _sql_escape(q.strip())
        like = f"%{esc.lower()}%"
        parts = [
            f"LOWER(COALESCE(CAST(item_name AS STRING), '')) LIKE '{like}'",
            f"LOWER(COALESCE(CAST(category AS STRING), '')) LIKE '{like}'",
            f"LOWER(COALESCE(CAST(ledger_name AS STRING), '')) LIKE '{like}'",
        ]
        if "description" in cols:
            parts.append(f"LOWER(COALESCE(CAST(description AS STRING), '')) LIKE '{like}'")
        where.append(
            "(" + " OR ".join(parts) + ")"
        )

    if isinstance(min_amount, (int, float)):
        where.append(f"SAFE_CAST(amount AS FLOAT64) >= {float(min_amount)}")
    if isinstance(max_amount, (int, float)):
        where.append(f"SAFE_CAST(amount AS FLOAT64) <= {float(max_amount)}")

    where_sql = " AND ".join(where) if where else "TRUE"

    try:
        from utils.bq_guardrails import query_to_df

        paid_from_expr = (
            f"COALESCE(CAST({paid_from_col} AS STRING), '') AS paid_from" if paid_from_col else "'' AS paid_from"
        )
        employee_expr = (
            f"COALESCE(CAST({employee_col} AS STRING), '') AS employee_name" if employee_col else "'' AS employee_name"
        )
        desc_expr = (
            "COALESCE(CAST(description AS STRING), '') AS description" if "description" in cols else "'' AS description"
        )

        q_data = f"""
        SELECT
          CAST(expense_date AS STRING) AS expense_date,
          COALESCE(CAST(item_name AS STRING), '') AS item_name,
          SAFE_CAST(amount AS FLOAT64) AS amount,
          COALESCE(CAST(category AS STRING), '') AS category,
          COALESCE(CAST(ledger_name AS STRING), '') AS ledger_name,
          COALESCE(CAST(main_category AS STRING), '') AS main_category,
          {desc_expr},
          {paid_from_expr},
          {employee_expr}
        FROM `{pid}.{ds}.expenses_master`
        WHERE {where_sql}
        ORDER BY expense_date DESC
        LIMIT {int(limit)}
        """
        df, _ = query_to_df(client, cfg, q_data, purpose="api.ops.expenses.list")
        items = df.to_dict("records") if not df.empty else []
        for it in items:
            it.setdefault("description", "")
            it.setdefault("paid_from", "")
            it.setdefault("employee_name", "")

        q_sum = f"""
        SELECT
          COALESCE(SUM(SAFE_CAST(amount AS FLOAT64)),0) AS total_amount,
          COUNT(1) AS row_count
        FROM `{pid}.{ds}.expenses_master`
        WHERE {where_sql}
        """
        df2, _ = query_to_df(client, cfg, q_sum, purpose="api.ops.expenses.summary")
        total_amount = float(df2["total_amount"].iloc[0] or 0) if not df2.empty and "total_amount" in df2.columns else 0.0
        row_count = int(df2["row_count"].iloc[0] or 0) if not df2.empty and "row_count" in df2.columns else 0

        return {
            "ok": True,
            "start": str(s),
            "end": str(e),
            "filters": {
                "ledger": ledger or "",
                "main_category": main_category or "",
                "employee": employee or "",
                "paid_from": paid_from or "",
                "q": q or "",
                "min_amount": min_amount,
                "max_amount": max_amount,
            },
            "summary": {"total_amount": total_amount, "row_count": row_count},
            "items": items,
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/metrics/revenue-expenses")
def metrics_revenue_expenses(
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    cfg = _settings()
    client = _get_bq_client()
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected (missing/invalid service-key.json or dataset)")

    s, e = _date_range(start, end, default_days=30)
    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    if not pid or not ds:
        raise HTTPException(status_code=400, detail="PROJECT_ID/DATASET_ID not configured")

    try:
        from utils.bq_guardrails import query_to_df

        if _table_exists(client, pid, ds, "sales_enhanced"):
            # sales_enhanced may be empty for the date range; when that happens, fall back to raw.
            qr = f"""
            WITH
            enhanced_daily AS (
              SELECT dt,
                     COUNT(1) AS orders,
                     COALESCE(SUM(order_total),0) AS revenue
              FROM (
                SELECT SAFE_CAST(bill_date AS DATE) AS dt,
                       CAST(order_id AS STRING) AS order_id,
                       ANY_VALUE(SAFE_CAST(order_total AS FLOAT64)) AS order_total,
                       ANY_VALUE(CAST(order_status AS STRING)) AS order_status
                FROM `{pid}.{ds}.sales_enhanced`
                WHERE SAFE_CAST(bill_date AS DATE) BETWEEN DATE('{s}') AND DATE('{e}')
                GROUP BY SAFE_CAST(bill_date AS DATE), CAST(order_id AS STRING)
              )
              WHERE NOT REGEXP_CONTAINS(LOWER(COALESCE(order_status, '')), r"cancel")
              GROUP BY dt
            ),
            raw_daily AS (
              SELECT dt,
                     COUNT(1) AS orders,
                     COALESCE(SUM(order_total),0) AS revenue
              FROM (
                SELECT bill_date AS dt,
                       CAST(order_id AS STRING) AS order_id,
                       ANY_VALUE(SAFE_CAST(JSON_VALUE(full_json, '$.Order.order_total') AS FLOAT64)) AS order_total,
                       ANY_VALUE(CAST(JSON_VALUE(full_json, '$.Order.status') AS STRING)) AS order_status
                FROM `{pid}.{ds}.sales_raw_layer`
                WHERE bill_date BETWEEN DATE('{s}') AND DATE('{e}')
                GROUP BY bill_date, CAST(order_id AS STRING)
              )
              WHERE NOT REGEXP_CONTAINS(LOWER(COALESCE(order_status, '')), r"cancel")
              GROUP BY dt
            )
            SELECT
              d AS dt,
              IF(COALESCE(e.orders,0) > 0, COALESCE(e.revenue,0), COALESCE(r.revenue,0)) AS revenue
            FROM (
              SELECT dt AS d FROM enhanced_daily
              UNION DISTINCT
              SELECT dt AS d FROM raw_daily
            )
            LEFT JOIN enhanced_daily e ON e.dt = d
            LEFT JOIN raw_daily r ON r.dt = d
            ORDER BY dt
            """
        elif _table_exists(client, pid, ds, "sales_raw_layer"):
            qr = f"""
            SELECT dt, COALESCE(SUM(order_total),0) AS revenue
            FROM (
              SELECT bill_date AS dt,
                     CAST(order_id AS STRING) AS order_id,
                     ANY_VALUE(
                       COALESCE(
                         SAFE_CAST(JSON_VALUE(full_json, '$.Order.order_total') AS FLOAT64),
                         SAFE_CAST(JSON_VALUE(full_json, '$.Order.total') AS FLOAT64),
                         SAFE_CAST(JSON_VALUE(full_json, '$.Order.grand_total') AS FLOAT64),
                         SAFE_CAST(JSON_VALUE(full_json, '$.Order.orderTotal') AS FLOAT64)
                       )
                     ) AS order_total,
                     ANY_VALUE(
                       COALESCE(
                         CAST(JSON_VALUE(full_json, '$.Order.status') AS STRING),
                         CAST(JSON_VALUE(full_json, '$.Order.order_status') AS STRING),
                         CAST(JSON_VALUE(full_json, '$.Order.orderStatus') AS STRING)
                       )
                     ) AS order_status
              FROM `{pid}.{ds}.sales_raw_layer`
              WHERE bill_date BETWEEN DATE('{s}') AND DATE('{e}')
              GROUP BY bill_date, CAST(order_id AS STRING)
            )
            WHERE NOT REGEXP_CONTAINS(LOWER(COALESCE(order_status, '')), r"cancel")
            GROUP BY dt
            """
        else:
            qr = f"""
            SELECT bill_date AS dt, COALESCE(SUM(total_revenue),0) AS revenue
            FROM `{pid}.{ds}.sales_items_parsed`
            WHERE bill_date BETWEEN DATE('{s}') AND DATE('{e}')
            GROUP BY bill_date
            """
        qe = f"""
        SELECT expense_date AS dt, COALESCE(SUM(amount),0) AS expenses
        FROM `{pid}.{ds}.expenses_master`
        WHERE expense_date BETWEEN DATE('{s}') AND DATE('{e}')
        GROUP BY expense_date
        """
        dr, _ = query_to_df(client, cfg, qr, purpose="api.metrics.revenue_by_day")
        de, _ = query_to_df(client, cfg, qe, purpose="api.metrics.expenses_by_day")

        rev_map = {
            str(r["dt"]): float(r.get("revenue") or 0)
            for _, r in dr.iterrows()
        } if not dr.empty and "dt" in dr.columns else {}
        exp_map = {
            str(r["dt"]): float(r.get("expenses") or 0)
            for _, r in de.iterrows()
        } if not de.empty and "dt" in de.columns else {}

        dates: List[str] = []
        revenue: List[float] = []
        expenses: List[float] = []
        d = s
        while d <= e:
            ds_ = str(d)
            dates.append(ds_)
            revenue.append(float(rev_map.get(ds_, 0.0)))
            expenses.append(float(exp_map.get(ds_, 0.0)))
            d = d + timedelta(days=1)

        net = [r - x for r, x in zip(revenue, expenses)]
        return {
            "ok": True,
            "start": str(s),
            "end": str(e),
            "dates": dates,
            "revenue": revenue,
            "expenses": expenses,
            "net": net,
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@app.get("/tasks/pending")
def tasks_pending(
    limit: int = Query(default=20, ge=1, le=200),
) -> Dict[str, Any]:
    cfg = _settings()
    client = _get_bq_client()
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected (missing/invalid service-key.json or dataset)")

    pid, ds = getattr(cfg, "PROJECT_ID", ""), getattr(cfg, "DATASET_ID", "")
    if not pid or not ds:
        raise HTTPException(status_code=400, detail="PROJECT_ID/DATASET_ID not configured")

    try:
        from utils.bq_guardrails import query_to_df

        q = f"""
        SELECT created_at, task_type, item_involved, description, priority, department, status
        FROM `{pid}.{ds}.ai_task_queue`
        WHERE status = 'Pending'
        ORDER BY created_at DESC
        LIMIT {int(limit)}
        """
        df, _ = query_to_df(client, cfg, q, purpose=f"api.tasks.pending_limit_{int(limit)}")
        items = df.to_dict("records") if not df.empty else []
        return {"ok": True, "items": items}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))
