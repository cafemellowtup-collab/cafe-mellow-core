"""
Gemini Chat Integration with BigQuery Memory
"""
import sys
import os
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import requests
import json
import settings
from datetime import datetime
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from utils.bq_guardrails import query_to_df

def get_bigquery_context(client, settings, limit=10):
    """Get recent context from BigQuery for chat memory"""
    context_parts = []
    
    try:
        # Get recent sales data - use enhanced table if available
        try:
            # Try enhanced table first (has all fields)
            q_sales = f"""
                SELECT 
                    bill_date, 
                    customer_name,
                    table_number,
                    order_type,
                    delivery_partner,
                    item_name, 
                    quantity, 
                    total_revenue,
                    payment_mode,
                    coupon_codes,
                    advance_order
                FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_enhanced`
                ORDER BY bill_date DESC
                LIMIT {limit}
            """
            sales_df, _ = query_to_df(client, settings, q_sales, purpose=f"chat.context.sales_enhanced_limit_{int(limit)}")
            if not sales_df.empty:
                # Format for AI context
                sales_summary = f"Recent Sales Data ({len(sales_df)} orders):\n"
                sales_summary += sales_df[['bill_date', 'customer_name', 'order_type', 'item_name', 'total_revenue', 'payment_mode']].to_string(index=False)
                context_parts.append(sales_summary)
        except:
            # Fallback to basic parsed table
            try:
                q_sales = f"""
                    SELECT bill_date, item_name, quantity, total_revenue 
                    FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_items_parsed`
                    ORDER BY bill_date DESC
                    LIMIT {limit}
                """
                sales_df, _ = query_to_df(client, settings, q_sales, purpose=f"chat.context.sales_items_parsed_limit_{int(limit)}")
                if not sales_df.empty:
                    context_parts.append("Recent Sales Data:\n" + sales_df.to_string(index=False))
            except:
                pass
        
        # Get recent tasks
        try:
            q_tasks = f"""
                SELECT task_type, item_involved, description, priority
                FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.ai_task_queue`
                WHERE status = 'Pending'
                ORDER BY created_at DESC
                LIMIT 5
            """
            tasks_df, _ = query_to_df(client, settings, q_tasks, purpose="chat.context.pending_alerts_limit_5")
            if not tasks_df.empty:
                context_parts.append("Recent Alerts:\n" + tasks_df.to_string(index=False))
        except:
            pass
        
        # Get financial summary
        try:
            q_finance = f"""
                SELECT 
                    (SELECT SUM(total_revenue) FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_items_parsed` WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as week_revenue,
                    (SELECT SUM(amount) FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.expenses_master` WHERE expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as week_expenses,
                    (SELECT SUM(total_revenue) FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_items_parsed` WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY) AND bill_date < DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as prev_week_revenue,
                    (SELECT SUM(amount) FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.expenses_master` WHERE expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY) AND expense_date < DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as prev_week_expenses
            """
            fin_df, _ = query_to_df(client, settings, q_finance, purpose="chat.context.financial_summary_7d")
            if not fin_df.empty and fin_df.iloc[0]['week_revenue']:
                rev = fin_df.iloc[0]['week_revenue'] or 0
                exp = fin_df.iloc[0]['week_expenses'] or 0
                prev_rev = fin_df.iloc[0].get('prev_week_revenue') or 0
                prev_exp = fin_df.iloc[0].get('prev_week_expenses') or 0
                delta_rev = float(rev or 0) - float(prev_rev or 0)
                delta_exp = float(exp or 0) - float(prev_exp or 0)
                pct_rev = (delta_rev / float(prev_rev)) * 100.0 if float(prev_rev or 0) else None
                pct_exp = (delta_exp / float(prev_exp)) * 100.0 if float(prev_exp or 0) else None

                line = f"Financial Summary (Last 7 days): Revenue: ₹{rev:,.2f}, Expenses: ₹{exp:,.2f}, Net: ₹{rev-exp:,.2f}"
                line += f"\nPrevious 7 days: Revenue: ₹{prev_rev:,.2f}, Expenses: ₹{prev_exp:,.2f}, Net: ₹{float(prev_rev or 0)-float(prev_exp or 0):,.2f}"
                if pct_rev is not None:
                    line += f"\nΔ Revenue: ₹{delta_rev:,.2f} ({pct_rev:+.1f}%)"
                else:
                    line += f"\nΔ Revenue: ₹{delta_rev:,.2f}"
                if pct_exp is not None:
                    line += f"\nΔ Expenses: ₹{delta_exp:,.2f} ({pct_exp:+.1f}%)"
                else:
                    line += f"\nΔ Expenses: ₹{delta_exp:,.2f}"
                context_parts.append(line)
        except:
            pass
            
    except Exception as e:
        print(f"Error getting context: {e}")
    
    return "\n\n".join(context_parts)

def save_conversation(client, settings, user_message, ai_response):
    """Save conversation to BigQuery for memory"""
    try:
        import sys
        if sys.platform == 'win32':
            # Fix encoding for Windows
            try:
                user_message = user_message.encode('utf-8', errors='replace').decode('utf-8')
                ai_response = ai_response.encode('utf-8', errors='replace').decode('utf-8')
            except:
                pass
        
        conversation_data = {
            'timestamp': datetime.now().isoformat(),  # Convert to ISO string
            'user_message': user_message[:5000] if len(user_message) > 5000 else user_message,  # Limit length
            'ai_response': ai_response[:10000] if len(ai_response) > 10000 else ai_response  # Limit length
        }
        
        # Check if table exists, create if not
        table_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}.chat_memory"
        
        try:
            client.get_table(table_id)
        except NotFound:
            # Create table schema
            schema = [
                bigquery.SchemaField("timestamp", "TIMESTAMP"),
                bigquery.SchemaField("user_message", "STRING"),
                bigquery.SchemaField("ai_response", "STRING")
            ]
            table = bigquery.Table(table_id, schema=schema)
            client.create_table(table)
        
        # Insert conversation - use DataFrame instead of JSON to handle datetime properly
        import pandas as pd
        df = pd.DataFrame([conversation_data])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
            source_format=bigquery.SourceFormat.PARQUET
        )
        
        try:
            job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Wait for job to complete
        except Exception as insert_error:
            # Fallback: try JSON with string timestamp
            conversation_data['timestamp'] = conversation_data['timestamp']
            rows_to_insert = [{
                'timestamp': conversation_data['timestamp'],
                'user_message': conversation_data['user_message'],
                'ai_response': conversation_data['ai_response']
            }]
            errors = client.insert_rows_json(table_id, rows_to_insert)
            if errors:
                print(f"Error saving conversation: {errors}")
    except Exception as e:
        # Don't fail chat if save fails
        import traceback
        print(f"Error in save_conversation: {e}")
        traceback.print_exc()

def get_conversation_history(client, settings, limit=10):
    """Get recent conversation history"""
    try:
        table_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}.chat_memory"
        q = f"""
            SELECT user_message, ai_response, timestamp
            FROM `{table_id}`
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        df = client.query(q).to_dataframe()
        return df.to_dict('records') if not df.empty else []
    except:
        return []

def chat_with_gemini(client, settings, user_message, conversation_history=None, use_enhanced_prompt=False, original_user_prompt=None):
    """Chat with Gemini API. If use_enhanced_prompt=True, user_message is the full instruction+data; no extra system wrap. original_user_prompt used for saving when use_enhanced_prompt."""
    
    _save_user = (original_user_prompt or user_message) if use_enhanced_prompt else user_message
    
    try:
        if use_enhanced_prompt:
            full_prompt = user_message + "\n\nAssistant:"
        else:
            # Get BigQuery context
            context = get_bigquery_context(client, settings)
            
            # TITAN CFO: Ruthless Financial Intelligence Engine
            system_prompt = f"""You are TITAN CFO. You are NOT a consultant. You are the ruthless Chief Financial Officer for this restaurant.

**RULE 1: NO POLITE FILLER**
BANNED PHRASES: "Let's work together", "I'd suggest", "You might consider", "Great question", "I'm happy to help", "Let me explain".
START every response with THE NUMBER. No preamble.

**RULE 2: EVERY ISSUE = [TASK:]**
When you identify ANY problem, gap, anomaly, or opportunity, you MUST output an action item in this EXACT format:
[TASK:] <action> by <deadline> | Owner: <who>

Example: [TASK:] Retrain prep staff on dough yield by tomorrow 10 AM | Owner: Kitchen Manager

**YOUR PERSONA:**
- Speak in SHORT, DIRECTIVE sentences.
- Every answer structure: (1) THE NUMBER (2) ROOT CAUSE (3) [TASK:] ACTION
- Quantify EVERYTHING. "High" = ₹X. "Low" = Y%.
- Root causes MUST be data-backed, not guesses.
- Deadlines are non-negotiable. Use: "by EOD", "by tomorrow 10 AM", "within 2 hours".

**AVAILABLE DATA:**
{context}

**LOCATION:** Tiruppur, Tamil Nadu, India

**RESPONSE FORMAT:**
BAD: "Your expenses seem high. You might want to look into reducing costs."
GOOD: "Weekly expense: ₹48,200 (+18% vs last week). Root cause: Unplanned repair ₹8,000 on Day 3. [TASK:] Get 3 vendor quotes for equipment maintenance contract by Friday 5 PM | Owner: Admin Manager"

**MULTI-ISSUE FORMAT:**
• **Item 1:** ₹X impact. Root cause: Y. [TASK:] Action by deadline | Owner: Z
• **Item 2:** ₹X impact. Root cause: Y. [TASK:] Action by deadline | Owner: Z

You are a CFO. Numbers. Root causes. Tasks. No fluff. Execute."""

            # Build conversation history
            history_text = ""
            if conversation_history:
                for conv in conversation_history[-5:]:  # Last 5 conversations
                    user_msg = conv.get('user_message', '')
                    ai_msg = conv.get('ai_response', '')
                    if user_msg and ai_msg:
                        history_text += f"User: {user_msg}\n"
                        history_text += f"Assistant: {ai_msg}\n\n"
            
            # Build full prompt
            full_prompt = f"{system_prompt}\n\n{history_text}User: {user_message}\nAssistant:"
        
        # Call Gemini API with proper error handling
        url = f"{settings.GEMINI_URL}?key={settings.GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": full_prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.9,  # Higher for more natural responses
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,  # Increased for detailed responses
                "candidateCount": 1
            }
        }
        
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle different response structures
            if 'candidates' in data and len(data['candidates']) > 0:
                candidate = data['candidates'][0]
                
                # Check for content block
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if parts and len(parts) > 0 and 'text' in parts[0]:
                        ai_response = parts[0]['text']
                        
                        # Save conversation only if successful
                        try:
                            save_conversation(client, settings, _save_user, ai_response)
                        except:
                            pass  # Don't fail if save fails
                        
                        return ai_response
                
                # Fallback: try to extract text directly
                if 'text' in candidate:
                    ai_response = candidate['text']
                    try:
                        save_conversation(client, settings, _save_user, ai_response)
                    except:
                        pass
                    return ai_response
            
            # Check for error in response
            if 'error' in data:
                error_msg = data['error'].get('message', 'Unknown error')
                return f"I encountered an issue: {error_msg}. Please try rephrasing your question."
            
            return "I apologize, but I couldn't generate a proper response. The API response format was unexpected. Please try again."
            
        elif response.status_code == 400:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Invalid request')
                return f"Request error: {error_msg}. Please check your question format."
            except:
                return "Invalid request. Please try rephrasing your question."
        elif response.status_code == 401:
            return "Authentication error. Please check your Gemini API key in settings.py"
        elif response.status_code == 429:
            return "Rate limit exceeded. Please wait a moment and try again."
        else:
            return f"API error (Status {response.status_code}): {response.text[:200]}"
            
    except requests.exceptions.Timeout:
        return "The request took too long. This might be due to a large query. Please try a simpler question or try again."
    except requests.exceptions.ConnectionError:
        return "Connection error. Please check your internet connection and try again."
    except json.JSONDecodeError as e:
        return f"Error parsing API response. Please try again."
    except Exception as e:
        error_detail = str(e)
        return f"Unexpected error: {error_detail}. Please check the logs for details."


def chat_with_gemini_stream(client, settings, user_message, conversation_history=None, use_enhanced_prompt=False, original_user_prompt=None):
    """Stream Gemini response chunks.

    Yields incremental text segments as they arrive from Gemini.
    Also saves the full conversation to BigQuery at the end (best-effort).
    """

    _save_user = (original_user_prompt or user_message) if use_enhanced_prompt else user_message

    if use_enhanced_prompt:
        full_prompt = user_message + "\n\nAssistant:"
    else:
        msg_trim = (user_message or "").strip().lower()
        # Fast path: for tiny greetings, don't run multiple BigQuery queries.
        if msg_trim in ("hi", "hello", "hey", "hai", "namaste") or len(msg_trim) <= 4:
            context = "(No BigQuery context loaded for this short greeting.)"
        else:
            context = get_bigquery_context(client, settings)

        system_prompt = f"""You are TITAN CFO. You are NOT a consultant. You are the ruthless Chief Financial Officer for this restaurant.

**RULE 1: NO POLITE FILLER**
BANNED PHRASES: "Let's work together", "I'd suggest", "You might consider", "Great question", "I'm happy to help".
START every response with THE NUMBER. No preamble.

**RULE 2: EVERY ISSUE = [TASK:]**
When you identify ANY problem, gap, anomaly, or opportunity, output an action item in this EXACT format:
[TASK:] <action> by <deadline> | Owner: <who>

**YOUR PERSONA:**
- SHORT, DIRECTIVE sentences.
- Structure: (1) THE NUMBER (2) ROOT CAUSE (3) [TASK:] ACTION
- Quantify EVERYTHING. "High" = ₹X. "Low" = Y%.
- Root causes MUST be data-backed.
- Deadlines: "by EOD", "by tomorrow 10 AM", "within 2 hours".

**AVAILABLE DATA:**
{context}

**LOCATION:** Tiruppur, Tamil Nadu, India

**FORMAT:**
• **Issue:** ₹X impact. Root cause: Y. [TASK:] Action by deadline | Owner: Z

You are a CFO. Numbers. Root causes. Tasks. No fluff. Execute."""

        history_text = ""
        if conversation_history:
            for conv in conversation_history[-5:]:
                user_msg = conv.get("user_message", "")
                ai_msg = conv.get("ai_response", "")
                if user_msg and ai_msg:
                    history_text += f"User: {user_msg}\n"
                    history_text += f"Assistant: {ai_msg}\n\n"

        full_prompt = f"{system_prompt}\n\n{history_text}User: {user_message}\nAssistant:"

    base_url = getattr(settings, "GEMINI_URL", "")
    if not base_url:
        raise RuntimeError("GEMINI_URL is missing")

    # Convert :generateContent to :streamGenerateContent if needed.
    stream_base = base_url.replace(":generateContent", ":streamGenerateContent")
    # Request SSE explicitly so tokens arrive incrementally.
    url = f"{stream_base}?key={settings.GEMINI_API_KEY}&alt=sse"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": full_prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.9,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 2048,
            "candidateCount": 1,
        },
    }

    full_text = ""
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=(10, 120),
            stream=True,
            headers={"Accept": "text/event-stream"},
        )
        response.raise_for_status()

        for raw in response.iter_lines(decode_unicode=True):
            if not raw:
                continue

            line = raw.strip()
            if line.startswith("data:"):
                line = line[5:].lstrip()

            # Some implementations may send a terminal marker.
            if line in ("[DONE]", "DONE"):
                break

            try:
                data = json.loads(line)
            except Exception:
                continue

            candidates = data.get("candidates") or []
            if not candidates:
                continue

            content = candidates[0].get("content") or {}
            parts = content.get("parts") or []
            if not parts:
                continue

            text = parts[0].get("text")
            if not text:
                continue

            full_text += text
            yield text

    finally:
        if full_text:
            try:
                save_conversation(client, settings, _save_user, full_text)
            except:
                pass
