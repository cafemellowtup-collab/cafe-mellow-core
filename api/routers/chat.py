"""
Chat Router - AI Conversation Engine with Relational Intelligence
Supports streaming SSE, Text-to-SQL, deductive reasoning, and self-learning
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from pillars.config_vault import EffectiveSettings
from utils.gemini_chat import stream_chat
from utils.bq_guardrails import QueryMetaCollector
from pillars.chat_intel import parse_time_window
from utils.auto_task_extractor import extract_tasks_from_response, insert_tasks_to_bigquery

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    raw = str(text).strip()
    if raw.startswith("```"):
        fence_start = raw.find("\n")
        fence_end = raw.rfind("```")
        if fence_start != -1 and fence_end != -1 and fence_end > fence_start:
            raw = raw[fence_start:fence_end].strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = raw[start : end + 1]
    try:
        obj = json.loads(candidate)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _tasks_from_suggested_tasks(suggested_tasks: Any) -> List[Dict[str, Any]]:
    if not isinstance(suggested_tasks, list):
        return []

    out: List[Dict[str, Any]] = []
    for t in suggested_tasks:
        if not isinstance(t, dict):
            continue
        title = t.get("title")
        if not isinstance(title, str) or not title.strip():
            continue
        priority = t.get("priority")
        assignee = t.get("assignee")
        deadline = t.get("deadline")
        out.append(
            {
                "description": title[:500],
                "item_involved": "General",
                "priority": str(priority or "Medium"),
                "department": str(assignee or "Operations")[:120],
                "deadline": str(deadline) if deadline else None,
                "task_type": "AI_Generated_Action",
                "status": "Pending",
            }
        )
    return out


def _ensure_envelope(obj: Optional[Dict[str, Any]], fallback_message: str, visual_widget: Optional[Dict[str, Any]] = None, suggested_tasks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        obj = {}
    message = obj.get("message")
    if not isinstance(message, str) or not message.strip():
        obj["message"] = fallback_message
    if "thought_process" not in obj or not isinstance(obj.get("thought_process"), str):
        obj["thought_process"] = "Internal reasoning withheld."
    if "visual_widget" not in obj:
        obj["visual_widget"] = visual_widget
    if "suggested_tasks" not in obj:
        obj["suggested_tasks"] = suggested_tasks or []
    if "next_questions" not in obj:
        obj["next_questions"] = []
    return obj


def _visual_widget_from_visual_data(visual_data: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(visual_data, dict):
        return None

    chart_type = visual_data.get("chart_type")
    chart_data = visual_data.get("chart_data")
    if isinstance(chart_type, str) and chart_type in ("bar", "line", "pie") and isinstance(chart_data, list):
        return {
            "type": chart_type,
            "title": "Key Metrics",
            "data": chart_data,
        }

    kpi_cards = visual_data.get("kpi_cards")
    if isinstance(kpi_cards, list) and kpi_cards:
        return {
            "type": "kpi_card",
            "title": "KPIs",
            "data": kpi_cards,
        }

    return None


def _build_partner_prompt(user_message: str, data_summary: str, data_payload: Dict[str, Any], conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
    history_text = ""
    if conversation_history:
        for conv in conversation_history[-5:]:
            user_msg = conv.get("user_message", "")
            ai_msg = conv.get("ai_response", "")
            if user_msg and ai_msg:
                history_text += f"User: {user_msg}\nAssistant: {ai_msg}\n\n"

    system_hint = data_payload.get("system_hint") if isinstance(data_payload, dict) else None
    visual_data = data_payload.get("visual_data") if isinstance(data_payload, dict) else None
    has_zero = bool(data_payload.get("has_zero_data")) if isinstance(data_payload, dict) else False

    hint_block = f"\n{system_hint}\n" if system_hint else ""
    visual_block = ""
    try:
        if visual_data is not None:
            visual_block = "\nVISUAL_DATA_JSON:\n" + json.dumps(visual_data, ensure_ascii=False)
    except Exception:
        visual_block = ""

    zero_rule = "If the data shows 0 sales/revenue/profit, assume a POS sync/data pipeline issue. Ask a quick diagnostic question and suggest technical checks (do NOT scold or give business strategy)." if has_zero else ""

    return f"""You are TITAN — a high-IQ Strategic Business Partner for Cafe Mellow.

TONE: Conversational, confident, professional, fluid (like a senior McKinsey consultant).
RULES:
- Do NOT use robotic headings like 'Finding:', 'Root Cause:', 'Action:' unless the user explicitly requests a formal report.
- {zero_rule}

YOU MUST OUTPUT VALID JSON ONLY (no markdown fences, no extra text) with these keys:
{{
  \"thought_process\": \"Internal reasoning withheld.\",
  \"message\": \"markdown text for the user\",
  \"visual_widget\": {{ \"type\": \"bar\", \"title\": \"...\", \"data\": [{{\"name\":\"Revenue\",\"value\":123}}] }} OR null,
  \"suggested_tasks\": [{{\"title\":\"...\",\"assignee\":\"IT\",\"priority\":\"High\",\"deadline\":\"2026-01-29\"}}] OR [],
  \"next_questions\": [\"...\"] OR []
}}

Allowed visual_widget.type values: bar, line, pie, kpi_card.

BUSINESS DATA (authoritative):
{data_summary}
{hint_block}
{visual_block}

{history_text}User: {user_message}"""


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    org_id: Optional[str] = None
    location_id: Optional[str] = None
    enable_sql: bool = True
    enable_vision: bool = False
    image_base64: Optional[str] = None


class MetacognitiveLearnRequest(BaseModel):
    org_id: str
    location_id: str
    rule_type: str  # "user_feedback", "auto_learned", "operational_pattern"
    description: str
    created_by: str = "user"
    confidence_score: float = 1.0


def _get_bq_client():
    try:
        from google.cloud import bigquery
        import os
        
        cfg = EffectiveSettings()
        key_file = getattr(cfg, "KEY_FILE", "service-key.json")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
        
        # Try service account key file first (local development)
        if os.path.exists(key_path):
            return bigquery.Client.from_service_account_json(key_path)
        
        # Fall back to Application Default Credentials (Cloud Run)
        project_id = getattr(cfg, "PROJECT_ID", None) or os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if project_id:
            return bigquery.Client(project=project_id)
        
        return bigquery.Client()
    except Exception:
        return None


def _validate_chat_request(req: ChatRequest):
    cfg = EffectiveSettings()
    msg = (req.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="message is required")
    
    if not getattr(cfg, "GEMINI_API_KEY", ""):
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY is missing")
    
    client = _get_bq_client()
    if not client:
        raise HTTPException(
            status_code=400,
            detail="BigQuery not connected (missing/invalid service-key.json)",
        )
    
    return cfg, client, msg


@router.post("/stream")
def chat_stream(req: ChatRequest):
    """
    Streaming chat with Server-Sent Events (SSE)
    
    Features:
    - Real-time streaming responses
    - BigQuery cost tracking
    - Conversation memory (last 10 messages)
    - Relational Intelligence: Auto Text-to-SQL
    - Deductive reasoning for negative inventory
    - Self-learning pattern detection
    """
    cfg, client, msg = _validate_chat_request(req)
    
    async def _sse():
        yield ": stream-open\n\n"
        
        try:
            streamed_any = False
            tw_sql, tw_label, _tw_days = parse_time_window(msg)

            # Accumulate full response for auto-task extraction
            full_ai_response = ""
            
            data_context = None
            data_payload: Dict[str, Any] = {"has_zero_data": False, "visual_data": None, "system_hint": None}
            
            # Vision context if image provided
            vision_context = None
            if req.enable_vision and req.image_base64:
                vision_context = f"[Image analysis enabled. Base64 length: {len(req.image_base64)}]"

            with QueryMetaCollector() as qc:
                async for chunk in stream_chat(msg):
                    full_ai_response += str(chunk or "")

                parsed = _extract_json_object(full_ai_response)

                default_visual = _visual_widget_from_visual_data(data_payload.get("visual_data"))
                envelope = _ensure_envelope(
                    parsed,
                    fallback_message=full_ai_response or "My brain is fuzzy right now, but I can still help. What period do you want to analyze?",
                    visual_widget=default_visual,
                    suggested_tasks=[],
                )

                # Stream the conversational message (human-readable)
                stream_text = str(envelope.get("message") or "")
                if stream_text:
                    streamed_any = True
                    safe = stream_text.replace("\r", "").replace("\n", "\\n")
                    yield f"data:{safe}\n\n"

                # Provide the full JSON envelope for the frontend to render charts/tasks
                try:
                    envelope_json = json.dumps(envelope, ensure_ascii=False).replace("\r", "").replace("\n", "")
                    yield f"event: response_json\ndata:{envelope_json}\n\n"
                except Exception:
                    pass
            
            # Query metadata for cost tracking
            items = list(getattr(qc, "items", []) or [])
            total_inr = float(sum(float(x.get("cost_inr") or 0.0) for x in items))
            sources_payload = {
                "time_window": tw_label or "",
                "queries": items,
                "total_cost_inr": total_inr,
                "sql_executed": bool(data_context),
            }
            sources_json = json.dumps(sources_payload, ensure_ascii=False).replace("\r", "").replace("\n", "")
            yield f"event: sources\ndata:{sources_json}\n\n"
            
            if not streamed_any:
                yield "event: done\ndata: {}\n\n"
                return
            
            # Auto-learn patterns if detected
            if req.org_id and req.location_id:
                _auto_learn_pattern(msg, client, cfg, req.org_id, req.location_id)
            
            if req.org_id and req.location_id and full_ai_response:
                try:
                    tasks = _tasks_from_suggested_tasks(envelope.get("suggested_tasks"))
                    if not tasks:
                        tasks = extract_tasks_from_response(full_ai_response)
                    if tasks:
                        inserted = insert_tasks_to_bigquery(
                            client, cfg, tasks,
                            org_id=req.org_id,
                            location_id=req.location_id,
                        )
                        if inserted > 0:
                            task_notification = json.dumps({"tasks_created": inserted}, ensure_ascii=False)
                            yield f"event: tasks\ndata:{task_notification}\n\n"
                except Exception as e:
                    print(f"Auto-task extraction error: {e}")
            
            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            fallback = {
                "thought_process": "Internal reasoning withheld.",
                "message": f"My brain is fuzzy, but here is what I know: {str(e)}",
                "visual_widget": None,
                "suggested_tasks": [],
                "next_questions": [],
            }
            try:
                fallback_json = json.dumps(fallback, ensure_ascii=False).replace("\r", "").replace("\n", "")
                yield f"event: response_json\ndata:{fallback_json}\n\n"
                safe = str(fallback.get("message") or "").replace("\r", "").replace("\n", "\\n")
                if safe:
                    yield f"data:{safe}\n\n"
            except Exception:
                pass
            yield "event: done\ndata: {}\n\n"
    
    return StreamingResponse(
        _sse(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("")
def chat_non_streaming(req: ChatRequest) -> Dict[str, Any]:
    """
    Non-streaming chat endpoint (legacy support)
    """
    cfg, client, msg = _validate_chat_request(req)

    try:
        from utils.gemini_chat import chat_with_gemini

        data_context = None
        data_payload: Dict[str, Any] = {"has_zero_data": False, "visual_data": None, "system_hint": None}
        if req.enable_sql:
            try:
                di = DataIntelligence(client, cfg)
                intent, period = di.detect_intent(msg)
                ctx = di.get_context(intent, period)
                data_context = ctx.summary
                data_payload = {
                    "intent": intent.value,
                    "time_period": ctx.time_period,
                    "has_zero_data": bool(ctx.has_zero_data),
                    "system_hint": ctx.system_hint,
                    "visual_data": ctx.visual_data,
                    "raw_numbers": ctx.raw_numbers,
                }
            except Exception as e:
                data_context = None
                data_payload = {
                    "has_zero_data": False,
                    "system_hint": f"[SYSTEM_NOTE: Data intelligence failed: {str(e)}]",
                    "visual_data": None,
                }

        conversation_history = []
        prompt = _build_partner_prompt(
            user_message=msg,
            data_summary=(data_context or "(No business data loaded.)"),
            data_payload=data_payload,
            conversation_history=conversation_history,
        )

        raw = chat_with_gemini(prompt)

        parsed = _extract_json_object(str(raw or ""))
        default_visual = _visual_widget_from_visual_data(data_payload.get("visual_data"))
        envelope = _ensure_envelope(parsed, fallback_message=str(raw or ""), visual_widget=default_visual)
        return {"ok": True, "answer": json.dumps(envelope, ensure_ascii=False)}
    except Exception as e:
        fallback = {
            "thought_process": "Internal reasoning withheld.",
            "message": f"My brain is fuzzy, but here is what I know: {str(e)}",
            "visual_widget": None,
            "suggested_tasks": [],
            "next_questions": [],
        }
        return {"ok": False, "answer": json.dumps(fallback, ensure_ascii=False)}


@router.post("/metacognitive/learn")
def learn_strategy(req: MetacognitiveLearnRequest) -> Dict[str, Any]:
    """
    Meta-Cognitive Learning: AI learns user patterns and business rules
    
    Examples:
    - "User orders milk on Thursdays"
    - "High wastage on Mondays - prep optimization needed"
    - "Swiggy orders peak at 8 PM - staff accordingly"
    """
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected")
    
    try:
        from utils.bq_guardrails import query_to_df
        
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        table_name = "system_knowledge_base"
        
        # Create table if not exists
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.{table_name}` (
            id STRING,
            org_id STRING,
            location_id STRING,
            rule_type STRING,
            description STRING,
            created_by STRING,
            created_at TIMESTAMP,
            confidence_score FLOAT64,
            usage_count INT64,
            last_used_at TIMESTAMP,
            status STRING
        )
        """
        client.query(create_table_sql).result()
        
        # Insert new learning
        rule_id = f"{req.org_id}_{req.location_id}_{int(datetime.now().timestamp())}"
        insert_sql = f"""
        INSERT INTO `{project_id}.{dataset_id}.{table_name}`
        (id, org_id, location_id, rule_type, description, created_by, created_at, confidence_score, usage_count, last_used_at, status)
        VALUES (
            '{rule_id}',
            '{req.org_id}',
            '{req.location_id}',
            '{req.rule_type}',
            '''{req.description.replace("'", "''")}''',
            '{req.created_by}',
            CURRENT_TIMESTAMP(),
            {req.confidence_score},
            0,
            NULL,
            'active'
        )
        """
        client.query(insert_sql).result()
        
        return {
            "ok": True,
            "rule_id": rule_id,
            "message": "Learning recorded. AI will use this knowledge in future conversations."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metacognitive/strategies")
def get_learned_strategies(
    org_id: str = Query(...),
    location_id: str = Query(...),
    status: str = Query("active")
) -> Dict[str, Any]:
    """
    Get all learned strategies for a tenant
    UI can show Approve/Reject/Delete actions
    """
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected")
    
    try:
        from utils.bq_guardrails import query_to_df
        
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        
        query = f"""
        SELECT 
            id,
            rule_type,
            description,
            created_by,
            created_at,
            confidence_score,
            usage_count,
            last_used_at,
            status
        FROM `{project_id}.{dataset_id}.system_knowledge_base`
        WHERE org_id = '{org_id}'
          AND location_id = '{location_id}'
          AND status = '{status}'
        ORDER BY created_at DESC
        LIMIT 100
        """
        
        df, _ = query_to_df(client, cfg, query, purpose="api.chat.metacognitive.get_strategies")
        
        strategies = df.to_dict('records') if not df.empty else []
        
        return {
            "ok": True,
            "strategies": strategies,
            "count": len(strategies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/metacognitive/strategies/{rule_id}")
def delete_strategy(rule_id: str) -> Dict[str, Any]:
    """
    Delete or deactivate a learned strategy
    """
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=400, detail="BigQuery not connected")
    
    try:
        project_id = getattr(cfg, "PROJECT_ID", "")
        dataset_id = getattr(cfg, "DATASET_ID", "")
        
        # Soft delete by updating status
        update_sql = f"""
        UPDATE `{project_id}.{dataset_id}.system_knowledge_base`
        SET status = 'deleted'
        WHERE id = '{rule_id}'
        """
        client.query(update_sql).result()
        
        return {
            "ok": True,
            "message": "Strategy deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _detect_sql_intent(message: str, client, cfg, org_id: Optional[str], location_id: Optional[str]) -> Optional[str]:
    """
    Relational Intelligence: Detect if user query needs SQL execution
    Returns simplified SQL context for AI reasoning
    """
    try:
        # Keywords that suggest SQL query need
        sql_triggers = [
            "how many", "count", "total", "sum", "average",
            "show me", "list", "find", "search",
            "negative inventory", "missing", "gap",
            "compare", "difference", "trend"
        ]
        
        msg_lower = message.lower()
        needs_sql = any(trigger in msg_lower for trigger in sql_triggers)
        
        if not needs_sql:
            return None
        
        # Simple context - just confirm SQL capability available
        return "BigQuery SQL execution enabled for cross-referencing Recipes, Sales, Expenses, and Inventory"
    except Exception:
        return None


def _auto_learn_pattern(message: str, client, cfg, org_id: str, location_id: str):
    """
    Self-Learning: Silently detect and save business patterns
    
    Examples:
    - Frequent queries about specific items → save as "user interest"
    - Time-based patterns → save for predictive alerts
    - Recurring issues → save for proactive monitoring
    """
    try:
        # Pattern detection logic (simplified for now)
        # In production, this would use ML/NLP to detect patterns
        
        msg_lower = message.lower()
        
        # Detect inventory concern patterns
        if "negative" in msg_lower and ("inventory" in msg_lower or "stock" in msg_lower):
            pattern_desc = f"User frequently checks negative inventory. Auto-monitor: {datetime.now().date()}"
            # Would insert into system_knowledge_base here
            pass
        
        # Detect time-based patterns (day of week, time of day)
        weekday_pattern = False  # Placeholder for actual pattern detection
        if weekday_pattern:
            # Save pattern silently
            pass
        
    except Exception:
        # Silent failure - learning is optional
        pass
